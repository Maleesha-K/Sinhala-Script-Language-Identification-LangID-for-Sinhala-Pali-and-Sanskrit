"""Build every results table from the saved per-sample predictions only.

Consistency checks (any failure stops the stage):
  - per eval set, every model was scored on the identical sample_id/text set;
  - macro F1 recomputed from predictions.csv equals summary.json and per_label.csv.
Tables (CSV + Markdown + LaTeX) in datasets/benchmark_results/tables/:
  table0_baselines        traditional baselines, short-text stress test: target macro F1 on the
                          target test split as full sentences and 5/3/1-word fragments, plus
                          figure_baselines_short_text.{png,pdf}
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
from lidpipe.evaluate import PHASES, eval_set_paths, fragment_set_paths
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
CURRENT = {es: sha256_file(p) for es, p in {**eval_set_paths(), **fragment_set_paths()}.items()}
FRAG_SETS = list(fragment_set_paths())
FRAG_NAMES = {s: 'Full sentence' if s == 'target_test' else f'{s.rsplit("_", 1)[1][:-1]} word'
              + ('s' if not s.endswith('_1w') else '') for s in FRAG_SETS}


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


def baseline_stress_test(title):
    """Baselines on the target test split at decreasing input length (macro F1 over the 3 target labels)."""
    rows = []
    for model, sets in results('baselines').items():
        row = {'model': model}
        for es in FRAG_SETS:
            if es in sets:
                saved, table = verified(model, 'baselines', es, sets[es])
                row[f'{es}_macro_f1'] = saved['macro_target3']
                row[f'{es}_macro_f1_ci'] = saved['macro_target3_ci95']
                row[f'{es}_accuracy'] = saved['accuracy']
                for l in TARGET:
                    row[f'{es}_{l}_f1'] = table.loc[l, 'f1']
        rows.append(row)
    stale_files = [*OUT.glob(f'{title}.*'), *OUT.glob(f'per_label_{title}_*.csv'),
                   *OUT.glob('figure_baselines_short_text.*')]
    for f in stale_files:
        prepare_output(f)
    if not rows:
        return
    last = f'{FRAG_SETS[-1]}_macro_f1'
    df = pd.DataFrame(rows).set_index('model').sort_values(last, ascending=False)
    files = []
    p = prepare_output(OUT / f'{title}.csv')
    df.to_csv(p)
    files.append(p)
    label = lambda m: NAMES.get(m.replace('\\', '/').split('/')[-1], m)   # model keys are OS paths
    best = {es: df[f'{es}_macro_f1'].max() for es in FRAG_SETS if f'{es}_macro_f1' in df}
    head = ['Model'] + [FRAG_NAMES[es] for es in FRAG_SETS]
    md = [f'## {title}', '', 'Traditional baselines trained on the target train split only; macro F1 over '
          'sin_Sinh, pli_Sinh, san_Sinh on the target test split (18,982 rows) as full sentences and as k-word '
          'fragments [95% bootstrap CI]. Best per column in bold.', '',
          '| ' + ' | '.join(head) + ' |', '|---|' + '---:|' * (len(head) - 1)]
    tex = ['\\begin{tabular}{l' + 'r' * (len(head) - 1) + '}', '\\toprule', ' & '.join(head) + ' \\\\', '\\midrule']
    for model, r in df.iterrows():
        cells_md, cells_tex = [], []
        for es in FRAG_SETS:
            v = r.get(f'{es}_macro_f1')
            top = v is not None and v == v and v == best.get(es)
            c = fmt(v, r.get(f'{es}_macro_f1_ci'))
            cells_md.append(f'**{c}**' if top else c)
            c = fmt(v)
            cells_tex.append(f'\\textbf{{{c}}}' if top else c)
        md.append('| ' + ' | '.join([label(model)] + cells_md) + ' |')
        tex.append(' & '.join([label(model)] + cells_tex) + ' \\\\')
    tex += ['\\bottomrule', '\\end{tabular}']
    for ext, text in (('md', '\n'.join(md)), ('tex', '\n'.join(tex))):
        p = prepare_output(OUT / f'{title}.{ext}')
        p.write_text(text + '\n', encoding='utf-8')
        files.append(p)
    for es in FRAG_SETS:
        cols = [f'{es}_{l}_f1' for l in TARGET]
        if set(cols) <= set(df.columns):
            p = prepare_output(OUT / f'per_label_{title}_{es}.csv')
            df[cols].set_axis(TARGET, axis=1).to_csv(p)
            files.append(p)
    files += short_text_figure(df, label)
    return files


def short_text_figure(df, label):
    """Line chart: macro F1 vs input length, one line per baseline. The three best
    at one word are coloured and bold; the rest recede in grey. Every line is
    direct-labelled with its 1-word score (no legend box needed)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ink, muted, grid, grey = '#0b0b0b', '#52514e', '#e4e3df', '#a3a29d'
    highlight = ['#2a78d6', '#eb6834', '#1baf7a']          # validated categorical slots 1-3
    cols = [f'{es}_macro_f1' for es in FRAG_SETS]
    data = df[cols].dropna()
    if data.empty:
        return []
    x = list(range(len(FRAG_SETS)))
    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    order = list(data.index)                                 # sorted by 1-word score, best first
    for rank, model in reversed(list(enumerate(order))):     # draw greys first, highlights on top
        color = highlight[rank] if rank < len(highlight) else grey
        # highlighted lines get distinct markers too, so near-coincident lines stay distinguishable
        ax.plot(x, data.loc[model].values, color=color, linewidth=2 if rank < 3 else 1.4,
                marker='osD'[rank] if rank < 3 else 'o', markersize=6 if rank < 3 else 5,
                markeredgecolor='#ffffff', markeredgewidth=1.2, zorder=3 if rank < 3 else 2)
    # Direct labels at the right end, nudged apart so none overlap.
    import math
    lo = math.floor((float(data.values.min()) - 0.03) * 10) / 10
    span = 1.005 - lo
    ys = sorted(((float(data.loc[m, cols[-1]]), m) for m in order), reverse=True)
    gap, placed = 0.04 * span, []
    for y, m in ys:
        y_lab = min(y, placed[-1] - gap) if placed else y
        placed.append(y_lab)
        rank = order.index(m)
        color = highlight[rank] if rank < len(highlight) else grey
        # a short line swatch in the series colour keys each label (identity is never colour-alone:
        # the name is always written; the swatch separates lines that end at almost the same value)
        ax.plot([x[-1] + 0.1, x[-1] + 0.22], [y_lab, y_lab], color=color, linewidth=2.4, clip_on=False,
                solid_capstyle='round')
        ax.annotate(f'{label(m)}  {y:.2f}', xy=(x[-1], y), xytext=(x[-1] + 0.28, y_lab), va='center',
                    fontsize=9, color=ink if rank < 3 else muted, fontweight='bold' if rank < 3 else 'normal',
                    annotation_clip=False)
    ax.set_xticks(x, [FRAG_NAMES[es] for es in FRAG_SETS])
    ax.set_xlim(-0.25, x[-1] + 0.08)
    ax.set_ylim(lo, 1.005)
    ax.set_ylabel('Macro-F1 (3 target languages)', color=muted)
    ax.set_title('All baselines saturate on full sentences; they separate on short fragments',
                 loc='left', fontsize=11, color=ink, fontweight='bold')
    ax.grid(axis='y', color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(grid)
    ax.tick_params(colors=muted, length=0)
    fig.subplots_adjust(left=0.09, right=0.70, top=0.9, bottom=0.1)
    files = []
    for ext in ('png', 'pdf'):
        p = prepare_output(OUT / f'figure_baselines_short_text.{ext}')
        fig.savefig(p, facecolor=fig.get_facecolor())
        files.append(p)
    plt.close(fig)
    return files


z, _ = build('zero_shot', 'table1_zero_shot')
z_index = z if not z.empty else None
baseline_stress_test('table0_baselines')
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
    if t == 'table0_baselines' and (OUT / 'figure_baselines_short_text.png').exists():
        report += ['![Baselines at decreasing input length](figure_baselines_short_text.png)', '']
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
