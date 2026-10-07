"""Inference for the XLM-R LID model (pretrained or fine-tuned: pretrained model
+ extended head + LoRA adapter) and for fine-tuned LID-176 (fasttext_continual)."""
import json
from pathlib import Path

from .. import config
from ..device import torch_device


def extend_head(model, new_labels):
    """Append zero-initialised output rows for `new_labels` to an XLM-R
    sequence-classification head, keeping every original row unchanged."""
    import torch
    if not new_labels:
        return model
    old = model.classifier.out_proj
    head = torch.nn.Linear(old.in_features, old.out_features + len(new_labels))
    with torch.no_grad():
        head.weight.zero_()
        head.bias.zero_()
        head.weight[:old.out_features].copy_(old.weight)
        head.bias[:old.out_features].copy_(old.bias)
    model.classifier.out_proj = head
    labels = [model.config.id2label[i] for i in range(old.out_features)] + list(new_labels)
    model.config.id2label = dict(enumerate(labels))
    model.config.label2id = {l: i for i, l in enumerate(labels)}
    model.config.num_labels = model.num_labels = len(labels)
    return model


class XLMR:
    """The pretrained XLM-R LID model (zero-shot) or a stage-07 checkpoint
    (pretrained model + extended head + LoRA adapter)."""

    def __init__(self, path):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        path = Path(path)
        self.torch = torch
        self.device = torch_device()
        self.max_length = config.pipeline()['training']['xlmr']['max_length']
        self.tok = AutoTokenizer.from_pretrained(path)
        meta_file = path / 'lidpipe_labels.json'
        if meta_file.exists():  # fine-tuned
            from peft import PeftModel
            meta = json.loads(meta_file.read_text(encoding='utf-8'))
            base = AutoModelForSequenceClassification.from_pretrained(meta['base'])
            extend_head(base, meta['labels'][base.config.num_labels:])
            model = PeftModel.from_pretrained(base, path)
        else:  # pretrained LID model
            model = AutoModelForSequenceClassification.from_pretrained(path)
        self.model = model.to(self.device).eval()
        cfg = self.model.config
        self.labels = [cfg.id2label[i] for i in range(cfg.num_labels)]

    def predict(self, texts, batch_size=128):
        torch = self.torch
        labels, conf = [], []
        texts = list(texts)
        with torch.inference_mode(), torch.autocast(self.device, dtype=torch.float16,
                                                    enabled=self.device == 'cuda'):
            for start in range(0, len(texts), batch_size):
                enc = self.tok(texts[start:start + batch_size], truncation=True, max_length=self.max_length,
                               padding=True, return_tensors='pt')
                p = self.model(**{k: v.to(self.device) for k, v in enc.items()}).logits.float().softmax(-1)
                c, i = p.max(-1)
                labels += [self.labels[j] for j in i.cpu().tolist()]
                conf += c.cpu().tolist()
        return labels, conf


class LID176Continual:
    def __init__(self, path):
        from fasttext_continual.model import ContinualLID
        self.model = ContinualLID.from_pretrained(path, device=torch_device())
        self.labels = list(self.model.labels)

    def predict(self, texts):
        labels, scores = self.model.predict(list(texts), batch_size=512)
        return [l[0] for l in labels], [s[0] for s in scores]
