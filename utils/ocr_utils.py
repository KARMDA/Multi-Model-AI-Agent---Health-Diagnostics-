from PIL import Image, ImageOps
import pytesseract
from pytesseract import TesseractNotFoundError
import os


def _load_image(path: str) -> Image.Image:
    """
    Load an image from a file path. If a PDF is provided, render the first
    page to an image so OCR can proceed.
    """
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        img = Image.open(path)

    # Basic enhancement to improve OCR accuracy on scanned reports.
    img = img.convert("L")  # grayscale
    img = ImageOps.autocontrast(img)
    # Upscale small images to help OCR detect characters
    if min(img.size) < 1500:
        scale = 1500 / min(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size)

    return img


def _ensure_tesseract_installed():
    try:
        # Allow user to point directly to tesseract executable via env
        custom_cmd = os.getenv("TESSERACT_CMD")
        if custom_cmd:
            pytesseract.pytesseract.tesseract_cmd = custom_cmd
        else:
            # Try common Windows install path as a fallback
            default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_win_path):
                pytesseract.pytesseract.tesseract_cmd = default_win_path
        pytesseract.get_tesseract_version()
        return True
    except (TesseractNotFoundError, FileNotFoundError):
        return False


def run_ocr(path: str) -> str:
    """
    Run OCR using Tesseract. Raises a RuntimeError with a friendly message
    if the Tesseract binary is not available on the system.
    """
    if not _ensure_tesseract_installed():
        raise RuntimeError(
            "Tesseract is not installed or not in PATH. "
            "Install it from https://github.com/tesseract-ocr/tesseract and "
            "ensure the binary is on your system PATH."
        )

    img = _load_image(path)
    return pytesseract.image_to_string(img)
