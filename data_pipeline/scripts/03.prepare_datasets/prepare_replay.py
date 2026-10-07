"""Rehearsal data and the mixed (target + replay) training/validation sets.

For each of the 8 replay labels, from OpenLID-v2 (pinned):
 1. draw `candidates_per_language` random rows (seeded), streaming the parquet,
    skipping OpenLID sub-sources listed in `exclude_sources` (benchmark origins);
 2. apply the same normalisation, sentence segmentation, length and script
    filters as the target data (config `target_split`);
 3. drop exact duplicates, then keep one unit per MinHash near-duplicate cluster;
 4. decontaminate: drop units that appear in any benchmark eval set (exact
    match or MinHash near duplicate of a same-label row) or in the target
    data (exact match);
 5. shuffle (seeded) and take `per_language.validation` then `per_language.train`.
Outputs, in datasets/hybrid_finetune/replay_mixed/:
  replay_{train,validation}.jsonl   8 replay labels, balanced
  mixed_{train,validation}.jsonl    target split + replay split
"""
import json
from collections import Counter

import numpy as np
import pyarrow.parquet as pq

from lidpipe import config, paths
from lidpipe.dedup import clusters, near_duplicate_pairs, near_matches
from lidpipe.labels import REPLAY
from lidpipe.manifest import prepare_output, write_manifest
from lidpipe.text import letter_count, normalise, script_of, segment, text_sha256

cfg = config.pipeline()['replay']
unit_cfg = config.pipeline()['target_split']
nd = unit_cfg['near_dup']
raw_dir = paths.FINETUNE / 'openlid_v2' / 'raw' / 'data'
out_dir = paths.FINETUNE / 'replay_mixed'


def read_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def sample_rows(path, n, rng):
    pf = pq.ParquetFile(path)
    total = pf.metadata.num_rows
    wanted = np.sort(rng.choice(total, size=min(n, total), replace=False))
    rows, offset, w = [], 0, 0
    for batch in pf.iter_batches(batch_size=65536, columns=['text', 'language', 'source']):
        end = offset + batch.num_rows
        hi = np.searchsorted(wanted, end)
        if hi > w:
            local = (wanted[w:hi] - offset).tolist()
            cols = batch.to_pydict()
            rows += [(offset + i, cols['text'][i], cols['language'][i], cols['source'][i]) for i in local]
            w = hi
        offset = end
        if w == len(wanted):
            break
    return rows, total


# References for decontamination: every benchmark eval text and all target text.
bench = {name: read_jsonl(paths.benchmark_eval(name)) for name in paths.BENCHMARK_NAMES}
target = {s: read_jsonl(paths.TARGET / s / f'{s}.jsonl') for s in ('train', 'validation', 'test')}
forbidden_hashes = {r['text_sha256'] for rows in (*bench.values(), *target.values()) for r in rows}

report = {'source': config.locks()[cfg['source']], 'config': cfg, 'languages': {}}
replay = {'train': [], 'validation': []}
for li, label in enumerate(REPLAY):
    rng = np.random.default_rng([cfg['seed'], li])
    rows, total = sample_rows(raw_dir / f'{label}.parquet', cfg['candidates_per_language'], rng)
    stats = Counter(source_rows=total, sampled_rows=len(rows))
    if bad := {lang for _, _, lang, _ in rows if lang != label}:
        raise SystemExit(f'{label}.parquet contains labels {bad}')
    script = label.split('_')[1]
    units, seen = [], set()
    excluded = set(cfg.get('exclude_sources', []))
    stats['excluded_source_rows'] = sum(1 for *_, src in rows if src in excluded)
    rows = [r for r in rows if r[3] not in excluded]
    for idx, text, _, src in rows:
        for si, unit in enumerate(segment(normalise(text), unit_cfg['max_chars'])):
            if letter_count(unit) < unit_cfg['min_letters'] or script_of(unit) != script:
                stats['filtered_length_or_script'] += 1
                continue
            h = text_sha256(unit)
            if h in seen:
                stats['exact_duplicate_removed'] += 1
                continue
            seen.add(h)
            units.append({'sample_id': f'openlid_v2:{label}:{idx}:{si}', 'text': unit, 'label': label,
                          'source': 'openlid_v2', 'subcorpus': src, 'doc_id': f'openlid_v2:{label}:{idx}',
                          'text_sha256': h})
    rep = clusters(len(units), near_duplicate_pairs([u['text'] for u in units], nd['shingle'],
                                                    nd['num_perm'], nd['threshold']))
    stats['near_duplicate_removed'] = sum(1 for i, r in enumerate(rep) if r != i)
    units = [u for i, u in enumerate(units) if rep[i] == i]

    before = len(units)
    units = [u for u in units if u['text_sha256'] not in forbidden_hashes]
    stats['decontam_exact_removed'] = before - len(units)
    refs = [r['text'] for rows in bench.values() for r in rows if r['label'] == label]
    near = near_matches([u['text'] for u in units], refs, nd['shingle'], nd['num_perm'], nd['threshold'])
    stats['decontam_near_removed'] = len(near)
    units = [u for i, u in enumerate(units) if i not in near]

    order = rng.permutation(len(units))
    need_val, need_train = cfg['per_language']['validation'], cfg['per_language']['train']
    if len(units) < need_val + need_train:
        raise SystemExit(f'{label}: only {len(units)} clean units, need {need_val + need_train}; '
                         f'raise replay.candidates_per_language')
    val = [units[i] for i in order[:need_val]]
    train = [units[i] for i in order[need_val:need_val + need_train]]
    replay['validation'] += sorted(val, key=lambda u: u['sample_id'])
    replay['train'] += sorted(train, key=lambda u: u['sample_id'])
    stats.update(clean_units=len(units), validation=len(val), train=len(train))
    stats['openlid_sources_train'] = dict(Counter(u['subcorpus'] for u in train).most_common())
    report['languages'][label] = dict(stats)
    print(label, dict(stats), flush=True)

files = []
for split in ('train', 'validation'):
    mixed = target[split] + replay[split]
    for name, data in ((f'replay_{split}.jsonl', replay[split]), (f'mixed_{split}.jsonl', mixed)):
        path = prepare_output(out_dir / name)
        with open(path, 'w', encoding='utf-8') as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        files.append(path)
    report[f'mixed_{split}_label_counts'] = dict(Counter(r['label'] for r in mixed))
rpath = prepare_output(out_dir / 'replay_report.json')
rpath.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
files.append(rpath)
write_manifest(out_dir, '03.prepare_datasets', files)
print(json.dumps({k: v for k, v in report.items() if k.startswith('mixed')}, indent=2))
