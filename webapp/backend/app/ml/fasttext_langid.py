"""fastText LID backends: the fine-tuned NLLB LID-218, GlotLID v3 and OpenLID v3.

These are the data_pipeline stage-07 rehearsal checkpoints (see app/ml/paths.py):
native fastText softmax models continued on the target and replay data, which
extend the pretrained label space with sin_Sinh / pli_Sinh / san_Sinh while
keeping every original label.

Predictions are unrestricted top-1 over the model's full label space, then
mapped onto the three categories the web app reports. A prediction outside the
three targets is surfaced as "other" rather than being silently forced into a
target class.
"""

import logging
import os
import threading
from typing import Dict, List

from app.ml.base import BaseClassifier
from app.ml.language_names import describe_code
from app.ml.paths import finetuned
from app.ml.text import normalise

logger = logging.getLogger(__name__)

# The web app reports these three; everything else in the label space is "other".
LABEL_MAP = {
    "sin_Sinh": "sinhala",
    "pli_Sinh": "pali",
    "san_Sinh": "sanskrit",
}
REPORTED = ("sinhala", "pali", "sanskrit")


class FastTextLangIDClassifier(BaseClassifier):
    """Wraps a fine-tuned fastText supervised checkpoint.

    The checkpoint is 1-1.7 GB, so it is loaded lazily on first use and held
    for the life of the process. Loading is guarded by a lock because Celery
    prefork workers can touch the same instance concurrently.
    """

    def __init__(self, model_path: str, display_name: str):
        self.model_path = model_path
        self.display_name = display_name
        self._model = None
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return os.path.exists(self.model_path)

    def _ensure_loaded(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"{self.display_name} checkpoint not found at {self.model_path}. "
                    "Run data_pipeline stage 07 or set the *_MODEL_PATH env var."
                )
            import fasttext
            import numpy as np

            logger.info("Loading %s from %s", self.display_name, self.model_path)
            model = fasttext.load_model(self.model_path)
            # fastText's Python predict() clamps its returned scores, so every
            # label can come back as ~1.0. Keep the output matrix and compute a
            # real softmax over the full label space instead.
            self._labels = [l.removeprefix("__label__") for l in model.get_labels()]
            self._output = np.asarray(model.get_output_matrix())
            self._model = model
            logger.info("Loaded %s (%d labels)", self.display_name, len(self._labels))

    def _probabilities(self, text: str):
        """True softmax over the model's full label space."""
        import numpy as np

        hidden = self._model.get_sentence_vector(text)
        logits = self._output @ hidden
        logits = logits - logits.max()
        exp = np.exp(logits)
        return exp / exp.sum()

    def predict(self, text: str) -> str:
        if not text or not text.strip():
            return "unknown"
        return self.predict_batch([text])[0]["language"]

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        if not texts:
            return []
        self._ensure_loaded()

        # The pipeline normalises every input; this also turns newlines, which
        # fastText treats as end-of-sentence, into spaces.
        cleaned = [normalise(t or "") for t in texts]

        results: List[Dict] = []
        for text in cleaned:
            # None: the model abstains (ConLID finds no features in the text).
            probs = self._probabilities(text) if text else None
            if probs is None:
                results.append(
                    {"language": "unknown", "confidence": 0.0,
                     "probabilities": {c: 0.0 for c in REPORTED}}
                )
                continue

            top_index = int(probs.argmax())
            top_code = self._labels[top_index]
            confidence = float(probs[top_index])
            top_language = LABEL_MAP.get(top_code, "other")

            # Always report the three target categories with their real mass.
            probabilities = {}
            for code, name in LABEL_MAP.items():
                try:
                    probabilities[name] = float(probs[self._labels.index(code)])
                except ValueError:
                    probabilities[name] = 0.0

            if top_language == "other":
                # Name the language the model actually detected, so the result
                # is informative rather than just "not one of the three".
                probabilities[describe_code(top_code)] = confidence

            results.append(
                {
                    "language": top_language,
                    "detected_code": top_code,
                    "detected_language": describe_code(top_code),
                    "confidence": confidence,
                    "probabilities": probabilities,
                }
            )

        return results


nllb_classifier = FastTextLangIDClassifier(
    os.environ.get("NLLB_MODEL_PATH") or finetuned("nllb_lid218", "model.bin"),
    "NLLB LID-218 (fine-tuned)",
)

glotlid_classifier = FastTextLangIDClassifier(
    os.environ.get("GLOTLID_MODEL_PATH") or finetuned("glotlid_v3", "model.bin"),
    "GlotLID v3 (fine-tuned)",
)

openlid_classifier = FastTextLangIDClassifier(
    os.environ.get("OPENLID_MODEL_PATH") or finetuned("openlid_v3", "model.bin"),
    "OpenLID v3 (fine-tuned)",
)
