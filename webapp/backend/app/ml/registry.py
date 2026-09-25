"""Registry of selectable classification models.

`model_name` is persisted on ClassificationJob and used by credit_service to
look up billing rates, so the ids here are stable identifiers, not labels.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List

from app.ml.base import BaseClassifier

BASELINE_MODEL = "sklearn_langid"

# The three categories every model reports.
TARGET_LANGUAGES = ["sinhala", "pali", "sanskrit"]

# The fine-tuned checkpoints keep their original label space, so a correction
# can name any of the replay languages too. These are the eight the models were
# rehearsed on (data_pipeline/new_method/lidlab/data.py REPLAY), which are the
# realistic corrections for non-target text.
FASTTEXT_EXTRA_LANGUAGES = [
    "Sanskrit (Devanagari)", "English", "Tamil", "Hindi",
    "Bengali", "Arabic", "French", "German",
]


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    description: str
    family: str
    is_baseline: bool
    loader: Callable[[], BaseClassifier]

    @property
    def correction_languages(self) -> List[str]:
        """Languages a user may pick when correcting this model's output.

        The baseline is a three-way classifier trained only on the targets, so
        offering it other languages would record labels it can never predict.
        """
        if self.is_baseline:
            return list(TARGET_LANGUAGES)
        return TARGET_LANGUAGES + FASTTEXT_EXTRA_LANGUAGES

    def available(self) -> bool:
        try:
            classifier = self.loader()
        except Exception:
            return False
        return getattr(classifier, "available", True)


def _load_sklearn() -> BaseClassifier:
    from app.ml.sklearn_langid import langid_classifier
    return langid_classifier


def _load_nllb() -> BaseClassifier:
    from app.ml.fasttext_langid import nllb_classifier
    return nllb_classifier


def _load_glotlid() -> BaseClassifier:
    from app.ml.fasttext_langid import glotlid_classifier
    return glotlid_classifier


MODELS: Dict[str, ModelInfo] = {
    BASELINE_MODEL: ModelInfo(
        id=BASELINE_MODEL,
        label="Baseline (TF-IDF)",
        description="Original scikit-learn character n-gram classifier. Fast, three-way output.",
        family="baseline",
        is_baseline=True,
        loader=_load_sklearn,
    ),
    "nllb_finetuned": ModelInfo(
        id="nllb_finetuned",
        label="NLLB LID-218 (fine-tuned)",
        description="Meta's lid218e continued on the 11-group set with replay. 220 labels.",
        family="fasttext",
        is_baseline=False,
        loader=_load_nllb,
    ),
    "glotlid_finetuned": ModelInfo(
        id="glotlid_finetuned",
        label="GlotLID v3 (fine-tuned)",
        description="GlotLID v3 continued on the 11-group set with replay. 2,104 labels.",
        family="fasttext",
        is_baseline=False,
        loader=_load_glotlid,
    ),
}


def get_classifier(model_name: str) -> BaseClassifier:
    info = MODELS.get(model_name)
    if info is None:
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {', '.join(sorted(MODELS))}"
        )
    return info.loader()


def list_models() -> List[dict]:
    return [
        {
            "id": info.id,
            "label": info.label,
            "description": info.description,
            "family": info.family,
            "is_baseline": info.is_baseline,
            "available": info.available(),
            "correction_languages": info.correction_languages,
        }
        for info in MODELS.values()
    ]
