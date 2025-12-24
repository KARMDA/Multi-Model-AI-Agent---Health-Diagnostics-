# model2/pipeline/contextual.py
from typing import Dict, Any

def to_float_safe(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip().replace(",", "")
        parts = s.split()
        num = parts[0]
        return float(num)
    except Exception:
        return None

def normalize_values(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert numeric-like strings to floats while preserving status fields from Model-1.
    We DO NOT recompute statuses here.
    """
    out = dict(row)
    for key, val in list(row.items()):
        f = to_float_safe(val)
        if f is not None:
            out[key] = f
    # ensure age is left as int or None
    if out.get("age") is not None:
        try:
            out["age"] = int(out["age"])
        except Exception:
            pass
    return out
