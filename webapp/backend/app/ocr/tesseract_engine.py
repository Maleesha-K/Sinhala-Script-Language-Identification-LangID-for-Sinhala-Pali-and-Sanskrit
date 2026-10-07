from PIL import Image

from app.ocr.base import BaseOCREngine


class TesseractEngine(BaseOCREngine):
    render_dpi = 300

    def extract_text(self, image: Image.Image) -> str:
        import pytesseract

        # Sinhala, Sanskrit (Devanagari) and English language packs.
        return pytesseract.image_to_string(image, lang="sin+san+eng")


tesseract_engine = TesseractEngine()
