"""Read-only audit of every dataset: benchmarks, target release, replay and
mixed sets. Never modifies its inputs.

Every check prints one PASS/FAIL line and is recorded in
datasets/audit/audit_report.{json,md}. Any FAIL exits non-zero, which stops
the pipeline. Leakage guarantees made by earlier stages (no near duplicates
across target splits, decontaminated replay data) are re-verified here
independently with MinHash LSH rather than trusted.
"""
import json
import re
import sys
from collections import Counter, defaultdict

from lidpipe import config, fragments, hub, paths
from lidpipe.dedup import near_duplicate_pairs, near_matches
from lidpipe.labels import ABSENT_BY_DESIGN, EXPECTED_SCRIPT, REPLAY, SCORED, TARGET
from lidpipe.manifest import prepare_output, sha256_file, verify_manifest, write_manifest
from lidpipe.text import is_normalised, script_of

REPLAY_DIR = paths.FINETUNE / 'replay_mixed'
LABEL_RE = re.compile(r'^[a-z][a-z-]*_[A-Z][a-z]{3}$')
SPLITS = ('train', 'validation', 'test')
cfg = config.pipeline()
nd = cfg['target_split']['near_dup']
checks, report = [], {}


def check(section, name, ok, detail=''):
    checks.append({'section': section, 'check': name, 'status': 'PASS' if ok else 'FAIL', 'detail': str(detail)})
    print(f'[{"PASS" if ok else "FAIL"}] {section}: {name}' + (f' -- {detail}' if detail else ''), flush=True)


def info(section, name, detail):
    checks.append({'section': section, 'check': name, 'status': 'INFO', 'detail': str(detail)})
    print(f'[INFO] {section}: {name} -- {detail}', flush=True)


