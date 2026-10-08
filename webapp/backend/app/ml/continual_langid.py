"""fastText LID-176 continued with hierarchical-softmax leaf surgery.

Checkpoint: the data_pipeline stage-07 rehearsal checkpoint (see app/ml/paths.py),
produced with data_pipeline/fasttext_continual. LID176_MODEL_PATH may instead
name a Hugging Face repo id. It is NOT a native fastText .bin:
it ships config.json (labels plus explicit Huffman paths), vocab.json and
weights.pt, so the `fasttext` package cannot load it.

This module is an inference-only port of data_pipeline/fasttext_continual
(features.py and ContinualLID.predict). The training code there is the source
of truth; keep the feature hashing below byte-for-byte identical to it.

Labels are LID-176's ISO-639-1 codes plus the surgically added 'pi' (Pali).
LID-176 has a single 'sa' label covering Sanskrit in every script, so the
script of the text decides whether it is the Sinhala-script Sanskrit the web
app reports or Devanagari Sanskrit ("other"), matching the other models.
"""

import json
import logging
import os
import re
import threading
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from app.ml.base import BaseClassifier
from app.ml.paths import finetuned
from app.ml.text import normalise

logger = logging.getLogger(__name__)

FORMAT_VERSION = 1

LABEL_MAP = {"si": "sinhala", "pi": "pali", "sa": "sanskrit"}
REPORTED = ("sinhala", "pali", "sanskrit")

# Names for the labels a user is likely to meet; the rest fall back to the code.
# These match FASTTEXT_EXTRA_LANGUAGES in the registry so corrections line up.
ISO2_NAMES = {
    "en": "English", "ta": "Tamil", "hi": "Hindi", "bn": "Bengali",
    "ar": "Arabic", "fr": "French", "de": "German", "ne": "Nepali",
    "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi", "te": "Telugu",
    "kn": "Kannada", "ml": "Malayalam", "or": "Odia", "ur": "Urdu",
    "dv": "Dhivehi", "my": "Burmese", "th": "Thai", "bo": "Tibetan",
    "es": "Spanish", "pt": "Portuguese", "it": "Italian", "nl": "Dutch",
    "ru": "Russian", "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "fa": "Persian", "id": "Indonesian", "la": "Latin",
}
SANSKRIT_DEVANAGARI = "Sanskrit (Devanagari)"

SINHALA_CHARS = re.compile(r"[඀-෿]")
DEVANAGARI_CHARS = re.compile(r"[ऀ-ॿ]")

# --- Feature IDs (port of data_pipeline/fasttext_continual/features.py) -----

ASCII_SEPARATORS = re.compile(r"[ \t\r\v\f\x00]+")
EOS = "</s>"


def _tokens(text: str):
    # fastText.predict appends a newline, which creates an EOS token. The
    # literal EOS also terminates a line. Non-ASCII whitespace is NOT split.
    for token in ASCII_SEPARATORS.split(text):
        if not token:
            continue
        yield token
        if token == EOS:
            return
    yield EOS


