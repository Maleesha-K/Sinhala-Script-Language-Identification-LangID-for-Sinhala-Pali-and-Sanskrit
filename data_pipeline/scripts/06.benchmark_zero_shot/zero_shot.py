"""Zero-shot: every pretrained LID model, unchanged, on the four eval sets.

Predictions are unrestricted: a model may only output its own labels (e.g. the
XLM-R LID model has 20, without Sinhala, Pali, Sanskrit, Tamil or Bengali), and
rows of languages it cannot output count as errors.
"""
import gc

from lidpipe.evaluate import evaluate, finalize_phase
from lidpipe.models import PRETRAINED, REGISTRY, base_checkpoint, load, selected

for name in selected(PRETRAINED):
    print(f'\n== {name} (pinned pretrained checkpoint) ==', flush=True)
    model = load(name)
    evaluate(name, 'zero_shot', model.predict,
             metadata={'checkpoint': str(base_checkpoint(name)), 'family': REGISTRY[name][0],
                       'output_labels': len(model.labels)})
    del model
    gc.collect()

finalize_phase('zero_shot')