def read(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def common_row_checks(section, rows, allowed):
    check(section, 'manifest-listed rows readable', bool(rows), f'{len(rows)} rows')
    bad = sorted({r['label'] for r in rows} - set(allowed))
    check(section, 'labels in allowed set', not bad, bad or sorted({r['label'] for r in rows}))
    check(section, 'labels are <lang>_<Script>', all(LABEL_RE.match(r['label']) for r in rows))
    n = sum(1 for r in rows if not is_normalised(r['text']))
    check(section, 'all text NFC-normalised', not n, f'{n} rows not normalised')
    n = sum(v - 1 for v in Counter(r['sample_id'] for r in rows).values())
    check(section, 'sample_id unique', not n, f'{n} duplicates')


# ---------------------------------------------------------------- benchmarks
# eval.jsonl is the hybrid set: the benchmark's own replay-label rows plus the
# whole target test split in place of the benchmark's Sinhala-script rows.
target_test_rows = read(paths.TARGET / 'test' / 'test.jsonl')
target_test_ids = Counter((r['sample_id'], r['text_sha256'], r['label']) for r in target_test_rows)
eval_rows, own_rows, report['benchmarks'] = {}, {}, {}
for name in paths.BENCHMARK_NAMES:
    sec = f'benchmark/{name}'
    problems = verify_manifest(paths.benchmark_dir(name)) + verify_manifest(paths.benchmark_raw(name))
    check(sec, 'raw + processed files match their sha256 manifests', not problems, problems)
    clean, ev = read(paths.benchmark_clean(name)), read(paths.benchmark_eval(name))
    common_row_checks(f'{sec}/clean', clean, {r['label'] for r in clean})
    common_row_checks(f'{sec}/eval', ev, SCORED)
    n = sum(v - 1 for v in Counter((r['text_sha256'], r['label']) for r in clean).values())
    check(sec, 'no duplicate (text, label) rows', not n, f'{n} duplicates')
    origins = Counter(r.get('origin') for r in ev)
    check(sec, 'every eval row has origin benchmark or target_test',
          set(origins) <= {'benchmark', 'target_test'}, dict(origins))
    own = [r for r in ev if r.get('origin') == 'benchmark']
    hyb = [r for r in ev if r.get('origin') == 'target_test']
    clean_ids = {r['sample_id'] for r in clean}
    check(sec, 'benchmark-origin eval rows are a subset of clean', all(r['sample_id'] in clean_ids for r in own))
    n = sum(1 for r in own if r['label'] in TARGET)
    check(sec, "hybrid: none of the benchmark's own Sinhala-script target rows remain", not n, f'{n} rows')
    got = Counter((r['sample_id'], r['text_sha256'], r['label']) for r in hyb)
    check(sec, 'hybrid: target rows are exactly the target test split', got == target_test_ids,
          f'{len(hyb)} rows vs {len(target_test_rows)} in target test')
    n = len({r['text_sha256'] for r in own} & {r['text_sha256'] for r in hyb})
    check(sec, 'hybrid: no benchmark row shares text with a target test row', not n, f'{n} texts')
    absent = ABSENT_BY_DESIGN.get(name, set())
    own_scored = {r['label'] for r in clean if r['label'] in SCORED}
    check(sec, 'declared-absent labels really absent from the benchmark itself', not (own_scored & absent),
          sorted(own_scored & absent) or f'absent by design: {sorted(absent)}')
    present = {r['label'] for r in ev}
    missing = set(SCORED) - present - (absent - set(TARGET))
    check(sec, 'every scored label present in the hybrid eval set (except declared-absent replay labels)',
          not missing, sorted(missing) or sorted(present))
    manifest = json.loads((paths.benchmark_dir(name) / 'manifest.json').read_text())
    check(sec, 'hybrid built from the current target test file',
          manifest['summary']['hybrid']['target_test_file_sha256'] == sha256_file(paths.TARGET / 'test' / 'test.jsonl'))
    info(sec, "benchmark's own target-label rows replaced", manifest['summary']['hybrid']['benchmark_rows_replaced'])
    ambiguous = sum(1 for r in ev if set(r['other_labels']) & set(SCORED))
    check(sec, 'no eval text carries two scored labels', not ambiguous, f'{ambiguous} rows')
    arb = [r for r in ev if r['label'] == 'arb_Arab']
    check(sec, 'Arabic policy: arb_Arab gold rows come only from raw `arb`',
          all(r['label_raw'] == 'arb' for r in arb), f'{len(arb)} arb_Arab rows')
    for lang, script in EXPECTED_SCRIPT.items():
        rows = [r for r in ev if r['label'].startswith(lang + '_')]
        if rows:
            check(sec, f'{lang} labelled with expected script {script}',
                  all(r['label'].endswith('_' + script) for r in rows))
    if name == 'wili_2018':
        n = sum(1 for r in clean if not r['sample_id'].startswith('wili_2018:test:'))
        check(sec, 'WiLI rows come from the test split only', not n, f'{n} non-test rows')
    expected = config.locks()[name]['expected_rows']
    raw_rows = manifest['summary']['stats']['raw_rows']
    check(sec, 'raw row count equals pinned count', raw_rows == expected, f'{raw_rows} vs {expected}')
    counts = Counter(r['label'] for r in ev)
    flags = defaultdict(Counter)
    for r in ev:
        flags[r['label']].update(r['flags'])
    report['benchmarks'][name] = {
        'clean_rows': len(clean), 'eval_rows': len(ev), 'eval_origin': dict(origins),
        'eval': {l: {'rows': counts.get(l, 0), **flags[l]} for l in SCORED}}
    eval_rows[name], own_rows[name] = ev, own

eval_hashes = {n: {r['text_sha256'] for r in rows} for n, rows in eval_rows.items()}
own_hashes = {n: {r['text_sha256'] for r in rows} for n, rows in own_rows.items()}
for i, a in enumerate(own_hashes):
    for b in list(own_hashes)[i + 1:]:
        info('benchmarks', f'overlap {a} ~ {b} (benchmark rows)', f'{len(own_hashes[a] & own_hashes[b])} shared texts')

# ------------------------------------------------------------ target release
sec = 'target'
problems = verify_manifest(paths.TARGET)
check(sec, 'files match their sha256 manifest', not problems, problems)
lock = config.locks()['target_dataset']
pinned_ok = all(sha256_file(paths.TARGET / (f.removesuffix('.jsonl')) / f if f.endswith('.jsonl')
                            else paths.TARGET / f) == sha for f, sha in lock['files_sha256'].items())
where = hub.resolve(lock)[0] if lock['kind'] == 'dataset' else lock['path']
check(sec, 'files byte-identical to the release pinned in locks.json', pinned_ok, f'{lock["kind"]}: {where}')
target = {s: read(paths.TARGET / s / f'{s}.jsonl') for s in SPLITS}
max_chars = cfg['target_split']['max_chars']
for s, rows in target.items():
    common_row_checks(f'{sec}/{s}', rows, TARGET)
    check(f'{sec}/{s}', f'units are sentence-level (<= {max_chars} chars)', all(len(r['text']) <= max_chars for r in rows))
    n = sum(1 for r in rows if script_of(r['text']) != 'Sinh')
    check(f'{sec}/{s}', 'all text is Sinhala script', not n, f'{n} rows')
    check(f'{sec}/{s}', 'all three target labels present', {r['label'] for r in rows} == set(TARGET))
split_of_hash, split_of_block = defaultdict(set), defaultdict(set)
for s, rows in target.items():
    for r in rows:
        split_of_hash[r['text_sha256']].add(s)
        split_of_block[r['block_id']].add(s)
n = sum(1 for v in split_of_hash.values() if len(v) > 1)
check(sec, 'no text shared between splits', not n, f'{n} texts')
n = sum(1 for v in split_of_block.values() if len(v) > 1)
check(sec, 'no document block spans two splits', not n, f'{n} blocks')
flat = [r for s in SPLITS for r in target[s]]
pairs = near_duplicate_pairs([r['text'] for r in flat], nd['shingle'], nd['num_perm'], nd['threshold'])
side = [s for s in SPLITS for _ in target[s]]
n = sum(1 for i, j in pairs if side[i] != side[j])
check(sec, f'no near-duplicates across splits (MinHash, Jaccard >= {nd["threshold"]})', not n, f'{n} pairs')
split_report = json.loads((paths.TARGET / 'split_report.json').read_text(encoding='utf-8'))
prov = split_report.get('provenance', {})
check(sec, 'parallel rows verified against the public corpus at build time',
      prov and prov['rows_checked'] == prov['rows_matching_public_alignment'], prov or 'no provenance record')
report['target'] = {s: dict(Counter(r['label'] for r in rows)) for s, rows in target.items()}
report['target_split_report'] = split_report

# ------------------------------------------------------------ replay / mixed
sec = 'replay'
problems = verify_manifest(REPLAY_DIR) + verify_manifest(paths.FINETUNE / 'openlid_v2' / 'raw')
check(sec, 'files match their sha256 manifests', not problems, problems)
sets = {f: read(REPLAY_DIR / f'{f}.jsonl') for f in
        ('replay_train', 'replay_validation', 'mixed_train', 'mixed_validation')}
for f, rows in sets.items():
    common_row_checks(f'{sec}/{f}', rows, REPLAY if f.startswith('replay') else SCORED)
per = cfg['replay']['per_language']
for s in ('train', 'validation'):
    counts = Counter(r['label'] for r in sets[f'replay_{s}'])
    check(sec, f'replay_{s} balanced: {per[s]} per replay label',
          all(counts.get(l) == per[s] for l in REPLAY), dict(counts))
    mixed = sets[f'mixed_{s}']
    want = Counter(r['sample_id'] for r in target[s] + sets[f'replay_{s}'])
    check(sec, f'mixed_{s} == target {s} + replay_{s}', Counter(r['sample_id'] for r in mixed) == want,
          f'{len(mixed)} rows')
rt, rv = sets['replay_train'], sets['replay_validation']
excluded = set(cfg['replay'].get('exclude_sources', []))
n = sum(1 for r in rt + rv if r['subcorpus'] in excluded)
check(sec, f'no rows from excluded benchmark-origin sources {sorted(excluded)}', not n, f'{n} rows')
n = len({r['text_sha256'] for r in rt} & {r['text_sha256'] for r in rv})
check(sec, 'replay train/validation share no text', not n, f'{n} texts')
for label in REPLAY:
    a = [r['text'] for r in rv if r['label'] == label]
    b = [r['text'] for r in rt if r['label'] == label]
    n = len(near_matches(a, b, nd['shingle'], nd['num_perm'], nd['threshold']))
    check(sec, f'{label}: no validation text near-duplicates a train text', not n, f'{n} rows')

# ------------------------------------------- short-text stress-test fragments
sec = 'fragments'
problems = verify_manifest(paths.FRAGMENTS)
check(sec, 'files match their sha256 manifest', not problems, problems)
fcfg = cfg['fragments']
source = {r['sample_id']: r for r in target['test']}
report['fragments'] = {}
for k in fragments.sizes():
    name = fragments.name(k)
    rows = read(fragments.path(k))
    common_row_checks(f'{sec}/{name}', rows, TARGET)
    check(sec, f'{name}: one fragment per target test row, same id and label',
          Counter((r['sample_id'], r['label']) for r in rows)
          == Counter((r['sample_id'], r['label']) for r in target['test']), f'{len(rows)} rows')
    bad_len = bad_span = 0
    for r in rows:
        words, src = r['text'].split(), fragments.words_of(source[r['sample_id']]['text'])
        if len(words) != min(k, len(src)):
            bad_len += 1
        if not any(src[i:i + len(words)] == words for i in range(len(src) - len(words) + 1)):
            bad_span += 1
    check(sec, f'{name}: exactly {k} words (fewer only when the sentence is shorter)', not bad_len, f'{bad_len} rows')
    check(sec, f'{name}: every fragment is a contiguous run of words of its source sentence', not bad_span,
          f'{bad_span} rows')
    rebuilt = sum(1 for r in rows
                  if fragments.fragment(source[r['sample_id']]['text'], k, fcfg['seed'], r['sample_id']) != r['text'])
    check(sec, f'{name}: reproducible from config fragments (seed {fcfg["seed"]})', not rebuilt, f'{rebuilt} rows differ')
    report['fragments'][name] = dict(Counter(r['label'] for r in rows))

# --------------------------------------------------- contamination gates
sec = 'contamination'
all_eval = set().union(*eval_hashes.values())
target_test = {r['text_sha256'] for r in target['test']}
train_sets = {'target/train': target['train'], 'target/validation': target['validation'], **sets}
report['contamination'] = {}
for name, rows in train_sets.items():
    h = {r['text_sha256'] for r in rows}
    nb, nt = len(h & all_eval), len(h & target_test)
    report['contamination'][name] = {'benchmark_eval_exact': nb, 'target_test_exact': nt}
    check(sec, f'{name}: no benchmark eval text (exact)', not nb, f'{nb} texts')
    check(sec, f'{name}: no target test text (exact)', not nt, f'{nt} texts')
for label in REPLAY:
    refs = [r['text'] for rows in eval_rows.values() for r in rows if r['label'] == label]
    q = [r['text'] for r in rt + rv if r['label'] == label]
    n = len(near_matches(q, refs, nd['shingle'], nd['num_perm'], nd['threshold'])) if refs else 0
    report['contamination'][f'replay {label} near-dup'] = n
    check(sec, f'replay {label}: no near-duplicate of a benchmark eval text', not n, f'{n} rows')
n = len(target_test & set().union(*own_hashes.values()))
check(sec, "target test shares no text with any benchmark's own eval rows", not n, f'{n} texts')

# ------------------------------------------------------------------ report
failed = [c for c in checks if c['status'] == 'FAIL']
report['checks'] = checks
out_dir = paths.DATASETS / 'audit'
json_path = prepare_output(out_dir / 'audit_report.json')
json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
md = ['# Dataset audit', '',
      f'{sum(c["status"] == "PASS" for c in checks)} passed, {len(failed)} failed, '
      f'{sum(c["status"] == "INFO" for c in checks)} informational.', '',
      '## Checks', '', '| status | section | check | detail |', '|---|---|---|---|']
md += [f'| {c["status"]} | {c["section"]} | {c["check"]} | {c["detail"][:160].replace("|", "/")} |' for c in checks]
for name, b in report['benchmarks'].items():
    md += ['', f'## Benchmark {name} (hybrid eval set)', '',
           f'clean rows {b["clean_rows"]:,}; eval rows {b["eval_rows"]:,} '
           f'({b["eval_origin"].get("benchmark", 0):,} from the benchmark, '
           f'{b["eval_origin"].get("target_test", 0):,} from the target test split)', '',
           '| label | rows | short | no_letters | wrong_script |', '|---|---:|---:|---:|---:|']
    md += [f'| {l} | {e["rows"]} | {e.get("short", 0)} | {e.get("no_letters", 0)} | {e.get("wrong_script", 0)} |'
           for l, e in b['eval'].items()]
md += ['', '## Target release (rows per label)', '', '| split | ' + ' | '.join(TARGET) + ' |',
       '|---|' + '---:|' * len(TARGET)]
md += [f'| {s} | ' + ' | '.join(str(c.get(l, 0)) for l in TARGET) + ' |' for s, c in report['target'].items()]
md_path = prepare_output(out_dir / 'audit_report.md')
md_path.write_text('\n'.join(md) + '\n', encoding='utf-8')
write_manifest(out_dir, '04.dataset_checking', [json_path, md_path], readonly=False)
print(f'\n{md[2]}\nFull report: {md_path.relative_to(paths.ROOT)}')
sys.exit(1 if failed else 0)
