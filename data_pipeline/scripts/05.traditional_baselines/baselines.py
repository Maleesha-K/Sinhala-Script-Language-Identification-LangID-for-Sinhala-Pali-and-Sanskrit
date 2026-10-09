"""Seven traditional baselines, trained from scratch on the target train split
only (Sinhala/Pali/Sanskrit) and selected on target validation with the same
rule as the fine-tuned models (lidpipe.training.select), then scored on the
short-text stress test: the target test split as full sentences and as 5-, 3-
and 1-word fragments (stage 03, lidpipe/fragments.py). Macro F1 is over the 3
target labels.

Results: datasets/benchmark_results/00_traditional_ml_baselines/<phase>/<model>/<set>/
         <set> = target_test (full sentence), target_test_5w, target_test_3w, target_test_1w
Models:  models/00_traditional_ml_baselines/<phase>/<model>/seed<k>/

A (phase, model, seed) already trained with the same protocol is not retrained,
and is re-evaluated only when the eval sets changed, so a crashed run resumes
where it stopped (--force retrains all).
"""
import gc
import hashlib
import json
import shutil

from lidpipe import baselines, config, paths
from lidpipe.env import flag
from lidpipe.evaluate import PHASES, finalize_phase, evaluate, fragment_set_paths, result_dir
from lidpipe.manifest import content_fingerprint, write_manifest
from lidpipe.models import selected
from lidpipe.training import model_dir, select

cfg = config.pipeline()
b = cfg['baselines']
ROOT = paths.MODELS / '00_traditional_ml_baselines'
SETS = fragment_set_paths()


def protocol_hash(name):
    """Everything training depends on (not which phases run or how they are scored)."""
    blob = {'baselines': {k: v for k, v in b.items() if k not in ('grid', 'phases')}, 'grid': b['grid'][name],
            'selection': cfg['training']['selection_metric'], 'smoke': cfg.get('smoke', False),
            'data': content_fingerprint([paths.TARGET, paths.FINETUNE / 'replay_mixed'])}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def eval_hash():
    """Everything evaluation depends on: the eval sets and the bootstrap settings."""
    blob = {'bootstrap': cfg['bootstrap'], 'smoke': cfg.get('smoke', False), 'sets': sorted(SETS),
            'eval_sets': content_fingerprint([paths.TARGET, paths.FRAGMENTS])}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


# Results of phases or eval sets no longer in the protocol are removed, so the
# tables can never mix them with current ones (trained models are kept).
results_root = paths.RESULTS / PHASES['baselines']
for d in sorted(results_root.glob('*')) if results_root.exists() else []:
    if d.is_dir() and d.name not in b['phases']:
        print(f'removing results of baseline phase {d.name!r} (not in baselines.phases)', flush=True)
        shutil.rmtree(d)
    elif d.is_dir():
        for s in sorted(d.glob('*/*')):
            if s.is_dir() and s.name not in SETS:
                print(f'removing {s.relative_to(paths.ROOT)} (not a baseline eval set)', flush=True)
                shutil.rmtree(s)

for phase in b['phases']:
    for name in selected(baselines.BASELINES):
        param, grid = next(iter(b['grid'][name].items()))
        cls = baselines.CLASSES[name]
        for seed in cfg['seeds']:
            print(f'\n== {name} ({phase}, seed {seed}) ==', flush=True)
            h, e = protocol_hash(name), eval_hash()
            chosen_file = model_dir(phase, name, seed, ROOT / phase) / 'chosen.json'
            done = result_dir('baselines', f'{phase}/{name}') / 'manifest.json'
            chosen = json.loads(chosen_file.read_text()) if chosen_file.exists() else {}
            if flag('PIPELINE_FORCE') or chosen.get('protocol_sha256') != h:
                chosen = select(name, 'baseline', None, phase, seed,
                                lambda fam, base, labels, s, tcfg, cls=cls: baselines.Bound(cls, labels, s),
                                grid=grid, epochs=b['max_epochs'], root=ROOT / phase, param=param)
                chosen['protocol_sha256'] = h
            elif chosen.get('eval_sha256') == e and done.exists():
                print('already trained and evaluated with this protocol and these eval sets, skipping', flush=True)
                continue
            else:
                print(f'already trained with this protocol ({param}={chosen["chosen"][param]}, '
                      f'epoch {chosen["chosen"]["epoch"]}); eval sets changed, re-evaluating', flush=True)
            best = model_dir(phase, name, seed, ROOT / phase) / 'best'
            model = baselines.load(name, best)
            evaluate(f'{phase}/{name}', 'baselines', model.predict,
                     metadata={'chosen': chosen['chosen'], 'hyperparameter': param, 'seed': seed}, sets=SETS)
            chosen['eval_sha256'] = e
            chosen_file.write_text(json.dumps(chosen, indent=2) + '\n', encoding='utf-8')
            del model
            gc.collect()

finalize_phase('baselines')
if ROOT.exists():
    write_manifest(ROOT, '05.traditional_baselines',
                   sorted(p for ph in b['phases'] for p in (ROOT / ph).rglob('*') if p.is_file()),
                   readonly=False)
