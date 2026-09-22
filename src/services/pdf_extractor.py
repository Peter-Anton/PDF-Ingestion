import logging
import fitz  # PyMuPDF

from exceptions import PDFExtractionError

logger = logging.getLogger(__name__)


def extract_text(data: bytes) -> str:
    text = ""
    try:
        # Open the PDF directly from the byte stream in memory
        with fitz.open(stream=data, filetype="pdf") as doc:
            pages_text = [
                page.get_text()
                for page in doc
                if page.get_text()
            ]
            text = "\n".join(pages_text).strip()
            
    except Exception as e:
        logger.warning(f"fitz in-memory parsing failed: {e}")
        raise PDFExtractionError("Could not extract text from the file.") from e

    if not text:
        raise PDFExtractionError("Could not extract any text from the file. It may be an image-only PDF.")

    return text