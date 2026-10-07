"""Seven traditional baselines, trained from scratch on the same splits and
selected with the same rule as the fine-tuned models (lidpipe.training.select),
then evaluated on the same four eval sets (lidpipe.evaluate).

Results: datasets/benchmark_results/00_traditional_ml_baselines/<phase>/<model>/
Models:  models/00_traditional_ml_baselines/<phase>/<model>/seed<k>/
A target-only baseline only knows the 3 target labels, so its benchmark scores
measure nothing but Sinhala in FLORES/WiLI; the rehearsal baselines know all 11.

A (phase, model, seed) already trained and evaluated with the same protocol is
skipped, so a crashed run resumes where it stopped (--force retrains all).
"""
import gc
import hashlib
import json

from lidpipe import baselines, config, paths
from lidpipe.env import flag
from lidpipe.evaluate import evaluate, finalize_phase, result_dir
from lidpipe.manifest import sha256_file
from lidpipe.models import selected
from lidpipe.training import model_dir, select

cfg = config.pipeline()
b = cfg['baselines']
ROOT = paths.MODELS / '00_traditional_ml_baselines'


def protocol_hash(name):
    blob = {'baselines': {k: v for k, v in b.items() if k != 'grid'}, 'grid': b['grid'][name],
            'selection': cfg['training']['selection_metric'], 'smoke': cfg.get('smoke', False),
            'bootstrap': cfg['bootstrap'],
            'data': [sha256_file(p) for p in (paths.TARGET / 'manifest.json',
                                              paths.FINETUNE / 'replay_mixed' / 'manifest.json')]}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()

for phase in b['phases']:
    for name in selected(baselines.BASELINES):
        param, grid = next(iter(b['grid'][name].items()))
        cls = baselines.CLASSES[name]
        for seed in cfg['seeds']:
            print(f'\n== {name} ({phase}, seed {seed}) ==', flush=True)
            h = protocol_hash(name)
            chosen_file = model_dir(phase, name, seed, ROOT / phase) / 'chosen.json'
            done = result_dir('baselines', f'{phase}/{name}') / 'manifest.json'
            if (not flag('PIPELINE_FORCE') and chosen_file.exists() and done.exists()
                    and json.loads(chosen_file.read_text()).get('protocol_sha256') == h):
                print('already trained and evaluated with this protocol, skipping', flush=True)
                continue
            chosen = select(name, 'baseline', None, phase, seed,
                            lambda fam, base, labels, s, tcfg, cls=cls: baselines.Bound(cls, labels, s),
                            grid=grid, epochs=b['max_epochs'], root=ROOT / phase, param=param)
            best = model_dir(phase, name, seed, ROOT / phase) / 'best'
            model = baselines.load(name, best)
            evaluate(f'{phase}/{name}', 'baselines', model.predict,
                     metadata={'chosen': chosen['chosen'], 'hyperparameter': param, 'seed': seed})
            chosen['protocol_sha256'] = h
            chosen_file.write_text(json.dumps(chosen, indent=2) + '\n', encoding='utf-8')
            del model
            gc.collect()

finalize_phase('baselines')
if ROOT.exists():
    from lidpipe.manifest import write_manifest
    write_manifest(ROOT, '05.traditional_baselines',
                   sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'manifest.json'),
                   readonly=False)
