"""ConLID (EPFL), fine-tuned by data_pipeline stage 07.

The checkpoint is config.json, vocab.json, labels.json and model.safetensors
(an EmbeddingBag over words plus hashed character n-grams, then a linear head).
This is an inference-only numpy port of ConLIDWeights in
data_pipeline/new_method/lidlab/backends.py; keep the feature hashing below
identical to it.
"""

import json
import logging
import os
import re
from typing import List

from app.ml.fasttext_langid import FastTextLangIDClassifier
from app.ml.paths import finetuned

logger = logging.getLogger(__name__)

_SEPARATORS = re.compile(r"[\n\t\v\r\f\x00 ]+")


def _hash_ngram(s: str) -> int:
    """FNV-1a over SIGNED UTF-8 bytes, as in fastText."""
    h = 2166136261
    for b in s.encode("utf8"):
        h = ((h ^ ((b if b < 128 else b - 256) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


class ConLIDClassifier(FastTextLangIDClassifier):
    """Same output handling as the fastText backends; only loading and the
    forward pass differ. `model_path` is the checkpoint directory."""

    FILES = ("config.json", "vocab.json", "labels.json", "model.safetensors")

    @property
    def available(self) -> bool:
        if not all(os.path.isfile(os.path.join(self.model_path, f)) for f in self.FILES):
            return False
        try:
            import safetensors  # noqa: F401
        except ImportError:
            return False
        return True

    def _ensure_loaded(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not self.available:
                raise FileNotFoundError(
                    f"{self.display_name} checkpoint not found at {self.model_path}. "
                    "Run data_pipeline stage 07 or set CONLID_MODEL_PATH."
                )
            from safetensors.numpy import load_file

            logger.info("Loading %s from %s", self.display_name, self.model_path)
            read = lambda name: json.loads(
                open(os.path.join(self.model_path, name), encoding="utf8").read()
            )
            config, vocab, labels = read("config.json"), read("vocab.json"), read("labels.json")
            if config["aggr"] not in ("mean", "sum"):
                raise ValueError(f"Unsupported ConLID aggregation {config['aggr']!r}")
            if sorted(labels.values()) != list(range(len(labels))):
                raise ValueError("Noncontiguous ConLID label IDs")

            state = load_file(os.path.join(self.model_path, "model.safetensors"))
            self._embedding = state["embedding.weight"]
            self._fc_weight = state["fc.weight"]
            self._fc_bias = state["fc.bias"]
            self._config = config
            self._vocab = vocab
            self._labels = [label for label, _ in sorted(labels.items(), key=lambda x: x[1])]
            self._model = True
            logger.info("Loaded %s (%d labels)", self.display_name, len(self._labels))

    def _features(self, text: str) -> List[int]:
        cfg, vocab = self._config, self._vocab
        ids = []
        for word in _SEPARATORS.split(text):
            word = word.strip()
            if not word:
                continue
            if word in vocab:
                ids.append(vocab[word])
            if cfg["bucket"] > 0 and cfg["maxn"] > 0:
                padded = "<" + word + ">"
                for n in range(cfg["minn"], cfg["maxn"] + 1):
                    for start in range(len(padded) - n + 1):
                        ids.append(len(vocab) + _hash_ngram(padded[start:start + n]) % cfg["bucket"])
        skip = (cfg.get("pad_id", 0), cfg.get("unk_id", 1))
        return [i for i in ids if i not in skip]

    def _probabilities(self, text: str):
        import numpy as np

        ids = self._features(text)
        if not ids:
            return None
        rows = self._embedding[ids]
        hidden = rows.mean(axis=0) if self._config["aggr"] == "mean" else rows.sum(axis=0)
        logits = self._fc_weight @ hidden + self._fc_bias
        logits = logits - logits.max()
        exp = np.exp(logits)
        return exp / exp.sum()


conlid_classifier = ConLIDClassifier(
    os.environ.get("CONLID_MODEL_PATH") or finetuned("conlid"),
    "ConLID (fine-tuned)",
)