def _fasttext_hash(data: bytes) -> int:
    """FNV-1a with fastText's historical SIGNED UTF-8 bytes."""
    h = 2166136261
    for byte in data:
        signed = byte if byte < 128 else byte - 256
        h = ((h ^ (signed & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


class _FeatureEncoder:
    def __init__(self, words: List[str], args: dict):
        if args["wordNgrams"] != 1:
            raise ValueError("Only wordNgrams=1 checkpoints are supported")
        self.word_to_id = {word: i for i, word in enumerate(words)}
        self.nwords = len(words)
        self.args = dict(args)
        self.word_ids = lru_cache(maxsize=32768)(self._word_ids)

    def _word_ids(self, word: str):
        if word.startswith(self.args["label"]):
            return ()
        ids = []
        wid = self.word_to_id.get(word)
        if wid is not None:
            ids.append(wid)
        if word == EOS or self.args["maxn"] <= 0:
            return tuple(ids)
        wrapped = "<" + word + ">"
        for i in range(len(wrapped)):
            for n in range(1, self.args["maxn"] + 1):
                j = i + n
                if j > len(wrapped):
                    break
                if n < self.args["minn"]:
                    continue
                if n == 1 and (i == 0 or j == len(wrapped)):
                    continue
                h = _fasttext_hash(wrapped[i:j].encode("utf-8"))
                ids.append(self.nwords + h % self.args["bucket"])
        return tuple(ids)

    def encode(self, text: str) -> List[int]:
        ids: List[int] = []
        for word in _tokens(text.replace("\n", " ")):
            ids.extend(self.word_ids(word))
        return ids


# --- Classifier -------------------------------------------------------------


class ContinualLIDClassifier(BaseClassifier):
    """Loads the checkpoint from a local directory or the Hugging Face Hub.

    The input matrix is ~130 MB, so it is loaded lazily on first use and held
    for the life of the process, guarded by a lock like the fastText backends.
    """

    def __init__(self, source: str, display_name: str):
        self.source = source
        self.display_name = display_name
        self._loaded = False
        self._lock = threading.Lock()

    @property
    def _is_local(self) -> bool:
        return os.path.isabs(self.source) or self.source.startswith(".")

    @property
    def available(self) -> bool:
        try:
            import torch  # noqa: F401
        except ImportError:
            return False
        if self._is_local:
            return os.path.isfile(os.path.join(self.source, "weights.pt"))
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            return False
        return True

    def _resolve_directory(self) -> Path:
        if self._is_local:
            return Path(self.source)
        from huggingface_hub import snapshot_download

        # Cached under HF_HOME after the first download.
        return Path(snapshot_download(
            repo_id=self.source,
            allow_patterns=["config.json", "vocab.json", "weights.pt"],
        ))

    def _ensure_loaded(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            import numpy as np
            import torch

            directory = self._resolve_directory()
            logger.info("Loading %s from %s", self.display_name, directory)
            config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
            if config.get("format_version") != FORMAT_VERSION:
                raise ValueError(f"Unsupported {self.display_name} checkpoint format")
            words = json.loads((directory / "vocab.json").read_text(encoding="utf-8"))
            state = torch.load(directory / "weights.pt", map_location="cpu", weights_only=True)

            args = config["args"]
            self._input = state["input"].numpy()
            self._output = state["output"].numpy()
            if self._input.shape != (len(words) + args["bucket"], args["dim"]):
                raise ValueError("Input matrix and vocabulary/settings do not match")

            self._encoder = _FeatureEncoder(words, args)
            self._labels = list(config["labels"])

            # Root-to-leaf decision rows and branch bits for every label.
            paths, codes = config["paths"], config["codes"]
            width = max(map(len, paths))
            self._path_rows = np.zeros((len(paths), width), dtype=np.int64)
            self._path_signs = np.zeros((len(paths), width), dtype=np.float32)
            self._path_mask = np.zeros((len(paths), width), dtype=bool)
            for i, (path, code) in enumerate(zip(paths, codes)):
                self._path_rows[i, :len(path)] = path[::-1]
                self._path_signs[i, :len(code)] = [2 * c - 1 for c in code[::-1]]
                self._path_mask[i, :len(path)] = True

            self._loaded = True
            logger.info("Loaded %s (%d labels)", self.display_name, len(self._labels))

    def _probabilities(self, text: str):
        """Normalized hierarchical-softmax probability of every leaf."""
        import numpy as np

        ids = self._encoder.encode(text)
        hidden = self._input[ids].mean(axis=0)
        logits = self._output @ hidden
        signed = logits[self._path_rows] * self._path_signs
        # log(sigmoid(x)) = -log(1 + exp(-x)), summed along each leaf's path.
        log_probs = np.where(self._path_mask, -np.logaddexp(0.0, -signed), 0.0).sum(axis=1)
        return np.exp(log_probs)

    def predict(self, text: str) -> str:
        if not text or not text.strip():
            return "unknown"
        return self.predict_batch([text])[0]["language"]

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        if not texts:
            return []
        self._ensure_loaded()

        results: List[Dict] = []
        for raw in texts:
            text = normalise(raw or "")
            if not text:
                results.append(
                    {"language": "unknown", "confidence": 0.0,
                     "probabilities": {c: 0.0 for c in REPORTED}}
                )
                continue

            probs = self._probabilities(text)
            top_index = int(probs.argmax())
            top_code = self._labels[top_index]
            confidence = float(probs[top_index])
            top_language = LABEL_MAP.get(top_code, "other")
            detected_language = ISO2_NAMES.get(top_code, top_code)

            devanagari = False
            if top_code == "sa":
                devanagari = (
                    len(DEVANAGARI_CHARS.findall(text)) > len(SINHALA_CHARS.findall(text))
                )
                if devanagari:
                    top_language = "other"
                    detected_language = SANSKRIT_DEVANAGARI
                else:
                    detected_language = "Sanskrit"
            elif top_language != "other":
                detected_language = top_language.capitalize()

            probabilities = {}
            for code, name in LABEL_MAP.items():
                try:
                    value = float(probs[self._labels.index(code)])
                except ValueError:
                    value = 0.0
                # Devanagari Sanskrit mass is not the Sinhala-script category.
                probabilities[name] = 0.0 if (code == "sa" and devanagari) else value

            if top_language == "other":
                probabilities[detected_language] = confidence

            results.append(
                {
                    "language": top_language,
                    "detected_code": top_code,
                    "detected_language": detected_language,
                    "confidence": confidence,
                    "probabilities": probabilities,
                }
            )

        return results


lid176_classifier = ContinualLIDClassifier(
    os.environ.get("LID176_MODEL_PATH") or finetuned("lid176"),
    "fastText LID-176 (leaf surgery)",
)
