# extractor/step1_pdf_utils.py
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
from typing import List, Tuple

def is_pdf_digital(path: str) -> bool:
    """Return True if any page has extractable text via pdfplumber."""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt and txt.strip():
                    return True
        return False
    except Exception:
        return False

def extract_text_from_pdf(path: str) -> Tuple[List[str], list]:
    """
    Extract text from digital PDF using pdfplumber.
    Returns (pages_text, warnings)
    """
    warnings = []
    pages_text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages_text.append(page.extract_text() or "")
        return pages_text, warnings
    except Exception as e:
        warnings.append(f"pdf_extract_error:{e}")
        return [], warnings

def pdf_to_images(path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Convert PDF to list of PIL Images (one per page).
    """
    try:
        pages = convert_from_path(path, dpi=dpi)
        return pages
    except Exception:
        return []
