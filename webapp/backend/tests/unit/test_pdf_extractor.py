import pytest
from unittest.mock import MagicMock, patch
from app.utils.pdf_extractor import PDFExtractor

def test_pdf_extractor_extract_text_empty_bytes():
    """Verify PDFExtractor gracefully returns empty string on empty byte input."""
    extractor = PDFExtractor()
    result = extractor.extract_text(b"")
    assert result == ""

def test_pdf_extractor_extract_text_invalid_bytes():
    """Verify PDFExtractor catches exceptions on corrupted bytes and returns empty string."""
    extractor = PDFExtractor()
    result = extractor.extract_text(b"corrupted_non_pdf_data_header")
    assert result == ""

def test_pdf_extractor_extract_text_with_mocked_fitz():
    """Verify PDFExtractor iterates pages and concatenates extracted text properly."""
    extractor = PDFExtractor()
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "පළමු පිටුවේ පෙළ."
    
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "දෙවන පිටුවේ පෙළ."
    
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_doc.load_page.side_effect = [mock_page1, mock_page2]
    
    with patch("fitz.open", return_value=mock_doc):
        text = extractor.extract_text(b"%PDF-1.4 dummy content")
        assert "පළමු පිටුවේ පෙළ." in text
        assert "දෙවන පිටුවේ පෙළ." in text
        assert text == "පළමු පිටුවේ පෙළ.\nදෙවන පිටුවේ පෙළ."
