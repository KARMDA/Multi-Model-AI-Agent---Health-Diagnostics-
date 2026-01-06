import re
from utils.reference_ranges import DEFAULT_REFERENCE_RANGES

def extract_from_lab_table(text: str):
    results = {}

    pattern = re.compile(
        r"(?P<test>[A-Za-z ]+)\s+"
        r"(?P<value>\d+\.?\d*)\s*"
        r"(?P<unit>[a-zA-Z/%]+)?\s+"
        r"(?P<low>\d+\.?\d*)-(?P<high>\d+\.?\d*)"
    )

    for line in text.split("\n"):
        match = pattern.search(line)
        if not match:
            continue

        test = match.group("test").strip()
        value = float(match.group("value"))
        unit = match.group("unit")
        low = float(match.group("low"))
        high = float(match.group("high"))

        status = "normal"
        if value < low:
            status = "low"
        elif value > high:
            status = "high"

        results[test] = {
            "value": value,
            "unit": unit,
            "reference": {"low": low, "high": high},
            "status": status
        }

        # 🔥 THIS IS THE PATCH (RIGHT HERE)
        if not results[test].get("reference"):
            results[test]["reference"] = DEFAULT_REFERENCE_RANGES.get(test)


    return results
