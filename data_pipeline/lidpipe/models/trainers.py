"""Per-family training, behind one interface used by lidpipe.training:

    t = TRAINERS[family](base_path, label_set, seed, cfg)
    t.epoch(rows, lr, epoch)      # one pass over rows (dicts: text, label)
    t.predict(texts) -> raw labels, confidences
    t.save(directory)             # checkpoint loadable by lidpipe.models.load
    t.close()

Labels in `rows` are canonical (`sin_Sinh`, ...). Each trainer maps them to the
label the base model already uses for that language (lidpipe.labels.
model_label_map), so no language gets two competing outputs.
"""
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from ..device import torch_device
from ..labels import model_label_map


class FastTextSoftmax:
    """NLLB-218, GlotLID-v3, OpenLID-v3: native continued training of the full
    model (embeddings + output layer); new labels get zero-initialised rows."""

    def __init__(self, base_path, label_set, seed, cfg):
        from .fasttext_native import NativeModel
        self.tmp = Path(tempfile.mkdtemp(prefix='ft_'))
        base = NativeModel(base_path)
        self.map = model_label_map(base.labels)
        self.seed = seed
        self.model = base.continue_training([], self.tmp / 'init.bin', 0.05, seed,
                                            add_labels=[self.map[l] for l in label_set])

    def epoch(self, rows, lr, epoch):
        mapped = [{'text': r['text'], 'label': self.map[r['label']]} for r in rows]
        old = self.model.path
        self.model = self.model.continue_training(mapped, self.tmp / f'epoch{epoch}.bin', lr, self.seed + epoch)
        if old.parent == self.tmp:
            old.unlink()

    def predict(self, texts):
        return self.model.predict(texts)

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.model.path, directory / 'model.bin')

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class ConLIDTrainer:
    """ConLID: supervised cross-entropy over the full output space with sparse
    SGD (lidlab.backends.ConLIDBackend.train); new labels get zero rows."""

    def __init__(self, base_path, label_set, seed, cfg):
        from .conlid import ConLID
        self.tmp = Path(tempfile.mkdtemp(prefix='conlid_'))
        self.wrapper = ConLID(base_path)
        self.map = model_label_map(self.wrapper.labels)
        self.seed, self.batch = seed, cfg['batch_size']['conlid']
        self.device = self.wrapper.backend.device
        self.wrapper.backend.initialize([self.map[l] for l in label_set], self.tmp)
        self.wrapper.labels = list(self.wrapper.backend.labels)

    def epoch(self, rows, lr, epoch):
        import pandas as pd
        df = pd.DataFrame({'text': [r['text'] for r in rows], 'label': [self.map[r['label']] for r in rows]})
        self.wrapper.backend.train(df, self.tmp, lr, len(df), self.seed + epoch, self.batch)

    def predict(self, texts):
        return self.wrapper.predict(texts)

    def save(self, directory):
        self.wrapper.backend.save(directory)
        self.wrapper.backend.path = self.tmp  # keep training in the scratch dir

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class LID176Trainer:
    """LID-176 (hierarchical softmax): fasttext_continual imports the official
    checkpoint with verified parity, adds a Pali leaf under Sinhala (no other
    leaf moves), then trains all parameters with constant-rate SGD.
    Script-less outputs (`sa`) get their script from the text when scored."""

    def __init__(self, base_path, label_set, seed, cfg):
        import torch
        from fasttext_continual.model import ContinualLID
        from fasttext_continual.verify import PROBES, check_import
        torch.manual_seed(seed)
        self.torch = torch
        model, native = ContinualLID.from_fasttext(base_path)
        report = check_import(model, native, PROBES)
        del native
        model.config['parity_verified'] = True
        model.config['parity_report'] = report
        model.add_pali()
        self.device = torch_device()
        self.model = model.to(self.device)
        self.map = model_label_map(self.model.labels)
        self.seed, self.batch = seed, cfg['batch_size']['fasttext_hs']
        self.encoded = None

    def epoch(self, rows, lr, epoch):
        from fasttext_continual.model import pack_features
        torch = self.torch
        if self.encoded is None or len(self.encoded[0]) != len(rows):
            self.encoded = ([np.asarray(self.model.encoder.encode(r['text']), dtype=np.int64) for r in rows],
                            np.array([self.model.label_to_id[self.map[r['label']]] for r in rows]))
        feats, targets = self.encoded
        opt = torch.optim.SGD(self.model.parameters(), lr=lr)
        order = np.random.default_rng(self.seed + epoch).permutation(len(feats))
        self.model.train()
        for start in range(0, len(order), self.batch):
            idx = order[start:start + self.batch]
            ids, offsets = pack_features([feats[i] for i in idx], self.device)
            y = torch.as_tensor(targets[idx], device=self.device)
            opt.zero_grad(set_to_none=True)
            loss = self.model.nll(ids, offsets, y).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError('non-finite LID-176 loss')
            loss.backward()
            opt.step()

    def predict(self, texts):
        labels, scores = self.model.predict(list(texts), batch_size=512)
        return [l[0] for l in labels], [s[0] for s in scores]

    def save(self, directory):
        self.model.save_pretrained(directory)

    def close(self):
        del self.model
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


