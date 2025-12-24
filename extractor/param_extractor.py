"""
Robust parameter extraction module.

Provides:
 - extract_params_from_text(text) -> list[dict]
 - fallback_line_scan(text) -> list[dict]

Each dict:
{
  "raw_name": str,
  "raw_value": str | None,
  "value": float | None,
  "unit": str | None,
  "canonical": str | None,
  "match_confidence": float,
  "source": str | None   # e.g. "regex", "line_firstnum", "special_line_start", "line_token"
}
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ----------------- load param_map.json -----------------
BASE = Path(__file__).resolve().parents[0]
PMAP = BASE / "param_map.json"
if not PMAP.exists():
    PMAP = Path(__file__).resolve().parents[1] / "extractor" / "param_map.json"

if PMAP.exists():
    with open(PMAP, "r", encoding="utf-8") as f:
        PARAM_MAP = json.load(f)
else:
    PARAM_MAP = {}

# Build alias -> canonical lookup
CANONICAL_LOOKUP: Dict[str, str] = {}
for canon, info in PARAM_MAP.items():
    aliases = []
    if isinstance(info, dict):
        aliases = info.get("aliases", [])
    elif isinstance(info, list):
        aliases = info
    for a in aliases:
        CANONICAL_LOOKUP[str(a).lower()] = canon
    CANONICAL_LOOKUP[str(canon).lower()] = canon

# --------- patterns ----------
CANDIDATE_PARAM_PATTERN = re.compile(
    r'([A-Za-z0-9%()./\-\s]{3,40})\s*[:\-]?\s*([<>]?\s?-?\d+(?:[.,]\d+)?)\s*'
    r'(mg/dL|g/dL|g/L|mmol/L|µIU/mL|uIU/mL|IU/L|%|mmol/L|ng/mL|pg/mL|U/L|mm/hr)?',
    flags=re.IGNORECASE,
)

NUM_PATTERN = re.compile(r'([<>]?\s?-?\d+(?:[.,]\d+)?)')

# (old) line-start pattern is still kept for compatibility
LINE_START_PATTERN = re.compile(
    r'^\s*([A-Za-z][A-Za-z0-9 ()/%.,\-]{2,50})\s+([<>]?\s?-?\d+(?:[.,]\d+)?)\s*'
    r'(mg/dL|g/dL|g/L|mmol/L|µIU/mL|uIU/mL|IU/L|%|mmol/L|ng/mL|pg/mL|U/L|mm/hr)?',
    flags=re.IGNORECASE,
)


def _looks_like_name(s: str) -> bool:
    """Filter out junk names like '-' or mostly punctuation."""
    if not s:
        return False
    s = s.strip()
    if len(s) < 2:
        return False
    # must contain at least one letter
    if not any(c.isalpha() for c in s):
        return False
    # reject if letters are <30% of non-space chars
    letters = sum(1 for c in s if c.isalpha())
    total = len(s.replace(" ", ""))
    if total and letters / total < 0.3:
        return False
    return True


def normalize_number(s: str) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    s = s.replace(" ", "")
    s = s.replace(",", ".")
    # strip leading < or >
    s = s.lstrip("<>").strip()
    try:
        return float(s)
    except Exception:
        m = re.search(r'-?\d+(?:\.\d+)?', s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None


# Try rapidfuzz if available, else fallback
try:
    from rapidfuzz import process, fuzz
    _HAS_RAPIDFUZZ = True
except Exception:
    process = None
    fuzz = None
    _HAS_RAPIDFUZZ = False


def fuzzy_canonical(name: str, threshold: int = 78) -> Tuple[Optional[str], float]:
    """
    Match extracted name -> canonical. Use rapidfuzz if available, else substring matching.
    Returns (canonical_name, score) where score is 0..1.
    """
    if not name:
        return None, 0.0
    name_clean = re.sub(r'[^A-Za-z0-9 ]', ' ', name).strip().lower()
    if not name_clean:
        return None, 0.0

    # direct lookup
    if name_clean in CANONICAL_LOOKUP:
        return CANONICAL_LOOKUP[name_clean], 1.0

    # token-level lookup
    tokens = [t for t in name_clean.split() if len(t) > 1]
    for token in tokens:
        if token in CANONICAL_LOOKUP:
            return CANONICAL_LOOKUP[token], 0.9

    # rapidfuzz matching
    if _HAS_RAPIDFUZZ and CANONICAL_LOOKUP and len(name_clean) >= 3:
        choices = list(CANONICAL_LOOKUP.keys())
        match = process.extractOne(name_clean, choices, scorer=fuzz.WRatio)
        if match:
            matched_str, score, _ = match
            if score >= threshold:
                return CANONICAL_LOOKUP[matched_str], score / 100.0
            return None, score / 100.0

    # fallback substring check
    for k in CANONICAL_LOOKUP:
        if k in name_clean and len(k) >= 3:
            return CANONICAL_LOOKUP[k], 0.6

    return None, 0.0


def extract_params_from_text(text: str) -> List[Dict]:
    """
    Global regex scan. (kept for backward compatibility)
    """
    out: List[Dict] = []
    if not text:
        return out

    for m in CANDIDATE_PARAM_PATTERN.finditer(text):
        raw_name = m.group(1).strip()
        if not _looks_like_name(raw_name):
            continue

        raw_value = m.group(2).strip()
        unit = m.group(3) if m.group(3) else None
        val = normalize_number(raw_value)
        canon, score = fuzzy_canonical(raw_name)

        out.append({
            "raw_name": raw_name,
            "raw_value": raw_value,
            "value": val,
            "unit": unit,
            "canonical": canon,
            "match_confidence": score,
            "source": "regex"
        })
    return out


def fallback_line_scan(text: str) -> List[Dict]:
    """
    Secondary strategy, more robust for table rows like:
      'CK 1416 IU/L 38-204'
      'ALP 72 IU/L 40-129'

    Steps:
      A0) new: take substring before the FIRST number as name, and that first number as value
          -> source = 'line_firstnum'
      A)  old special line-start regex (kept)          -> 'special_line_start'
      B)  generic line scanning with tokens           -> 'line_token'
    """
    out: List[Dict] = []
    if not text:
        return out

    for line in text.splitlines():
        if not line:
            continue
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # ---------- A0) NEW: first-number heuristic ----------
        # e.g. "CK 1416 IU/L 38-204" -> name_part = "CK", value = 1416
        m_first = NUM_PATTERN.search(line_stripped)
        if m_first:
            raw_value = m_first.group(1).strip()
            name_part = line_stripped[:m_first.start()].strip(":- \t")
            if _looks_like_name(name_part):
                val_first = normalize_number(raw_value)
                canon_first, score_first = fuzzy_canonical(name_part, threshold=70)
                if canon_first and val_first is not None:
                    # tiny boost so this wins over noisier matches for same line
                    boosted_score = min(1.0, (score_first or 0.0) + 0.05)
                    out.append({
                        "raw_name": name_part,
                        "raw_value": raw_value,
                        "value": val_first,
                        "unit": None,
                        "canonical": canon_first,
                        "match_confidence": boosted_score,
                        "source": "line_firstnum"
                    })

        # ---------- A) existing special line-start pattern ----------
        m = LINE_START_PATTERN.match(line_stripped)
        if m:
            raw_name = m.group(1).strip()
            raw_value = m.group(2).strip()
            unit = m.group(3) if m.group(3) else None
            if _looks_like_name(raw_name):
                val = normalize_number(raw_value)
                canon, score = fuzzy_canonical(raw_name, threshold=70)
                if canon and val is not None:
                    out.append({
                        "raw_name": raw_name,
                        "raw_value": raw_value,
                        "value": val,
                        "unit": unit,
                        "canonical": canon,
                        "match_confidence": score,
                        "source": "special_line_start"
                    })

        # ---------- B) generic token-based scan ----------
        # require both letters and digits in line (lab-like)
        if not any(c.isalpha() for c in line_stripped) or not any(c.isdigit() for c in line_stripped):
            continue

        nums = NUM_PATTERN.findall(line)
        val = normalize_number(nums[0]) if nums else None

        tokens = re.split(r'[\t,;|:]', line)
        for token in tokens:
            token_stripped = token.strip()
            if not _looks_like_name(token_stripped):
                continue
            canon, score = fuzzy_canonical(token_stripped, threshold=85)
            if canon and val is not None:
                out.append({
                    "raw_name": token_stripped,
                    "raw_value": nums[0] if nums else None,
                    "value": val,
                    "unit": None,
                    "canonical": canon,
                    "match_confidence": score,
                    "source": "line_token"
                })

    return out


__all__ = [
    "extract_params_from_text",
    "fallback_line_scan",
    "normalize_number",
    "fuzzy_canonical",
    "PARAM_MAP",
]
