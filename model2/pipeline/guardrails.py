# model2/pipeline/guardrails.py
"""
Guardrails for Model-2 outputs:
- Prevent any function here from producing medication recommendations or dosage
- Ensure no LLM-like free text is produced by Model-2
- Provide a final sanitization step before outputs are written
"""

from typing import Dict, Any

FORBIDDEN_TERMS = ["prescribe", "dosage", "dose", "recommend medication", "start metformin", "start statin"]

def sanitize_output(output: Dict[str,Any]) -> Dict[str,Any]:
    """
    Traverse output and remove/freeze any free-text suggestions that look like prescriptions.
    For Model-2 we only allow: observations, patterns, probable causes, severity, and confidence.
    """
    cleaned = dict(output)  # shallow copy
    # remove any accidental 'recommendations' key
    if "recommendations" in cleaned:
        cleaned["recommendations_removed_by_guardrails"] = cleaned.pop("recommendations")
    # scan notes and supports
    def sanitize_obj(o):
        if isinstance(o, dict):
            for k,v in list(o.items()):
                if isinstance(v, str):
                    for t in FORBIDDEN_TERMS:
                        if t in v.lower():
                            o[k] = "[REDACTED_BY_GUARDRAILS]"
                else:
                    sanitize_obj(v)
        elif isinstance(o, list):
            for item in o:
                sanitize_obj(item)
    sanitize_obj(cleaned)
    return cleaned
