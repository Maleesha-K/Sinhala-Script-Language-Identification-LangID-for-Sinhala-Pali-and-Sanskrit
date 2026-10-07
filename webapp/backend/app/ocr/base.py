from abc import ABC, abstractmethod

from PIL import Image


class BaseOCREngine(ABC):
    """Extracts the text of one rendered PDF page."""

    # Resolution the PDF page is rendered at before it is handed to the engine.
    render_dpi: int = 300

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Return the page's text, one line per line of the page."""
