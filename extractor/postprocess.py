# extractor/postprocess.py
"""
Postprocessing helpers for extracted rows.

"""

from typing import Dict, Any

# attempt normal import first (works when package imports work)
try:
    from validation_and_standardize import normalize_unit_value, UNIT_MAP
except Exception:
    # fallback: load the module directly by file path relative to this file
    import importlib.util
    import importlib.machinery
    from pathlib import Path
    mod_path = Path(__file__).resolve().parents[0] / "validation_and_standardize.py"
    try:
        spec = importlib.util.spec_from_file_location("validation_and_standardize", str(mod_path))
        vmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vmod)
        normalize_unit_value = getattr(vmod, "normalize_unit_value")
        UNIT_MAP = getattr(vmod, "UNIT_MAP", {})
    except Exception:
        # Last-resort stubs to avoid crashing import; functions will no-op
        def normalize_unit_value(value, unit):
            return value, unit
        UNIT_MAP = {}

def postprocess_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply conservative salvage rules:
     - Hemoglobin unusually large (e.g., >30) -> assume g/L and divide by 10
     - Very large Total Protein -> try dividing by 100 (OCR missed decimal)
     - Convert zeros to empty for numeric labs (configurable)
    """
    if not isinstance(row, dict):
        return row

    # Hemoglobin salvage
    try:
        hb = row.get("Hemoglobin")
        if hb not in (None, "", "None"):
            try:
                hv = float(hb)
                if hv > 30:  # likely g/L misread
                    row["Hemoglobin"] = round(hv / 10.0, 2)
                    row.setdefault("_notes", {})
                    row["_notes"]["Hemoglobin"] = "Scaled by /10 (possible g/L -> g/dL)"
            except Exception:
                pass
    except Exception:
        pass

    # Total Protein salvage (e.g., 735 -> 7.35)
    try:
        tp = row.get("Total Protein")
        if tp not in (None, "", "None"):
            try:
                tv = float(tp)
                if tv > 100:
                    row["Total Protein"] = round(tv / 100.0, 2)
                    row.setdefault("_notes", {})
                    row["_notes"]["Total Protein"] = "Scaled by /100 (possible missing decimal)"
            except Exception:
                pass
    except Exception:
        pass

    # Remove placeholder zeros for numeric-looking fields (turn 0 -> "")
    for k in list(row.keys()):
        v = row.get(k)
        if isinstance(v, (int, float)) and v == 0:
            row[k] = ""

    return row
