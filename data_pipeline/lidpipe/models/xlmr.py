"""Inference for fine-tuned XLM-RoBERTa (base + LoRA adapter + head) and for
fine-tuned LID-176 (fasttext_continual checkpoint)."""
import json
from pathlib import Path

from .. import config
from ..device import torch_device


class XLMR:
    def __init__(self, path):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        path = Path(path)
        meta_file = path / 'lidpipe_labels.json'
        if not meta_file.exists():
            raise SystemExit('XLM-R has no language-identification head before fine-tuning; '
                             'only stage-07 checkpoints can be evaluated')
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
        self.labels = meta['labels']
        self.torch = torch
        self.device = torch_device()
        self.max_length = config.pipeline()['training']['xlmr']['max_length']
        self.tok = AutoTokenizer.from_pretrained(path)
        base = AutoModelForSequenceClassification.from_pretrained(
            meta['base'], num_labels=len(self.labels), id2label=dict(enumerate(self.labels)),
            label2id={l: i for i, l in enumerate(self.labels)})
        self.model = PeftModel.from_pretrained(base, path).to(self.device).eval()

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
