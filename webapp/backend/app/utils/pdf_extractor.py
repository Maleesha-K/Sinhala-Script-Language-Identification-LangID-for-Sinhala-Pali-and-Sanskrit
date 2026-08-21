import fitz # PyMuPDF
import io

class PDFExtractor:
    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        """
        Extracts plain text from a PDF file using PyMuPDF.
        If the PDF is image-only, this will return an empty string,
        indicating that true OCR is required.
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            full_text = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                full_text.append(page_text)
                
            return "\n".join(full_text)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

pdf_extractor = PDFExtractor()
