"""
Per-report structured CSV extractor (one structured CSV per input file).

Output:
  outputs/structured_per_report/<stem>.structured.csv
Columns:
  filename, patient_id, age, gender, <canonicals...>
"""
from pathlib import Path
import importlib.util
from PIL import Image
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "extractor"
SAMPLES = ROOT / "samples"
OUT_DIR = ROOT / "outputs" / "structured_per_report"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# dynamic loader
def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

step1_pdf_utils = load_mod("step1_pdf_utils", EX / "step1_pdf_utils.py")
step1_ocr_utils = load_mod("step1_ocr_utils", EX / "step1_ocr_utils.py")
param_extractor = load_mod("param_extractor", EX / "param_extractor.py")
postprocess = load_mod("postprocess", EX / "postprocess.py")
json_utils = load_mod("json_utils", EX / "json_utils.py")

is_pdf_digital = getattr(step1_pdf_utils, "is_pdf_digital")
extract_text_from_pdf = getattr(step1_pdf_utils, "extract_text_from_pdf")
pdf_to_images = getattr(step1_pdf_utils, "pdf_to_images")
ocr_image_to_text = getattr(step1_ocr_utils, "ocr_image_to_text")
extract_params_from_text = getattr(param_extractor, "extract_params_from_text")
fallback_line_scan = getattr(param_extractor, "fallback_line_scan")
postprocess_row = getattr(postprocess, "postprocess_row")

load_json = getattr(json_utils, "load_json", None)
flatten_json_text = getattr(json_utils, "flatten_json_text", None)

# same patient extraction helpers as Streamlit app (robust)
PID_RE = re.compile(r'Patient\s*ID[:\s\-]*([\w\-\./]+)', re.IGNORECASE)
AGE_RE = re.compile(r'\bAge[:\s\-]*(\d{1,3})', re.IGNORECASE)
GENDER_RE = re.compile(r'\bGender[:\s\-]*(Male|Female|M|F|Other)', re.IGNORECASE)

def _safe_gender_norm(g):
    if g is None:
        return ""
    try:
        import pandas as _pd
        if isinstance(g, float) and _pd.isna(g):
            return ""
    except Exception:
        pass
    s = str(g).strip()
    if not s:
        return ""
    sl = s.lower()
    if sl.startswith("m"):
        return "Male"
    if sl.startswith("f"):
        return "Female"
    return s

def extract_patient_info(text: str):
    if not text:
        return "", "", ""
    pid = ""
    age = ""
    gender = ""
    m = PID_RE.search(text)
    if m:
        pid = m.group(1).strip()
    m = AGE_RE.search(text)
    if m:
        age = m.group(1).strip()
    m = GENDER_RE.search(text)
    if m:
        gender = _safe_gender_norm(m.group(1))
    return pid, age, gender

def downscale_if_needed(pil_img: Image.Image, max_area: int = 40_000_000):
    w, h = pil_img.size
    area = w * h
    if area <= max_area:
        return pil_img
    scale = (max_area / area) ** 0.5
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return pil_img.resize((new_w, new_h), Image.LANCZOS)

def text_for_file(path: Path, dpi=300):
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            if is_pdf_digital(str(path)):
                pages, _ = extract_text_from_pdf(str(path))
                return "\n".join(pages)
            imgs = pdf_to_images(str(path), dpi=dpi)
            out = []
            for im in imgs:
                if not isinstance(im, Image.Image):
                    im = Image.fromarray(im)
                im = downscale_if_needed(im)
                out.append(ocr_image_to_text(im, try_multiple=True))
            return "\n".join(out)
        if ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            img = Image.open(str(path))
            img = downscale_if_needed(img)
            return ocr_image_to_text(img, try_multiple=True)
        if ext == ".json" and load_json and flatten_json_text:
            j = load_json(str(path))
            return flatten_json_text(j)
    except Exception:
        return ""
    return ""

def main():
    files = sorted(SAMPLES.glob("*.*"))
    if not files:
        print("No files in samples/")
        return

    param_keys = list(getattr(param_extractor, "PARAM_MAP", {}).keys())

    for path in files:
        txt = text_for_file(path)

        pid, age, gender = extract_patient_info(txt)

        primary = extract_params_from_text(txt) or []
        secondary = fallback_line_scan(txt) or []
        all_cands = primary + secondary

        grouped = {}
        for c in all_cands:
            canon = c.get("canonical")
            if not canon:
                continue
            if c.get("value") is None:
                continue
            grouped.setdefault(canon, []).append(c)

        row = {"filename": path.name, "patient_id": pid or "", "age": age or "", "gender": gender or ""}

        for canon in param_keys:
            cands = grouped.get(canon, [])
            if not cands:
                row[canon] = ""
            else:
                best = max(cands, key=lambda x: float(x.get("match_confidence") or 0))
                row[canon] = best.get("value")

        # postprocess (units salvage, scaling, etc.)
        row = postprocess_row(row)

        # write one structured CSV per report
        out = OUT_DIR / f"{path.stem}.structured.csv"
        # ensure columns ordering: filename, patient_id, age, gender, then params
        fieldnames = ["filename", "patient_id", "age", "gender"] + param_keys
        # Fill missing keys if any
        for k in fieldnames:
            if k not in row:
                row[k] = ""

        with open(out, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

        print("Structured →", out.name)

if __name__ == "__main__":
    main()
