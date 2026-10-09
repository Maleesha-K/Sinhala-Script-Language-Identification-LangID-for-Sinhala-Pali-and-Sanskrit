"""Build the leakage-free target-language release (Sinhala / Pali / Sanskrit in
Sinhala script) from the pooled corpus. Run once by a maintainer; researchers
download the published release in stage 01.

    uv run python scripts/maintainer/resplit_target.py --input-dir source_data/target

Method (parameters in config/pipeline.yaml `target_split`):
 1. Pool train/val/test, NFC-normalise, keep Sinhala-script text only.
 2. Recover documents. Non-parallel sources carry document ids (`group_id`).
    The parallel corpus is sinhala-nlp/pali-sinhala, row-aligned: Pali pair k
    has id k and its Sinhala translation id k + PARALLEL_PAIRS. Its rows are in
    canonical order, so a document (sutta) starts at each Pali incipit
    "evam me sutam"; both sides of a translation pair share the document.
 3. Split unit: contiguous block of <= block_size rows within a document.
 4. Sentence-level instances: paragraphs are split at sentence terminators and
    packed to <= max_chars; units inherit their block.
 5. Exact duplicates: same text and label keeps the first; the same text under
    two labels is dropped entirely.
 6. Near duplicates (MinHash LSH, char 5-grams, Jaccard >= threshold): one
    representative per same-label cluster; mixed-label clusters are dropped.
 7. Group-stratified split. Strata: the parallel corpus (blocks hold both
    languages), and (source, label) for every other source. Within a stratum,
    blocks are shuffled (seeded) and each goes to the split furthest below its
    target share of units.
 8. Verification: zero exact and zero near-duplicate pairs across splits.
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from lidpipe import config, paths
from lidpipe.dedup import clusters, near_duplicate_pairs
from lidpipe.manifest import prepare_output, reset_dir, sha256_file, write_manifest
from lidpipe.text import letter_count, normalise, script_of, segment, text_sha256

PARALLEL_SOURCE = 'pali-sinhala-parallel'
PARALLEL_PAIRS = 28395           # rows in sinhala-nlp/pali-sinhala output.tsv
PALI_INCIPIT = normalise('එවං මෙ සුතං')
LABELS = {'sinhala': 'sin_Sinh', 'pali': 'pli_Sinh', 'sanskrit': 'san_Sinh'}
SPLITS = ('train', 'validation', 'test')


def load(input_dir):
    csv.field_size_limit(sys.maxsize)
    rows, inputs = [], {}
    for name in ('train', 'val', 'test'):
        path = Path(input_dir) / f'{name}.csv'
        inputs[path.name] = sha256_file(path)
        with open(path, encoding='utf-8-sig', newline='') as f:
            rows += list(csv.DictReader(f))
    return rows, inputs


def verify_parallel_provenance(rows):
    """Check every parallel row against the pinned public corpus
    (sinhala-nlp/pali-sinhala): Pali id k must be row k's Pali side and Sinhala
    id k + PARALLEL_PAIRS row k's Sinhala side. Document recovery relies on
    this alignment, so any mismatch aborts."""
    import os
    import re
    from huggingface_hub import hf_hub_download
    from lidpipe.env import load_env
    load_env()
    lock = config.locks()['pali_sinhala_parallel']
    tsv = hf_hub_download(lock['repo_id'], 'output.tsv', repo_type='dataset', revision=lock['revision'],
                          token=os.environ.get('HF_TOKEN'))
    csv.field_size_limit(sys.maxsize)
    with open(tsv, encoding='utf-8', newline='') as f:
        public = list(csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    if len(public) != lock['rows'] or len(public) != PARALLEL_PAIRS:
        raise SystemExit(f'{lock["repo_id"]} has {len(public)} rows, expected {PARALLEL_PAIRS}')

    def key(text):  # Sinhala letters only: robust to punctuation/whitespace cleanup
        return re.sub(r'[^඀-෿]', '', normalise(text))[:80]

    checked = mismatched = 0
    for r in rows:
        if r['source'] != PARALLEL_SOURCE:
            continue
        n = int(r['group_id'].split('_')[1])
        pali = r['label'] == 'pali'
        k = n if pali else n - PARALLEL_PAIRS
        ref = public[k]['pali_text' if pali else 'sinhala_text'] if 0 <= k < PARALLEL_PAIRS else ''
        checked += 1
        mismatched += key(ref) != key(r['text'])
    result = {'public_corpus': f'{lock["repo_id"]}@{lock["revision"]}', 'rows_checked': checked,
              'rows_matching_public_alignment': checked - mismatched}
    print(f'[{"PASS" if not mismatched else "FAIL"}] parallel provenance: {checked - mismatched}/{checked} '
          f'rows match {lock["repo_id"]} row alignment')
    if mismatched:
        raise SystemExit('parallel rows do not follow the public corpus alignment; document recovery would be wrong')
    return result


def assign_documents(rows, block_size):
    """Attach `doc` and `block` to every row (see module docstring, steps 2-3)."""
    par = [r for r in rows if r['source'] == PARALLEL_SOURCE]
    for r in par:
        n = int(r['group_id'].split('_')[1])
        r['pair'] = n if r['label'] == 'pali' else n - PARALLEL_PAIRS
        if not 0 <= r['pair'] < PARALLEL_PAIRS or (r['label'] == 'pali') != (n < PARALLEL_PAIRS):
            raise SystemExit(f'parallel id {n} ({r["label"]}) does not fit the {PARALLEL_PAIRS}-pair layout')
    starts = sorted(r['pair'] for r in par if r['label'] == 'pali' and
                    normalise(r['text']).lstrip('‘’\'" ').startswith(PALI_INCIPIT))
    starts = np.array([0] + [s for s in starts if s > 0])
    for r in par:
        d = int(np.searchsorted(starts, r['pair'], side='right') - 1)
        r['doc'] = f'{PARALLEL_SOURCE}:sutta{d}'
        r['block'] = f'{r["doc"]}:b{(r["pair"] - starts[d]) // block_size}'
    by_doc = defaultdict(list)
    for r in rows:
        if r['source'] != PARALLEL_SOURCE:
            by_doc[r['group_id']].append(r)
    for doc, members in by_doc.items():
        members.sort(key=lambda r: int(r['id']))
        for pos, r in enumerate(members):
            r['doc'] = f'{r["source"]}:{doc}'
            r['block'] = f'{r["doc"]}:b{pos // block_size}'
    return len(starts)


def build_units(rows, cfg, stats):
    units = []
    for r in sorted(rows, key=lambda r: (r['source'], int(r['id']))):
        label = LABELS[r['label']]
        text = normalise(r['text'])
        if script_of(text) != 'Sinh':
            stats['rows_not_sinhala_script'] += 1
            continue
        for i, unit in enumerate(segment(text, cfg['max_chars'])):
            if letter_count(unit) < cfg['min_letters'] or script_of(unit) != 'Sinh':
                stats['units_too_short_or_wrong_script'] += 1
                continue
            units.append({'sample_id': f'target:{r["source"]}:{r["id"]}:{i}', 'text': unit, 'label': label,
                          'source': r['source'], 'subcorpus': r.get('subcorpus', ''), 'doc_id': r['doc'],
                          'block_id': r['block'], 'text_sha256': text_sha256(unit)})
    return units


def deduplicate(units, nd, stats):
    labels_of = defaultdict(set)
    for u in units:
        labels_of[u['text_sha256']].add(u['label'])
    seen, kept = set(), []
    for u in units:
        if len(labels_of[u['text_sha256']]) > 1:
            stats['exact_conflicting_label_removed'] += 1
        elif u['text_sha256'] in seen:
            stats['exact_duplicate_removed'] += 1
        else:
            seen.add(u['text_sha256'])
            kept.append(u)
    pairs = near_duplicate_pairs([u['text'] for u in kept], nd['shingle'], nd['num_perm'], nd['threshold'])
    rep = clusters(len(kept), pairs)
    members = defaultdict(list)
    for i, root in enumerate(rep):
        members[root].append(i)
    out = []
    for root, idx in members.items():
        if len({kept[i]['label'] for i in idx}) > 1:
            stats['near_duplicate_mixed_label_removed'] += len(idx)
            continue
        stats['near_duplicate_removed'] += len(idx) - 1
        out.append(kept[root])
    stats['near_duplicate_pairs'] = len(pairs)
    return sorted(out, key=lambda u: u['sample_id'])


def split(units, fractions, seed):
    rng = np.random.default_rng(seed)
    strata = defaultdict(lambda: defaultdict(list))
    for u in units:
        key = u['source'] if u['source'] == PARALLEL_SOURCE else f'{u["source"]}|{u["label"]}'
        strata[key][u['block_id']].append(u)
    for key in sorted(strata):
        blocks = strata[key]
        names = sorted(blocks)
        rng.shuffle(names)
        total = sum(len(b) for b in blocks.values())
        have = dict.fromkeys(SPLITS, 0)
        for name in names:
            # the split furthest below its target share takes the next block
            target = min(SPLITS, key=lambda s: have[s] - fractions[s] * total)
            for u in blocks[name]:
                u['split'] = target
            have[target] += len(blocks[name])


def verify(units, nd):
    """Cross-split leakage counts at the dedup threshold (must be 0) and at a
    looser Jaccard 0.5 (informational)."""
    texts = [u['text'] for u in units]
    report = {}
    exact = defaultdict(set)
    for u in units:
        exact[u['text_sha256']].add(u['split'])
    report['exact_cross_split'] = sum(1 for s in exact.values() if len(s) > 1)
    for thr in (nd['threshold'], 0.5):
        pairs = near_duplicate_pairs(texts, nd['shingle'], nd['num_perm'], thr)
        report[f'near_dup_cross_split_j{thr}'] = sum(1 for i, j in pairs if units[i]['split'] != units[j]['split'])
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--input-dir', default=str(paths.ROOT / 'source_data' / 'target'))
    ap.add_argument('--out-dir', default=str(paths.DATASETS / 'target_release'))
    ap.add_argument('--update-lock', action='store_true',
                    help='pin the new files in config/locks.json (only when the release is meant to change)')
    args = ap.parse_args()
    cfg = config.pipeline()['target_split']
    stats = Counter()

    rows, inputs = load(args.input_dir)
    stats['input_rows'] = len(rows)
    provenance = verify_parallel_provenance(rows)
    n_suttas = assign_documents(rows, cfg['block_size'])
    units = build_units(rows, cfg, stats)
    stats['units_after_segmentation'] = len(units) + stats['units_too_short_or_wrong_script']
    units = deduplicate(units, cfg['near_dup'], stats)
    split(units, cfg['fractions'], cfg['seed'])
    leakage = verify(units, cfg['near_dup'])
    strict = f'near_dup_cross_split_j{cfg["near_dup"]["threshold"]}'
    for name in ('exact_cross_split', strict):
        print(f'[{"PASS" if not leakage[name] else "FAIL"}] leakage {name}: {leakage[name]} pairs across splits')
    print(f'[INFO] near_dup_cross_split_j0.5: {leakage["near_dup_cross_split_j0.5"]} pairs '
          f'(looser threshold, reported only: formulaic canon text)')
    if leakage['exact_cross_split'] or leakage[strict]:
        raise SystemExit(f'leakage check failed: {leakage}')

    out = reset_dir(args.out_dir)
    files = []
    for s in SPLITS:
        path = prepare_output(out / f'{s}.jsonl')
        with open(path, 'w', encoding='utf-8') as f:
            for u in units:
                if u['split'] == s:
                    f.write(json.dumps({k: v for k, v in u.items() if k != 'split'}, ensure_ascii=False) + '\n')
        files.append(path)

    table = defaultdict(lambda: defaultdict(Counter))
    lengths = defaultdict(list)
    for u in units:
        table[u['split']][u['label']][u['source']] += 1
        lengths[u['label']].append(len(u['text']))
    report = {
        'inputs_sha256': inputs, 'config': cfg, 'stats': dict(stats), 'provenance': provenance,
        'parallel_documents': n_suttas,
        'splits': {s: {l: dict(c) for l, c in table[s].items()} for s in SPLITS},
        'split_totals': {s: sum(sum(c.values()) for c in table[s].values()) for s in SPLITS},
        'blocks_per_split': {s: len({u['block_id'] for u in units if u['split'] == s}) for s in SPLITS},
        'length_chars': {l: {'p50': float(np.median(v)), 'p90': float(np.percentile(v, 90)), 'max': max(v)}
                         for l, v in sorted(lengths.items())},
        'leakage': leakage,
    }
    rpath = prepare_output(out / 'split_report.json')
    rpath.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    files.append(rpath)
    write_manifest(out, 'maintainer.resplit_target', files)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Reproducibility: does this run reproduce the release pinned in locks.json?
    locks = json.loads(paths.LOCKS.read_text(encoding='utf-8'))
    pinned = locks['target_dataset']['files_sha256']
    built = {f.name: sha256_file(f) for f in files}
    same = built == pinned
    print(f'[{"PASS" if same else "INFO"}] reproduces the pinned release in config/locks.json: {same}')
    if args.update_lock and not same:
        locks['target_dataset'].update(kind='local_release', path=str(Path(args.out_dir).relative_to(paths.ROOT)),
                                       files_sha256=built)
        for k in ('repo_id', 'revision', 'published_repo', 'probe_file'):
            locks['target_dataset'].pop(k, None)
        paths.LOCKS.write_text(json.dumps(locks, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('updated config/locks.json target_dataset -> local_release (publish it next)')


if __name__ == '__main__':
    main()
