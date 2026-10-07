"""Seven traditional baselines trained from scratch, behind the same trainer
interface as the fine-tuned models (epoch / predict / save / close), so the
shared selection loop (lidpipe.training.select) treats them identically.

Linear models use one feature extractor: hashed character n-grams (char_wb,
1-4) with TF-IDF weighting (config `baselines.features`). Hyperparameter grids
are in config `baselines.grid`. Models without epochs fit once (max_epochs=1).
"""
import json
import pickle
import tempfile
from pathlib import Path

import numpy as np

from . import config

BASELINES = ['nb', 'svm', 'logreg', 'xgboost', 'fasttext_scratch', 'char_cnn', 'char_bigru']


def _features(n_features=None):
    from sklearn.feature_extraction.text import HashingVectorizer
    f = config.pipeline()['baselines']['features']
    return HashingVectorizer(analyzer=f['analyzer'], ngram_range=tuple(f['ngram_range']),
                             n_features=n_features or f['n_features'], alternate_sign=False, norm=None,
                             dtype=np.float32)


class _Sklearn:
    max_epochs = 1

    def __init__(self, value, labels, seed, n_features=None):
        from sklearn.feature_extraction.text import TfidfTransformer
        self.value, self.seed, self.labels = value, seed, list(labels)
        self.hasher, self.tfidf = _features(n_features), TfidfTransformer(sublinear_tf=True)

    def _x(self, texts, fit=False):
        x = self.hasher.transform(texts)
        return self.tfidf.fit_transform(x) if fit else self.tfidf.transform(x)

    def epoch(self, rows, value, epoch):
        x = self._x([r['text'] for r in rows], fit=True)
        y = np.array([self.labels.index(r['label']) for r in rows])
        self.clf.fit(x, y)

    def predict(self, texts):
        x = self._x(list(texts))
        if hasattr(self.clf, 'predict_proba'):
            p = self.clf.predict_proba(x)
            idx, conf = p.argmax(1), p.max(1)
        else:
            d = self.clf.decision_function(x)
            idx, conf = d.argmax(1), d.max(1)
        return [self.labels[i] for i in idx], conf.tolist()

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / 'model.pkl', 'wb') as f:
            pickle.dump(self, f)

    def close(self):
        pass


class NB(_Sklearn):
    def __init__(self, value, labels, seed):
        from sklearn.naive_bayes import MultinomialNB
        super().__init__(value, labels, seed)
        self.clf = MultinomialNB(alpha=value)


class SVM(_Sklearn):
    def __init__(self, value, labels, seed):
        from sklearn.svm import LinearSVC
        super().__init__(value, labels, seed)
        self.clf = LinearSVC(C=value, random_state=seed)


class LogReg(_Sklearn):
    def __init__(self, value, labels, seed):
        from sklearn.linear_model import LogisticRegression
        from sklearn.multiclass import OneVsRestClassifier
        super().__init__(value, labels, seed)
        # One-vs-rest liblinear: the standard char n-gram LogReg LID baseline.
        self.clf = OneVsRestClassifier(LogisticRegression(C=value, solver='liblinear', random_state=seed),
                                       n_jobs=config.pipeline()['baselines']['n_jobs'])


class XGBoost(_Sklearn):
    def __init__(self, value, labels, seed):
        from xgboost import XGBClassifier
        x = config.pipeline()['baselines']['xgboost']
        super().__init__(value, labels, seed, n_features=x['n_features'])
        self.clf = XGBClassifier(learning_rate=value, n_estimators=x['n_estimators'], max_depth=x['max_depth'],
                                 tree_method='hist', max_bin=x['max_bin'], device='cpu', n_jobs=-1,  # threads share one copy
                                 random_state=seed)

    def predict(self, texts):
        p = self.clf.predict_proba(self._x(list(texts)))
        return [self.labels[i] for i in p.argmax(1)], p.max(1).tolist()


class FastTextScratch:
    """fastText trained from random initialisation (no pretrained vectors),
    LID-style settings: character 2-5-grams, softmax. Epoch e = a fresh model
    trained for e epochs, so selection over epochs is exact."""

    def __init__(self, value, labels, seed):
        self.lr, self.seed, self.labels = value, seed, list(labels)
        self.tmp = Path(tempfile.mkdtemp(prefix='ftscratch_'))
        self.model = None

    def epoch(self, rows, value, epoch):
        import fasttext
        from .models.fasttext_native import NativeModel
        data = self.tmp / 'train.txt'
        if not data.exists():
            data.write_text(''.join(f'__label__{r["label"]} {r["text"]}\n' for r in rows), encoding='utf-8')
        m = fasttext.train_supervised(str(data), lr=self.lr, epoch=epoch, dim=64, minn=2, maxn=5,
                                      wordNgrams=1, loss='softmax', thread=1, seed=self.seed, verbose=0)
        m.save_model(str(self.tmp / 'model.bin'))
        self.model = NativeModel(self.tmp / 'model.bin')

    def predict(self, texts):
        return self.model.predict(texts)

    def save(self, directory):
        import shutil
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.tmp / 'model.bin', directory / 'model.bin')

    def close(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)


