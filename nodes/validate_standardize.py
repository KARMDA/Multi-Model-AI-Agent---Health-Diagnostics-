from utils.reference_ranges import load_reference_ranges


# Parameter-specific implicit scale handling
SCALE_RULES = {
    "Total WBC count": {"threshold": 100, "multiplier": 1000},
    "Platelet Count": {"threshold": 1000, "multiplier": 1000},
    "Absolute Neutrophils": {"threshold": 100, "multiplier": 1000},
    "Absolute Lymphocytes": {"threshold": 100, "multiplier": 1000},
}


def normalize_numeric(value):
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        return float(value)
    except Exception:
        return None


def normalize_scale(param, value):
    rule = SCALE_RULES.get(param)
    if not rule:
        return value

    if value < rule["threshold"]:
        return value * rule["multiplier"]

    return value


def resolve_reference(ref):
    """
    Resolve reference range deterministically.
    Supports:
    - {"low": x, "high": y}
    - {"adult_male": {...}, "adult_female": {...}}
    """
    if not isinstance(ref, dict):
        return None, None

    if "low" in ref and "high" in ref:
        return ref["low"], ref["high"]

    # deterministic fallback order
    for key in ("adult_male", "adult_female", "adult"):
        if key in ref and isinstance(ref[key], dict):
            return ref[key].get("low"), ref[key].get("high")

    return None, None


def determine_flag(value, low, high):
    if value is None or low is None or high is None:
        return "UNKNOWN"
    if value < low:
        return "LOW"
    if value > high:
        return "HIGH"
    return "NORMAL"


def validate_and_standardize(state):
    ranges = load_reference_ranges()
    cleaned = {}
    errors = list(getattr(state, "errors", []) or [])

    extracted = getattr(state, "extracted_params", {}) or {}

    for param, info in extracted.items():
        raw_val = info.get("value")
        raw_unit = info.get("unit")

        if raw_val is None:
            errors.append(f"{param}: missing value")
            continue

        if param not in ranges:
            errors.append(f"{param}: no reference range defined")
            continue

        value = normalize_numeric(raw_val)
        if value is None:
            errors.append(f"{param}: invalid numeric value '{raw_val}'")
            continue

        # Normalize scale BEFORE reference comparison
        value = normalize_scale(param, value)

        ref = ranges[param].get("reference")
        low, high = resolve_reference(ref)

        if low is None or high is None:
            errors.append(f"{param}: invalid reference range")
            continue

        flag = determine_flag(value, low, high)

        # Canonical unit (do not trust OCR blindly)
        units = ranges[param].get("units")
        unit = raw_unit or (units[0] if isinstance(units, list) and units else None)

        cleaned[param] = {
            "value": value,
            "unit": unit,
            "reference": {"low": low, "high": high},
            "flag": flag
        }

    return {
        "validated_params": cleaned,
        "errors": errors
    }


def validate_standardize_node(state):
    return validate_and_standardize(state)