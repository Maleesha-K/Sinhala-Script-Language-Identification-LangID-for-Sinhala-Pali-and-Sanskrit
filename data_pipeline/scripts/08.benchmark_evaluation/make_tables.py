"""Build every results table from the saved per-sample predictions only.

Consistency checks (any failure stops the stage):
  - per eval set, every model was scored on the identical sample_id/text set;
  - macro F1 recomputed from predictions.csv equals summary.json and per_label.csv.
Tables (CSV + Markdown + LaTeX) in datasets/benchmark_results/tables/:
  table0_baselines        traditional baselines (target test, and benchmarks for rehearsal)
  table1_zero_shot        pretrained models unchanged
  table2_target_only      fine-tuned on target data only
  table3_rehearsal        fine-tuned on target + replay data, with forgetting (delta vs zero-shot)
  per_label_<phase>_<set> F1 of all 11 labels for every model
Columns: target-test macro F1 over the 3 target labels and its per-label F1, then
each hybrid benchmark's macro F1 over the scored labels present in it (the
benchmark's replay-label rows + the target test split in place of its own
Sinhala-script rows). The CSVs also split each hybrid benchmark into its
target-3 and replay-8 macro F1. 95% bootstrap CIs are in the CSVs and the Markdown.
"""
import json
import sys

import pandas as pd

from lidpipe import paths
from lidpipe.evaluate import PHASES, eval_set_paths
from lidpipe.labels import SCORED, TARGET
from lidpipe.manifest import prepare_output, sha256_file, write_manifest
from lidpipe.metrics import per_label, summarise

OUT = paths.RESULTS / 'tables'
SETS = list(eval_set_paths())
BENCH = [s for s in SETS if s != 'target_test']
NAMES = {'nllb_lid218': 'NLLB-218 (fastText)', 'glotlid_v3': 'GlotLID v3', 'openlid_v3': 'OpenLID v3',
         'lid176': 'fastText LID-176', 'conlid': 'ConLID', 'xlmr': 'XLM-R LangID (papluca)',
         'nb': 'Multinomial NB', 'svm': 'Linear SVM', 'logreg': 'Char n-gram LogReg', 'xgboost': 'XGBoost',
         'fasttext_scratch': 'fastText (scratch)', 'char_cnn': 'Char-CNN', 'char_bigru': 'Char-BiGRU'}
failures, sample_sets, stale = [], {}, {}
CURRENT = {es: sha256_file(p) for es, p in eval_set_paths().items()}


def results(phase):
    """{model: {eval_set: directory}} for every completed evaluation of a phase."""
    root = paths.RESULTS / PHASES[phase]
    found = {}
    for summary in sorted(root.rglob('summary.json')):
        d = summary.parent
        model = str(d.parent.relative_to(root))
        # Scored on an older version of this eval set (e.g. before the hybrid
        # benchmarks): left out of the tables and listed, never mixed in.
        if json.loads(summary.read_text(encoding='utf-8')).get('eval_file_sha256') != CURRENT.get(d.name):
            stale.setdefault(f'{phase}/{model}', []).append(d.name)
            continue
        found.setdefault(model, {})[d.name] = d
    return found


def verified(model, phase, eval_set, d):
    """Recompute everything from predictions.csv and cross-check the saved files."""
    pred = pd.read_csv(d / 'predictions.csv', dtype={'sample_id': str, 'text_sha256': str}, keep_default_na=False)
    summary = json.loads((d / 'summary.json').read_text(encoding='utf-8'))
    s = summarise(pred.gold.tolist(), pred.prediction.tolist(), n_boot=0)
    saved = summary['all_rows']
    for k in ('accuracy', 'macro_all', 'macro_target3', 'macro_replay8'):
        a, b = s[k], saved[k]
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
            failures.append(f'{phase}/{model}/{eval_set}: {k} recomputed {a} != saved {b}')
    table = per_label(pred.gold.tolist(), pred.prediction.tolist())
    stored = pd.read_csv(d / 'per_label.csv')
    if not table.f1.fillna(-1).round(12).equals(stored.f1.fillna(-1).round(12)):
        failures.append(f'{phase}/{model}/{eval_set}: per_label.csv disagrees with predictions.csv')
    key = frozenset(zip(pred.sample_id, pred.text_sha256))
    ref = sample_sets.setdefault((eval_set, summary.get('smoke', False)), (key, f'{phase}/{model}'))
    if ref[0] != key:
        failures.append(f'{phase}/{model}/{eval_set}: scored on different samples than {ref[1]}')
    return saved, table.set_index('label')


def fmt(v, ci=None):
    if v is None or v != v:
        return '–'
    return f'{v:.4f}' if not ci else f'{v:.4f} [{ci[0]:.3f}, {ci[1]:.3f}]'


