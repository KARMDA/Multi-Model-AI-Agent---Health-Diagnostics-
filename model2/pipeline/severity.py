# model2/pipeline/severity.py
"""
Severity mapping and normalization.
Given a numeric value and a reference range, classify into:
- severe_low / low / borderline_low / normal / borderline_high / high / severe_high
Also provides human-friendly note and numeric distance from normal range.
"""

from typing import Tuple, Optional, Dict, Any
from .priors import get_reference_range

def label_from_range(param: str, value: Optional[float], age: Optional[int]=None, gender: Optional[str]=None
                    ) -> Dict[str, Any]:
    """
    Returns:
    {
      "value": value,
      "label": "low"|"normal"|"high"|...,
      "note": "14.0 g/dL (normal range 12.0-15.5)",
      "distance": -2.3  # difference relative to nearest bound (negative if below)
    }
    """
    if value is None:
        return {"value": None, "label": "missing", "note": "No value", "distance": None}

    ref = get_reference_range(param, age=age, gender=gender)
    if not ref:
        return {"value": value, "label": "unknown_range", "note": "No reference range", "distance": None}
    low, high, units = ref
    # ensure floats
    try:
        v = float(value)
    except Exception:
        return {"value": value, "label": "unparseable", "note": str(value), "distance": None}

    # distance: negative below low, positive above high, zero inside
    if v < low:
        diff = v - low
        severity = "severe_low" if v < 0.7*low else "low"
        if v < 0.5*low:
            severity = "very_severe_low"
        note = f"{v} {units} (reference {low} - {high} {units})"
        return {"value": v, "label": severity, "note": note, "distance": diff}
    elif v > high:
        diff = v - high
        severity = "severe_high" if v > 1.5*high else "high"
        if v > 2.0*high:
            severity = "very_severe_high"
        note = f"{v} {units} (reference {low} - {high} {units})"
        return {"value": v, "label": severity, "note": note, "distance": diff}
    else:
        # inside range — check borderline within 5% of edges
        span = high - low if high != low else high or 1
        border = 0.05 * span
        if (v - low) <= border:
            lbl = "borderline_low"
        elif (high - v) <= border:
            lbl = "borderline_high"
        else:
            lbl = "normal"
        note = f"{v} {units} (reference {low} - {high} {units})"
        return {"value": v, "label": lbl, "note": note, "distance": 0.0}
