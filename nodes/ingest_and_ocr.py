from utils.ocr_utils import run_ocr
import fitz  # PyMuPDF

def extract_pdf_text(path: str) -> str:
    """
    Attempt to extract raw text from a PDF without OCR.
    """
    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception:
        return ""

def ingest_and_ocr_node(state):
    """
    Node input: state (ReportState)
    Node returns: dict to update state (langgraph expects node returns)
    """
    file_path = state.raw_file_path
    text = ""
    
    # 1. Try native PDF text extraction first (faster, cleaner if selectable text)
    if file_path.lower().endswith(".pdf"):
        text = extract_pdf_text(file_path)

    # 2. If no text found (scanned PDF or Image), use OCR
    if not text or len(text.strip()) < 50:
        try:
            text = run_ocr(file_path)
        except Exception as e:
            # Bubble up a clear, user-friendly error instead of crashing.
            return {"errors": state.errors + [f"OCR failed: {str(e)}"]}

    return {"raw_text": text}
