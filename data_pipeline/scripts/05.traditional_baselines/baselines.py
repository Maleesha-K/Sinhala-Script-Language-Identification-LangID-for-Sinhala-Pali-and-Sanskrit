"""Seven traditional baselines, trained from scratch on the same splits and
selected with the same rule as the fine-tuned models (lidpipe.training.select),
then evaluated on the same four eval sets (lidpipe.evaluate).

Results: datasets/benchmark_results/00_traditional_ml_baselines/<phase>/<model>/
Models:  models/00_traditional_ml_baselines/<phase>/<model>/seed<k>/
A target-only baseline only knows the 3 target labels, so its benchmark scores
measure nothing but Sinhala in FLORES/WiLI; the rehearsal baselines know all 11.
"""
import gc

from lidpipe import baselines, config, paths
from lidpipe.evaluate import evaluate, finalize_phase
from lidpipe.models import selected
from lidpipe.training import model_dir, select

cfg = config.pipeline()
b = cfg['baselines']
ROOT = paths.MODELS / '00_traditional_ml_baselines'

for phase in b['phases']:
    for name in selected(baselines.BASELINES):
        param, grid = next(iter(b['grid'][name].items()))
        cls = baselines.CLASSES[name]
        for seed in cfg['seeds']:
            print(f'\n== {name} ({phase}, seed {seed}) ==', flush=True)
            chosen = select(name, 'baseline', None, phase, seed,
                            lambda fam, base, labels, s, tcfg, cls=cls: baselines.Bound(cls, labels, s),
                            grid=grid, epochs=b['max_epochs'], root=ROOT / phase, param=param)
            best = model_dir(phase, name, seed, ROOT / phase) / 'best'
            model = baselines.load(name, best)
            evaluate(f'{phase}/{name}', 'baselines', model.predict,
                     metadata={'chosen': chosen['chosen'], 'hyperparameter': param, 'seed': seed})
            del model
            gc.collect()

finalize_phase('baselines')
if ROOT.exists():
    from lidpipe.manifest import write_manifest
    write_manifest(ROOT, '05.traditional_baselines',
                   sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'manifest.json'),
                   readonly=False)
