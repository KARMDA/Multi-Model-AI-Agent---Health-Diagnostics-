# model2/verifier.py
from typing import Any, Tuple
from jsonschema import validate, ValidationError

SCHEMA = {
  "type": "object",
  "properties": {
    "interpretation": {"type": "string"},
    "numeric_fields": {
      "type": "object",
      "properties": {
        "LDL": {"type": ["number","null"]},
        "TG_HDL": {"type": ["number","null"]},
        "cardio_risk_score": {"type": ["number","null"]}
      },
      "required": ["LDL","TG_HDL","cardio_risk_score"]
    },
    "severity": {
      "type": "object",
      "properties": {
        "platelets": {"type":"object"},
        "hemoglobin": {"type":"object"},
        "ldl": {"type":"object"}
      }
    },
    "red_flags": {"type": "array", "items": {"type": "string"}},
    "recommendations": {"type": "array", "items": {"type": "string"}},
    "explainability": {"type": "array", "items": {"type": "string"}},
    "evidence_refs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "claim": {"type":"string"},
          "sources": {"type":"array", "items":{"type":"string"}}  # e.g. ["Platelets:109","LDL:84.6"]
        },
        "required":["claim","sources"]
      }
    }
  },
  "required": ["interpretation","numeric_fields","red_flags","recommendations","explainability"],
  "additionalProperties": False
}


from model2.pipeline.guardrails import scan_for_dangerous_recommendations, redact_recommendations

def verify_result(parsed: Any) -> Tuple[bool, str, Any]:
    if parsed is None:
        return False, "Could not parse JSON from LLM output", None
    if not isinstance(parsed, dict):
        return False, "Parsed output not a JSON object", None
    try:
        validate(instance=parsed, schema=SCHEMA)
    except ValidationError as e:
        return False, f"Schema validation failed: {e.message}", None
    recs = parsed.get("recommendations", [])
    has_danger, offenders = scan_for_dangerous_recommendations(recs)
    if has_danger:
        sanitized = dict(parsed)
        sanitized["recommendations"] = redact_recommendations(recs)
        return False, f"Sanitized dangerous content (keywords: {', '.join(offenders)})", sanitized
    return True, "OK", parsed
