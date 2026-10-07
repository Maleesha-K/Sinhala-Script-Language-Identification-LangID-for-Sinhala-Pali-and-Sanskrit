"""Shared stage-02 logic: raw benchmark rows -> clean.jsonl + eval.jsonl.

clean.jsonl keeps every language (normalised, exact duplicates removed, rows
flagged). eval.jsonl is the 11-label subset every model is scored on. Neither
file ever contains target-language test data.
"""
import json
from collections import Counter, defaultdict

from . import config, paths
from .labels import ABSENT_BY_DESIGN, EXPECTED_SCRIPT, MULTI_SCRIPT, SCORED, gold_language
from .manifest import prepare_output, write_manifest
from .text import letter_count, normalise, script_of, text_sha256


def _assign_scripts(rows):
    """Script for rows without one: per-language majority, or the row's own
    script for multi-script languages. Asserts expected scripts."""
    majority = defaultdict(Counter)
    for r in rows:
        if r['script'] is None:
            majority[r['lang']][r['detected_script']] += 1
    majority = {lang: c.most_common(1)[0][0] for lang, c in majority.items()}
    for lang, want in EXPECTED_SCRIPT.items():
        if lang in majority and majority[lang] != want:
            raise SystemExit(f'{lang}: majority script is {majority[lang]}, expected {want}; '
                             f'check the label mapping')
    for r in rows:
        if r['script'] is None:
            own = r['detected_script']
            r['script'] = own if own in MULTI_SCRIPT.get(r['lang'], ()) else majority[r['lang']]


def build(name, raw_rows, expected_rows=None, extra_manifest=None):
    """raw_rows: iterable of dicts with sample_id, text, label_raw and optional
    `script` (ISO 15924, when the benchmark provides it) and `meta`."""
    min_letters = config.pipeline()['preprocess']['short_text_min_letters']
    stats = Counter()
    rows = []
    for r in raw_rows:
        stats['raw_rows'] += 1
        text = normalise(r['text'])
        if not text:
            stats['empty_removed'] += 1
            continue
        rows.append({'sample_id': r['sample_id'], 'text': text, 'label_raw': r['label_raw'],
                     'lang': gold_language(name, r['label_raw']), 'script': r.get('script'),
                     'detected_script': script_of(text), 'meta': r.get('meta') or {}})
    if expected_rows is not None and stats['raw_rows'] != expected_rows:
        raise SystemExit(f'{name}: read {stats["raw_rows"]} raw rows, expected {expected_rows}')
    _assign_scripts(rows)

    # Exact duplicates (same text, same label) are dropped; texts carrying
    # several labels are kept but record the other labels, so evaluation can
    # drop rows that are ambiguous between two scored labels.
    labels_of = defaultdict(set)
    for r in rows:
        r['label'] = f'{r["lang"]}_{r["script"]}'
        r['text_sha256'] = text_sha256(r['text'])
        labels_of[r['text_sha256']].add(r['label'])
    seen, clean = set(), []
    for r in rows:
        key = (r['text_sha256'], r['label'])
        if key in seen:
            stats['duplicates_removed'] += 1
            continue
        seen.add(key)
        flags = []
        letters = letter_count(r['text'])
        if letters == 0:
            flags.append('no_letters')
        elif letters < min_letters:
            flags.append('short')
        if letters and r['detected_script'] != r['script']:
            flags.append('wrong_script')
        other = sorted(labels_of[r['text_sha256']] - {r['label']})
        if other:
            stats['rows_with_conflicting_labels'] += 1
        clean.append({'sample_id': r['sample_id'], 'text': r['text'], 'label': r['label'],
                      'label_raw': r['label_raw'], 'text_sha256': r['text_sha256'], 'flags': flags,
                      'other_labels': other, **r['meta']})

    scored = set(SCORED)
    evaluation = [r for r in clean if r['label'] in scored and not scored & set(r['other_labels'])]
    stats['eval_ambiguous_removed'] = sum(1 for r in clean if r['label'] in scored) - len(evaluation)
    present = {r['label'] for r in evaluation}
    absent = ABSENT_BY_DESIGN.get(name, set())
    if missing := scored - present - absent:
        raise SystemExit(f'{name}: scored labels missing after cleaning: {sorted(missing)}')
    if unexpected := present & absent:
        raise SystemExit(f'{name}: {sorted(unexpected)} declared absent in labels.yaml but present')

    out_dir = paths.benchmark_dir(name)
    files = []
    for path, data in ((paths.benchmark_clean(name), clean), (paths.benchmark_eval(name), evaluation)):
        with open(prepare_output(path), 'w', encoding='utf-8') as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        files.append(path)
    eval_counts = Counter(r['label'] for r in evaluation)
    flag_counts = {l: dict(Counter(f for r in evaluation if r['label'] == l for f in r['flags']))
                   for l in SCORED}
    summary = {'stats': dict(stats), 'clean_rows': len(clean), 'clean_labels': len({r['label'] for r in clean}),
               'eval_rows': len(evaluation), 'eval_label_counts': {l: eval_counts.get(l, 0) for l in SCORED},
               'eval_flag_counts': {l: c for l, c in flag_counts.items() if c},
               'absent_by_design': sorted(absent), **(extra_manifest or {})}
    write_manifest(out_dir, '02.preprocess', files, extra={'summary': summary})
    print(json.dumps(summary, indent=2, ensure_ascii=False))