class XLMRTrainer:
    """XLM-R language-identification model (papluca/xlm-roberta-base-language-
    detection, 20 labels). Like every other pretrained LID model, its head is
    extended: the 20 original rows are kept, missing labels are appended with
    zero rows, and predictions stay unrestricted over all outputs. LoRA adapters
    on attention + the (extended) head are trained with AdamW and linear decay
    over the whole epoch budget; max_length is the same in training and inference."""

    def __init__(self, base_path, label_set, seed, cfg):
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from .xlmr import extend_head
        torch.manual_seed(seed)
        self.torch, self.cfg = torch, cfg
        self.device = torch_device()
        self.tok = AutoTokenizer.from_pretrained(base_path)
        model = AutoModelForSequenceClassification.from_pretrained(base_path)
        original = [model.config.id2label[i] for i in range(model.config.num_labels)]
        self.map = model_label_map(original)
        extend_head(model, [self.map[l] for l in label_set if self.map[l] not in original])
        self.labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
        self.lookup = {l: i for i, l in enumerate(self.labels)}
        x = cfg['xlmr']
        lora = LoraConfig(task_type=TaskType.SEQ_CLS, r=x['lora_r'], lora_alpha=x['lora_alpha'],
                          lora_dropout=x['lora_dropout'], target_modules=['query', 'value'],
                          modules_to_save=['classifier'])
        self.model = get_peft_model(model, lora).to(self.device)
        self.base_path, self.seed, self.batch = str(base_path), seed, cfg['batch_size']['xlmr']
        self.opt = self.sched = None

    def _encode(self, texts):
        enc = self.tok(texts, truncation=True, max_length=self.cfg['xlmr']['max_length'],
                       padding=True, return_tensors='pt')
        return {k: v.to(self.device) for k, v in enc.items()}

    def epoch(self, rows, lr, epoch):
        torch = self.torch
        from transformers import get_linear_schedule_with_warmup
        steps = -(-len(rows) // self.batch)
        if self.opt is None:
            self.opt = torch.optim.AdamW([p for p in self.model.parameters() if p.requires_grad], lr=lr)
            total = steps * self.cfg['max_epochs']
            self.sched = get_linear_schedule_with_warmup(self.opt, int(0.06 * total), total)
        order = np.random.default_rng(self.seed + epoch).permutation(len(rows))
        texts = [rows[i]['text'] for i in order]
        y_all = torch.tensor([self.lookup[self.map[rows[i]['label']]] for i in order])
        scaler = torch.amp.GradScaler(enabled=self.device == 'cuda')
        self.model.train()
        for start in range(0, len(texts), self.batch):
            enc = self._encode(texts[start:start + self.batch])
            y = y_all[start:start + self.batch].to(self.device)
            with torch.autocast(self.device, dtype=torch.float16, enabled=self.device == 'cuda'):
                loss = torch.nn.functional.cross_entropy(self.model(**enc).logits.float(), y)
            self.opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(self.opt)
            scaler.update()
            self.sched.step()

    def predict(self, texts):
        torch = self.torch
        self.model.eval()
        labels, conf = [], []
        texts = list(texts)
        with torch.inference_mode(), torch.autocast(self.device, dtype=torch.float16,
                                                    enabled=self.device == 'cuda'):
            for start in range(0, len(texts), self.batch * 4):
                p = self.model(**self._encode(texts[start:start + self.batch * 4])).logits.float().softmax(-1)
                c, i = p.max(-1)
                labels += [self.labels[j] for j in i.cpu().tolist()]
                conf += c.cpu().tolist()
        return labels, conf

    def save(self, directory):
        directory = Path(directory)
        self.model.save_pretrained(directory)
        self.tok.save_pretrained(directory)
        (directory / 'lidpipe_labels.json').write_text(json.dumps({'labels': self.labels,
                                                                   'base': self.base_path}), encoding='utf-8')

    def close(self):
        del self.model
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


TRAINERS = {'fasttext_softmax': FastTextSoftmax, 'conlid': ConLIDTrainer,
            'fasttext_hs': LID176Trainer, 'xlmr': XLMRTrainer}
