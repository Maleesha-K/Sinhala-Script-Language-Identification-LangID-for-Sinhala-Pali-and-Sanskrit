"""Seven traditional baselines, trained from scratch on the same splits and
selected with the same rule as the fine-tuned models (lidpipe.training.select),
then evaluated on the same four eval sets (lidpipe.evaluate).

Results: datasets/benchmark_results/00_traditional_ml_baselines/<phase>/<model>/
Models:  models/00_traditional_ml_baselines/<phase>/<model>/seed<k>/
A target-only baseline only knows the 3 target labels, so on the hybrid
benchmarks it can only get the target test rows right; the rehearsal baselines
know all 11.

A (phase, model, seed) already trained with the same protocol is not retrained,
and is re-evaluated only when the eval sets changed, so a crashed run resumes
where it stopped (--force retrains all).
"""
import gc
import hashlib
import json

from lidpipe import baselines, config, paths
from lidpipe.env import flag
from lidpipe.evaluate import evaluate, finalize_phase, result_dir
from lidpipe.manifest import content_fingerprint
from lidpipe.models import selected
from lidpipe.training import model_dir, select

cfg = config.pipeline()
b = cfg['baselines']
ROOT = paths.MODELS / '00_traditional_ml_baselines'


def protocol_hash(name):
    blob = {'baselines': {k: v for k, v in b.items() if k != 'grid'}, 'grid': b['grid'][name],
            'selection': cfg['training']['selection_metric'], 'smoke': cfg.get('smoke', False),
            'data': content_fingerprint([paths.TARGET, paths.FINETUNE / 'replay_mixed'])}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def eval_hash():
    """Everything evaluation depends on: the eval sets and the bootstrap settings."""
    blob = {'bootstrap': cfg['bootstrap'], 'smoke': cfg.get('smoke', False),
            'eval_sets': content_fingerprint([paths.TARGET] + [paths.benchmark_dir(n) for n in paths.BENCHMARK_NAMES])}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


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
                     metadata={'chosen': chosen['chosen'], 'hyperparameter': param, 'seed': seed})
            chosen['eval_sha256'] = e
            chosen_file.write_text(json.dumps(chosen, indent=2) + '\n', encoding='utf-8')
            del model
            gc.collect()

finalize_phase('baselines')
if ROOT.exists():
    from lidpipe.manifest import write_manifest
    write_manifest(ROOT, '05.traditional_baselines',
                   sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'manifest.json'),
                   readonly=False)
