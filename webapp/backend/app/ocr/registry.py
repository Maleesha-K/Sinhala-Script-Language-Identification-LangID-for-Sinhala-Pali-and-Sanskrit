"""Registry of the OCR engines a user can choose between when uploading.

`id` is persisted on Document.ocr_engine and DocumentPage.ocr_model, and used
by credit_service to look up per-page billing rates, so ids are stable.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from app.ocr.base import BaseOCREngine

DEFAULT_OCR_ENGINE = "tesseract"


@dataclass(frozen=True)
class OCREngineInfo:
    id: str
    label: str
    description: str
    # Celery queue for engines too heavy for the shared prefork pool.
    queue: Optional[str]
    loader: Callable[[], BaseOCREngine]


def _load_tesseract() -> BaseOCREngine:
    from app.ocr.tesseract_engine import tesseract_engine
    return tesseract_engine


def _load_surya() -> BaseOCREngine:
    from app.ocr.surya_engine import surya_engine
    return surya_engine


OCR_ENGINES: Dict[str, OCREngineInfo] = {
    DEFAULT_OCR_ENGINE: OCREngineInfo(
        id=DEFAULT_OCR_ENGINE,
        label="Tesseract",
        description="Classic OCR with Sinhala, Sanskrit and English packs. Fast, a few seconds per page.",
        queue=None,
        loader=_load_tesseract,
    ),
    "surya": OCREngineInfo(
        id="surya",
        label="Surya (CPU)",
        description="Transformer OCR for 90+ languages, run on CPU. Slower than Tesseract: tens of seconds per page.",
        queue="surya",
        loader=_load_surya,
    ),
}


def get_ocr_engine(engine_id: str) -> BaseOCREngine:
    info = OCR_ENGINES.get(engine_id)
    if info is None:
        raise ValueError(
            f"Unknown OCR engine '{engine_id}'. Available: {', '.join(sorted(OCR_ENGINES))}"
        )
    return info.loader()


def list_ocr_engines() -> List[dict]:
    return [
        {
            "id": info.id,
            "label": info.label,
            "description": info.description,
            "is_default": info.id == DEFAULT_OCR_ENGINE,
        }
        for info in OCR_ENGINES.values()
    ]
