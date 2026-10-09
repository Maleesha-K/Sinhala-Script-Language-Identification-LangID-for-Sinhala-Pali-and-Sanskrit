"""Evaluate every fine-tuned checkpoint chosen in stage 07 on the four eval sets
(same evaluator as zero-shot). Models without a checkpoint (e.g. deferred
XLM-R) are listed as pending, not scored."""
import gc
import json

from lidpipe import config
from lidpipe.evaluate import evaluate, finalize_phase
from lidpipe.models import load, selected
from lidpipe.training import model_dir

MODELS = ['nllb_lid218', 'glotlid_v3', 'openlid_v3', 'lid176', 'conlid', 'xlmr']
pending = []
for phase in ('target_only', 'rehearsal'):
    for name in selected(MODELS):
        for seed in config.pipeline()['seeds']:
            d = model_dir(phase, name, seed)
            if not (d / 'chosen.json').exists():
                pending.append(f'{name}/{phase}/seed{seed}')
                continue
            chosen = json.loads((d / 'chosen.json').read_text())
            print(f'\n== {name} {phase} seed {seed}: lr={chosen["chosen"]["lr"]} epoch={chosen["chosen"]["epoch"]} ==',
                  flush=True)
            model = load(name, d / 'best')
            evaluate(name if len(config.pipeline()['seeds']) == 1 else f'{name}/seed{seed}', phase, model.predict,
                     metadata={'chosen': chosen['chosen'], 'seed': seed, 'checkpoint': str(d / 'best')})
            del model
            gc.collect()
    finalize_phase(phase)
for p in pending:
    print('PENDING (no stage-07 checkpoint):', p)
