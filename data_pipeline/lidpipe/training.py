"""The single fine-tuning protocol (config `training`), applied to every model:

  for each lr in the model family's 3-point grid:
      start from the pinned pretrained checkpoint (new labels zero-initialised)
      for epoch in 1..max_epochs:
          train one pass over the phase's training split
          score the phase's validation split with the shared scorer
  keep the (lr, epoch) with the best validation metric
  (ties keep the first found: smaller lr, then earlier epoch). Test sets are never read here.

Writes models/<phase_dir>/<model>/seed<k>/: best/ (checkpoint), selection_log.csv,
chosen.json.
"""
import json
import shutil
import time

import pandas as pd

from . import config, paths
from .labels import SCORED, TARGET, canonical_prediction
from .manifest import prepare_output, reset_dir
from .metrics import summarise

PHASE_DIRS = {'target_only': '02_target_only_sota', 'rehearsal': '03_global_rehearsal_sota'}


def read_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def phase_data(phase, smoke=False):
    """Training and validation rows for a phase; the same files for every model."""
    if phase == 'target_only':
        train = read_jsonl(paths.TARGET / 'train' / 'train.jsonl')
        val = read_jsonl(paths.TARGET / 'validation' / 'validation.jsonl')
        labels = TARGET
    else:
        mixed = paths.FINETUNE / 'replay_mixed'
        train = read_jsonl(mixed / 'mixed_train.jsonl')
        val = read_jsonl(mixed / 'mixed_validation.jsonl')
        labels = SCORED
    if smoke:
        train, val = _per_label(train, 200), _per_label(val, 50)
    return train, val, labels


def _per_label(rows, n):
    count, out = {}, []
    for r in rows:
        count[r['label']] = count.get(r['label'], 0) + 1
        if count[r['label']] <= n:
            out.append(r)
    return out


def model_dir(phase, model, seed, root=None):
    return (root or paths.MODELS / PHASE_DIRS[phase]) / model / f'seed{seed}'


def select(model, family, base_path, phase, seed, make_trainer, grid=None, epochs=None, root=None,
           param='lr'):
    """`grid` / `epochs` default to the fine-tuning config; the baselines pass
    their own hyperparameter grid (`param` names it) through the same loop."""
    cfg = config.pipeline()
    tcfg, smoke = cfg['training'], cfg.get('smoke', False)
    metric = tcfg['selection_metric'][phase]
    grid = grid if grid is not None else tcfg['lr_grid'][family]
    grid = grid[:1] if smoke else grid
    epochs = 1 if smoke else (epochs or tcfg['max_epochs'])
    train, val, labels = phase_data(phase, smoke)
    val_texts, val_gold = [r['text'] for r in val], [r['label'] for r in val]
    out = reset_dir(model_dir(phase, model, seed, root))
    log, best = [], None
    print(f'{model} {phase} seed={seed}: {len(train)} train / {len(val)} validation rows; '
          f'{param} grid {grid}; up to {epochs} epochs; selecting on validation {metric}', flush=True)
    for lr in grid:
        trainer = make_trainer(family, base_path, labels, seed, tcfg)
        try:
            for epoch in range(1, min(epochs, getattr(trainer, 'max_epochs', epochs)) + 1):
                t = time.time()
                trainer.epoch(train, lr, epoch)
                raw, _ = trainer.predict(val_texts)
                pred = [canonical_prediction(p, x) for p, x in zip(raw, val_texts)]
                s = summarise(val_gold, pred, n_boot=0)
                row = {param: lr, 'epoch': epoch, metric: s[metric], 'accuracy': s['accuracy'],
                       'macro_all': s['macro_all'], 'seconds': round(time.time() - t)}
                log.append(row)
                better = best is None or s[metric] > best[metric]  # strict: ties keep the earlier one
                print(f'  {param}={lr:<8g} epoch={epoch} val {metric}={s[metric]:.4f} acc={s["accuracy"]:.4f} '
                      f'({row["seconds"]}s){"  <- best so far" if better else ""}', flush=True)
                if better:
                    best = dict(row)
                    shutil.rmtree(out / 'best', ignore_errors=True)
                    trainer.save(out / 'best')
        finally:
            trainer.close()
    pd.DataFrame(log).to_csv(prepare_output(out / 'selection_log.csv'), index=False)
    chosen = {'model': model, 'family': family, 'phase': phase, 'seed': seed, 'selection_metric': metric,
              'chosen': best, 'hyperparameter': param, 'grid': grid, 'max_epochs': epochs, 'smoke': smoke,
              'train_rows': len(train), 'validation_rows': len(val), 'base_checkpoint': str(base_path),
              'rule': 'max validation metric; ties keep the first found: smaller lr, then earlier epoch'}
    prepare_output(out / 'chosen.json').write_text(json.dumps(chosen, indent=2) + '\n', encoding='utf-8')
    print(f'  chosen: {param}={best[param]} epoch={best["epoch"]} validation {metric}={best[metric]:.4f}', flush=True)
    return chosen
