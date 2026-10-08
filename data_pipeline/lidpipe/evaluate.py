"""The one evaluation routine for every model and phase.

Each model is scored on the same four evaluation sets: the target test split
alone (Sinhala/Pali/Sanskrit, Sinhala script), and the hybrid 11-label eval
sets of FLORES+, WiLI-2018 and CommonLID, in which each benchmark's own
Sinhala-script rows are replaced by that same target test split
(lidpipe.benchmarks). Predictions are unrestricted (a model may
output any of its labels) and mapped through lidpipe.labels.canonical_prediction.
Per set this writes:
    predictions.csv  sample_id, text_sha256, origin, gold, prediction_raw, prediction, confidence, flagged
    per_label.csv    precision / recall / F1 / support / tp / fp / fn per scored label
    confusion.csv    gold x prediction counts
    summary.json     accuracy + macro F1s with bootstrap CIs, on all rows and on unflagged rows
Tables (stage 08) are computed from these files only.
"""
import json
from pathlib import Path

import pandas as pd

from . import config, paths
from .labels import canonical_prediction
from .manifest import prepare_output, sha256_file, write_manifest
from .metrics import per_label, summarise

PHASES = {'baselines': '00_traditional_ml_baselines', 'zero_shot': '01_zero_shot',
          'target_only': '02_target_only', 'rehearsal': '03_multilingual_rehearsal'}


def eval_set_paths():
    sets = {'target_test': paths.TARGET / 'test' / 'test.jsonl'}
    sets.update({n: paths.benchmark_eval(n) for n in paths.BENCHMARK_NAMES})
    return sets


def fragment_set_paths():
    """Baseline short-text stress test: target test as full sentences and as k-word fragments."""
    from . import fragments
    sets = {'target_test': paths.TARGET / 'test' / 'test.jsonl'}
    sets.update({fragments.name(k): fragments.path(k) for k in fragments.sizes()})
    return sets


def load_eval_set(path, smoke=False):
    with open(path, encoding='utf-8') as f:
        rows = [json.loads(line) for line in f]
    if smoke:  # first 100 rows per label: exercises every code path quickly
        kept, count = [], {}
        for r in rows:
            count[r['label']] = count.get(r['label'], 0) + 1
            if count[r['label']] <= 100:
                kept.append(r)
        rows = kept
    return rows


def result_dir(phase, model):
    return paths.RESULTS / PHASES[phase] / model


def evaluate(model_name, phase, predict, metadata=None, sets=None):
    """Run `predict(texts) -> (raw_labels, confidences)` on every eval set
    (`sets`: {name: path}, default eval_set_paths())."""
    cfg = config.pipeline()
    smoke, boot = cfg.get('smoke', False), cfg['bootstrap']
    out_root = result_dir(phase, model_name)
    files, overview = [], {}
    for name, path in (sets or eval_set_paths()).items():
        rows = load_eval_set(path, smoke)
        texts = [r['text'] for r in rows]
        raw, conf = predict(texts)
        pred = [canonical_prediction(p, t) for p, t in zip(raw, texts)]
        gold = [r['label'] for r in rows]
        flagged = [bool(r.get('flags')) for r in rows]
        out = out_root / name
        frame = pd.DataFrame({'sample_id': [r['sample_id'] for r in rows],
                              'text_sha256': [r['text_sha256'] for r in rows],
                              'origin': [r.get('origin', 'target_test') for r in rows],
                              'gold': gold, 'prediction_raw': raw, 'prediction': pred,
                              'confidence': conf, 'flagged': flagged})
        p = prepare_output(out / 'predictions.csv')
        frame.to_csv(p, index=False)
        files.append(p)
        table = per_label(gold, pred)
        p = prepare_output(out / 'per_label.csv')
        table.to_csv(p, index=False)
        files.append(p)
        p = prepare_output(out / 'confusion.csv')
        pd.crosstab(frame.gold, frame.prediction).to_csv(p)
        files.append(p)
        clean = frame[~frame.flagged]
        summary = {'eval_set': name, 'model': model_name, 'phase': phase, 'smoke': smoke,
                   'eval_file_sha256': sha256_file(path),   # results from an older eval set are stale
                   'all_rows': summarise(gold, pred, boot['resamples'], boot['seed']),
                   'unflagged_rows': summarise(clean.gold.tolist(), clean.prediction.tolist(),
                                               boot['resamples'], boot['seed']),
                   'metadata': metadata or {}}
        p = prepare_output(out / 'summary.json')
        p.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        files.append(p)
        s = summary['all_rows']
        overview[name] = {k: s[k] for k in ('accuracy', 'macro_all', 'macro_target3', 'macro_replay8')}
        fmt = lambda v: 'n/a' if v is None else f'{v:.4f}'
        print(f'  {model_name:<14} {phase:<12} {name:<12} n={s["n"]:<6} acc={fmt(s["accuracy"])} '
              f'macroF1={fmt(s["macro_all"])} target3={fmt(s["macro_target3"])} '
              f'replay8={fmt(s["macro_replay8"])}', flush=True)
    write_manifest(out_root, f'evaluate.{phase}', files, extra={'overview': overview, 'metadata': metadata or {}},
                   readonly=False)
    return overview


def finalize_phase(phase):
    """One manifest over every file of a phase (all models evaluated so far),
    so the runner can verify the phase as a single stage output."""
    root = paths.RESULTS / PHASES[phase]
    files = sorted(p for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json')
    write_manifest(root, f'phase.{phase}', files, readonly=False)