def build(phase, title, zero_shot=None):
    rows, per_set = [], {}
    for model, sets in results(phase).items():
        row = {'model': model}
        for es in SETS:
            if es not in sets:
                continue
            saved, table = verified(model, phase, es, sets[es])
            per_set.setdefault(es, {})[model] = table.f1
            if es == 'target_test':
                row['target_macro_f1'] = saved['macro_target3']
                row['target_macro_f1_ci'] = saved['macro_target3_ci95']
                row['target_accuracy'] = saved['accuracy']
                for l in TARGET:
                    row[f'target_{l}_f1'] = table.loc[l, 'f1']
            else:
                row[f'{es}_macro_f1'] = saved['macro_all']
                row[f'{es}_macro_f1_ci'] = saved['macro_all_ci95']
                row[f'{es}_target3_macro_f1'] = saved['macro_target3']
                row[f'{es}_replay8_macro_f1'] = saved['macro_replay8']
                if zero_shot is not None and model.split('/')[-1] in zero_shot.index:
                    row[f'{es}_delta_vs_zero_shot'] = saved['macro_all'] - zero_shot.loc[model.split('/')[-1],
                                                                                          f'{es}_macro_f1']
        rows.append(row)
    df = pd.DataFrame(rows)
    if df.empty:  # remove tables from an earlier run so they cannot be mistaken for current ones
        for f in [*OUT.glob(f'{title}.*'), *OUT.glob(f'per_label_{title}_*.csv')]:
            prepare_output(f)
        return df, per_set
    df = df.set_index('model')
    files = []
    p = prepare_output(OUT / f'{title}.csv')
    df.to_csv(p)
    files.append(p)
    # Markdown and LaTeX: headline columns with CIs.
    cols = ['target_macro_f1'] + [f'target_{l}_f1' for l in TARGET] + [f'{b}_macro_f1' for b in BENCH]
    head = ['Model', 'Target macro-F1 [95% CI]', 'sin_Sinh', 'pli_Sinh', 'san_Sinh'] + [f'{b} macro-F1' for b in BENCH]
    if zero_shot is not None:
        head += [f'Δ {b}' for b in BENCH]
    md = [f'## {title}', '', '| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    tex = ['\\begin{tabular}{l' + 'r' * (len(head) - 1) + '}', '\\toprule',
           ' & '.join(h.replace('_', '\\_').replace('Δ', '$\\Delta$') for h in head) + ' \\\\', '\\midrule']
    for model, r in df.iterrows():
        name = NAMES.get(model.split('/')[-1], model) + (f' ({model.split("/")[0]})' if '/' in model else '')
        cells = [fmt(r.get('target_macro_f1'), r.get('target_macro_f1_ci'))]
        cells += [fmt(r.get(f'target_{l}_f1')) for l in TARGET]
        cells += [fmt(r.get(f'{b}_macro_f1'), r.get(f'{b}_macro_f1_ci')) for b in BENCH]
        if zero_shot is not None:
            cells += ['–' if pd.isna(r.get(f'{b}_delta_vs_zero_shot')) else f'{r[f"{b}_delta_vs_zero_shot"]:+.4f}'
                      for b in BENCH]
        md.append('| ' + ' | '.join([name] + cells) + ' |')
        tex.append(' & '.join([name.replace('_', '\\_')] + [c.split(' [')[0] for c in cells]) + ' \\\\')
    tex += ['\\bottomrule', '\\end{tabular}']
    for ext, text in (('md', '\n'.join(md)), ('tex', '\n'.join(tex))):
        p = prepare_output(OUT / f'{title}.{ext}')
        p.write_text(text + '\n', encoding='utf-8')
        files.append(p)
    for es, f1s in per_set.items():
        t = pd.DataFrame(f1s).T[SCORED]
        p = prepare_output(OUT / f'per_label_{title}_{es}.csv')
        t.to_csv(p)
        files.append(p)
    return df, per_set


z, _ = build('zero_shot', 'table1_zero_shot')
z_index = z if not z.empty else None
build('baselines', 'table0_baselines')
build('target_only', 'table2_target_only', zero_shot=z_index)
build('rehearsal', 'table3_rehearsal', zero_shot=z_index)

report = ['# Results', '', 'All numbers recomputed from per-sample predictions; '
          'target macro-F1 is over sin_Sinh, pli_Sinh, san_Sinh on the held-out target test split; '
          'benchmark macro-F1 is over the scored labels present in the hybrid benchmark set, i.e. the '
          "benchmark's own rows for the replay labels plus the target test split in place of its "
          'Sinhala-script rows (absent labels are excluded, never counted as 0). '
          'Δ = change vs the same model zero-shot.', '']
for t in ('table0_baselines', 'table1_zero_shot', 'table2_target_only', 'table3_rehearsal'):
    f = OUT / f'{t}.md'
    report += [f.read_text(encoding='utf-8') if f.exists() else f'## {t}\n\n(no results yet)', '']
pending = [f'{m}' for m in ('xlmr',) if not (paths.RESULTS / PHASES['rehearsal'] / m).exists()]
if pending:
    report += ['Pending (not trained yet): ' + ', '.join(NAMES[m] for m in pending), '']
if stale:
    report += ['Left out (scored on an older version of the eval set; re-run the stage that produced them): '
               + '; '.join(f'{m} ({", ".join(v)})' for m, v in stale.items()), '']
if failures:
    report += ['## Consistency check FAILURES', ''] + [f'- {f}' for f in failures]
else:
    report += ['Consistency checks passed: every model was scored on identical samples per eval set, and '
               'every macro-F1 recomputes exactly from the saved predictions.']
p = prepare_output(OUT / 'results.md')
p.write_text('\n'.join(report) + '\n', encoding='utf-8')
write_manifest(OUT, '08.make_tables', sorted(x for x in OUT.iterdir() if x.name != 'manifest.json'), readonly=False)
print('\n'.join(report))
for f in failures:
    print('[FAIL]', f)
sys.exit(1 if failures else 0)
