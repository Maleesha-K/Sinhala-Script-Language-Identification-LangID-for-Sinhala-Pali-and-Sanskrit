"""The one scorer used for every model, dataset and table.

One-vs-rest per scored label over unrestricted predictions (a prediction
outside the 11 labels is simply wrong). F1 is NaN for labels with no gold
support, and macro averages are over labels that are present.
"""
import numpy as np
import pandas as pd

from .labels import REPLAY, SCORED, TARGET

MACROS = {'macro_all': SCORED, 'macro_target3': TARGET, 'macro_replay8': REPLAY}


def _counts(y, p):
    rows = []
    for label in SCORED:
        g, q = y == label, p == label
        rows.append((int((g & q).sum()), int((~g & q).sum()), int((g & ~q).sum()), int(g.sum())))
    return np.array(rows)  # columns: tp, fp, fn, support


def _f1(c):
    tp, fp, fn, support = c.T
    with np.errstate(invalid='ignore', divide='ignore'):
        f1 = np.where(support > 0, 2 * tp / (2 * tp + fp + fn), np.nan)
    return f1


def per_label(gold, pred):
    y, p = np.asarray(gold, dtype=str), np.asarray(pred, dtype=str)
    if len(y) != len(p):
        raise ValueError('prediction count mismatch')
    c = _counts(y, p)
    tp, fp, fn, support = c.T
    with np.errstate(invalid='ignore', divide='ignore'):
        precision = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        recall = np.where(support > 0, tp / support, np.nan)
    return pd.DataFrame({'label': SCORED, 'precision': precision, 'recall': recall,
                         'f1': _f1(c), 'support': support, 'tp': tp, 'fp': fp, 'fn': fn})


def _macros(f1):
    by_label = dict(zip(SCORED, f1))
    out = {}
    for name, labels in MACROS.items():
        vals = [by_label[l] for l in labels if not np.isnan(by_label[l])]
        out[name] = float(np.mean(vals)) if vals else None  # None: no label of this group present
    return out


def summarise(gold, pred, n_boot=1000, seed=0):
    """Accuracy and macro F1s, each with a seeded percentile bootstrap 95% CI."""
    y, p = np.asarray(gold, dtype=str), np.asarray(pred, dtype=str)
    point = {'accuracy': float((y == p).mean()), **_macros(_f1(_counts(y, p)))}
    point['n'] = int(len(y))
    point['labels_scored'] = int((per_label(y, p).support > 0).sum())
    point['outside_scored_predictions'] = int((~np.isin(p, SCORED)).sum())
    if n_boot:
        rng = np.random.default_rng(seed)
        draws = {k: [] for k in ('accuracy', *MACROS)}
        for _ in range(n_boot):
            i = rng.integers(0, len(y), len(y))
            yb, pb = y[i], p[i]
            draws['accuracy'].append((yb == pb).mean())
            for k, v in _macros(_f1(_counts(yb, pb))).items():
                draws[k].append(v)
        for k, v in draws.items():
            v = np.asarray([x for x in v if x is not None], dtype=float)
            point[f'{k}_ci95'] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else None
    return point
