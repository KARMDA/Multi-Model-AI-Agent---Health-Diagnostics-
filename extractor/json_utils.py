# extractor/json_utils.py
import json
from typing import Any

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_json_text(data: Any) -> str:
    """
    Convert a JSON object to a single text blob suitable for CSV 'raw_text' cell.
    It concatenates top-level string fields and examines keys commonly used.
    """
    parts = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (str, int, float)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                # if list of dicts (extracted), join each
                for item in v:
                    if isinstance(item, dict):
                        parts.append(" ".join(f"{kk}={vv}" for kk,vv in item.items() if isinstance(vv,(str,int,float))))
                    else:
                        parts.append(str(item))
            else:
                parts.append(str(v))
    else:
        parts.append(str(data))
    return "\n".join(parts)