class _CharNet:
    """Character-level neural classifiers (Char-CNN, Char-BiGRU) with Adam."""
    MAX_LEN = 200  # equals target_split.max_chars

    def __init__(self, value, labels, seed):
        import torch
        torch.manual_seed(seed)
        self.torch, self.lr, self.seed, self.labels = torch, value, seed, list(labels)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.vocab, self.net, self.opt = None, None, None

    def _ids(self, texts):
        torch = self.torch
        out = torch.zeros(len(texts), self.MAX_LEN, dtype=torch.long)
        for i, t in enumerate(texts):
            ids = [self.vocab.get(c, 1) for c in t[:self.MAX_LEN]]
            out[i, :len(ids)] = torch.tensor(ids)
        return out

    def epoch(self, rows, value, epoch):
        torch = self.torch
        if self.net is None:
            from collections import Counter
            counts = Counter(c for r in rows for c in r['text'])
            self.vocab = {c: i + 2 for i, (c, n) in enumerate(counts.most_common()) if n >= 2}  # 0 pad, 1 unk
            self.net = self.build(len(self.vocab) + 2, len(self.labels)).to(self.device)
            self.opt = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        y_all = torch.tensor([self.labels.index(r['label']) for r in rows])
        order = np.random.default_rng(self.seed + epoch).permutation(len(rows))
        self.net.train()
        for start in range(0, len(order), 256):
            idx = order[start:start + 256]
            x = self._ids([rows[i]['text'] for i in idx]).to(self.device)
            loss = torch.nn.functional.cross_entropy(self.net(x), y_all[idx].to(self.device))
            self.opt.zero_grad(set_to_none=True)
            loss.backward()
            self.opt.step()

    def predict(self, texts):
        torch = self.torch
        self.net.eval()
        labels, conf = [], []
        texts = list(texts)
        with torch.inference_mode():
            for start in range(0, len(texts), 1024):
                p = self.net(self._ids(texts[start:start + 1024]).to(self.device)).softmax(-1)
                c, i = p.max(-1)
                labels += [self.labels[j] for j in i.cpu().tolist()]
                conf += c.cpu().tolist()
        return labels, conf

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.torch.save(self.net.state_dict(), directory / 'model.pt')
        (directory / 'meta.json').write_text(json.dumps({'class': type(self).__name__, 'lr': self.lr,
                                                         'labels': self.labels, 'vocab': self.vocab},
                                                        ensure_ascii=False), encoding='utf-8')

    def close(self):
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()


class CharCNN(_CharNet):
    def build(self, vocab, classes):
        nn = self.torch.nn
        torch = self.torch

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(vocab, 64, padding_idx=0)
                self.convs = nn.ModuleList(nn.Conv1d(64, 128, k) for k in (3, 4, 5))
                self.drop, self.out = nn.Dropout(0.3), nn.Linear(3 * 128, classes)

            def forward(self, x):
                h = self.emb(x).transpose(1, 2)
                return self.out(self.drop(torch.cat([c(h).relu().amax(2) for c in self.convs], 1)))
        return Net()


class CharBiGRU(_CharNet):
    def build(self, vocab, classes):
        nn = self.torch.nn
        torch = self.torch

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(vocab, 64, padding_idx=0)
                self.gru = nn.GRU(64, 128, batch_first=True, bidirectional=True)
                self.drop, self.out = nn.Dropout(0.3), nn.Linear(2 * 2 * 128, classes)

            def forward(self, x):
                mask = (x != 0).unsqueeze(-1).float()
                h, _ = self.gru(self.emb(x))
                mean = (h * mask).sum(1) / mask.sum(1).clamp(min=1)
                mx = h.masked_fill(mask == 0, -1e4).amax(1)
                return self.out(self.drop(torch.cat([mean, mx], 1)))
        return Net()


CLASSES = {'nb': NB, 'svm': SVM, 'logreg': LogReg, 'xgboost': XGBoost, 'fasttext_scratch': FastTextScratch,
           'char_cnn': CharCNN, 'char_bigru': CharBiGRU}


def load(model, directory):
    """Reload a saved baseline for evaluation."""
    directory = Path(directory)
    if (directory / 'model.pkl').exists():
        with open(directory / 'model.pkl', 'rb') as f:
            return pickle.load(f)
    if model == 'fasttext_scratch':
        from .models.fasttext_native import NativeModel
        return NativeModel(directory / 'model.bin')
    meta = json.loads((directory / 'meta.json').read_text(encoding='utf-8'))
    net = CLASSES[model](meta['lr'], meta['labels'], 0)
    net.vocab = meta['vocab']
    net.net = net.build(len(net.vocab) + 2, len(net.labels)).to(net.device)
    net.net.load_state_dict(net.torch.load(directory / 'model.pt', map_location=net.device, weights_only=True))
    return net


class Bound:
    """Adapts a baseline class to lidpipe.training.select: the grid value
    arrives with the first epoch() call, so the model is built then."""

    def __init__(self, cls, labels, seed):
        self.cls, self.labels, self.seed, self.inner = cls, list(labels), seed, None
        self.max_epochs = getattr(cls, 'max_epochs', 10 ** 9)

    def epoch(self, rows, value, epoch):
        if self.inner is None:
            self.inner = self.cls(value, self.labels, self.seed)
        self.inner.epoch(rows, value, epoch)

    def predict(self, texts):
        return self.inner.predict(texts)

    def save(self, directory):
        self.inner.save(directory)

    def close(self):
        if self.inner is not None:
            self.inner.close()
