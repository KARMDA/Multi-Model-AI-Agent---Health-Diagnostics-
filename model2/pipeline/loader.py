# model2/pipeline/loader.py
import csv
import json
import re
from typing import Dict, Any

ALIAS_MAP = {
    "hdl_cholesterol": "HDL",
    "total_cholesterol": "Total_Cholesterol",
    "triglycerides": "Triglycerides",
    "glucose_fasting": "Glucose_Fasting",
    "hba1c": "HbA1c",
    "creatinine": "Creatinine",
    "crp": "CRP",
    "hemoglobin": "Hemoglobin",
    "platelets": "Platelets",
    "mcv": "MCV",
    "mch": "MCH",
    "mchc": "MCHC",
    "rdw": "RDW",
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "ldl": "LDL",
    "vldl": "VLDL",
    "urea_bun": "Urea_BUN",
    "urea": "Urea_BUN",
}

META_KEYS = {"age", "gender", "patient_id", "filename", "report_date"}

def _normalize_header(h: str) -> str:
    if h is None:
        return ""
    s = h.strip()
    s = re.sub(r"\(([^)]+)\)", r" \1", s)            # parentheses -> text
    s = s.replace("%", " percent")
    s = re.sub(r"[^0-9A-Za-z]+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s

def _canonical_key(h: str) -> str:
    n = _normalize_header(h)
    key = n.lower()
    if key in ALIAS_MAP:
        return ALIAS_MAP[key]
    parts = n.split("_")
    parts = [p.upper() if p.lower() in ("hdl","ldl","vldl","crp","hba1c","rbc","wbc") else p.capitalize() for p in parts]
    return "_".join(parts)

def _cast_number(s: Any):
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    # remove common units and letters
    s = re.sub(r"[A-Za-z/°%]+", "", s).strip()
    s = s.replace(",", "")
    if s == "":
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        try:
            return float(s)
        except Exception:
            return s

def load_input(path: str) -> Dict[str, Any]:
    """
    Load Model-1 output CSV (one-row) or JSON (testing).
    Returns a dict:
      {
        "age": ...,
        "gender": ...,
        "parameters": { <canonical param>: numeric_or_None, ... },
        "status": { <canonical param>: "LOW"/"HIGH"/"NORMAL", ... },
        "notes": { <canonical param>: "..." }
      }
    """
    result = {
        "parameters": {},
        "status": {},
        "notes": {},
    }

    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            j = json.load(f)
        # flatten tester JSON -> result
        for k, v in j.items():
            key = _canonical_key(k)
            if key.lower() in ("age", "gender", "patient_id", "filename", "report_date"):
                result[key] = v
                continue
            # try numeric cast
            num = _cast_number(v)
            if isinstance(num, (int, float)) or num is None:
                result["parameters"][key] = num
            else:
                # non-numeric strings could be statuses/notes
                up = str(v).strip().upper()
                if up in ("LOW", "HIGH", "NORMAL"):
                    result["status"][key] = up
                else:
                    result["notes"][key] = str(v)
        return result

    # CSV case
    with open(path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        try:
            row = next(reader)
        except StopIteration:
            return result

    # process columns
    for raw_h, raw_v in row.items():
        norm = _normalize_header(raw_h)
        # detect status/note columns by suffix before canonicalization
        lowkey = norm.lower()
        if lowkey.endswith("_status") or lowkey.endswith(" status"):
            base = norm.rsplit("_", 1)[0]
            canonical = _canonical_key(base)
            val = (raw_v or "").strip()
            if val != "":
                result["status"][canonical] = val.upper()
            continue
        if lowkey.endswith("_note") or lowkey.endswith(" note"):
            base = norm.rsplit("_", 1)[0]
            canonical = _canonical_key(base)
            val = (raw_v or "").strip()
            if val != "":
                result["notes"][canonical] = val
            continue

        canonical = _canonical_key(norm)
        # metadata
        if canonical.lower() in ("age", "gender", "patient_id", "filename", "report_date"):
            if canonical.lower() == "age":
                result["age"] = _cast_number(raw_v)
            else:
                result[canonical] = (raw_v or "").strip() if raw_v is not None else None
            continue

        # numeric lab
        val = _cast_number(raw_v)

        # ONLY numeric values are allowed as parameters
        if isinstance(val, (int, float)) or val is None:
            result["parameters"][canonical] = val
        # everything else is ignored here (strings handled earlier as status/note)

    return result
