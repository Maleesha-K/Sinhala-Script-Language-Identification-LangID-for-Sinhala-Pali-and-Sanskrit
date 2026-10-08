"""Surya OCR v1 (surya-ocr 0.17.x), run on CPU with PyTorch.

The models (~1.5 GB on disk, ~4 GB RAM once loaded) are downloaded on first
use and loaded once per worker process, so Surya jobs go to a dedicated
single-process Celery queue rather than every prefork worker holding a copy.
"""
import os
import threading

from PIL import Image

from app.ocr.base import BaseOCREngine
from app.ocr.reading_order import Line, lines_to_text


class SuryaEngine(BaseOCREngine):
    # Surya works best on pages no wider than ~2048px; A4 at 200 DPI is 1654px.
    render_dpi = 200

    def __init__(self):
        self._recognition = None
        self._detection = None
        self._lock = threading.Lock()

    def _ensure_loaded(self):
        if self._recognition is not None:
            return
        with self._lock:
            if self._recognition is not None:
                return
            # Default to CPU unless the deployment explicitly picks a device.
            os.environ.setdefault("TORCH_DEVICE", "cpu")
            from surya.detection import DetectionPredictor
            from surya.foundation import FoundationPredictor
            from surya.recognition import RecognitionPredictor

            self._detection = DetectionPredictor()
            self._recognition = RecognitionPredictor(FoundationPredictor())

    def extract_text(self, image: Image.Image) -> str:
        self._ensure_loaded()
        predictions = self._recognition([image.convert("RGB")], det_predictor=self._detection)
        lines = predictions[0].text_lines if predictions else []
        # Surya returns lines in detection order; put them in reading order
        # (columns, paragraphs) as Tesseract does.
        return lines_to_text(Line(*line.bbox, line.text) for line in lines)


surya_engine = SuryaEngine()
