# validation_and_standardization.py
"""
Read structured CSV (wide) -> convert to long, standardize and validate.
Exports:
 - read_structured_csv(structured_path: Path) -> pd.DataFrame (long)
 - standardize_dataframe(df_long: pd.DataFrame) -> pd.DataFrame (standardized)
Preserves backwards compatibility: adds columns but keeps original ones.
"""

from pathlib import Path
import re
import json
import math
from typing import Tuple, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[0]
PARAM_MAP_PATH = ROOT / "extractor" / "param_map.json"

# Load param_map.json (used for canonical keys, preferred unit, ranges, aliases)
try:
    with open(PARAM_MAP_PATH, "r", encoding="utf-8") as fh:
        PARAM_MAP = json.load(fh)
except Exception:
    PARAM_MAP = {}

# Build canonical name lookup (lowercase)
CANONICAL_KEYS = {k.lower(): k for k in PARAM_MAP.keys()}

# Build alias -> canonical mapping from param_map (cover common alias lookups)
ALIAS_TO_CANON: dict = {}
for canonical, info in PARAM_MAP.items():
    aliases = info.get("aliases", []) if isinstance(info, dict) else []
    for a in aliases:
        ALIAS_TO_CANON[str(a).strip().lower()] = canonical
    # also map the canonical string itself lower->canonical
    ALIAS_TO_CANON[str(canonical).strip().lower()] = canonical


# ---------- helper: numeric parsing ----------
NUM_RE = re.compile(r'([<>]?\s*-?\d+(?:[.,]\d+)?)')

def parse_number(s: Optional[str]) -> Optional[float]:
    """Extract a numeric value from a string. Returns float or None."""
    if s is None:
        return None
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        try:
            if isinstance(s, float) and math.isnan(s):
                return None
            return float(s)
        except Exception:
            return None
    s = str(s).strip()
    if s == "":
        return None
    # Replace comma decimal
    s_clean = s.replace(" ", "").replace(",", ".")
    # remove any trailing non-numeric (like mg/dL)
    m = NUM_RE.search(s_clean)
    if not m:
        return None
    token = m.group(1)
    token = token.lstrip("<>").strip()
    try:
        return float(token)
    except Exception:
        # fallback: extract first float-like substring
        m2 = re.search(r'-?\d+(?:\.\d+)?', token)
        if m2:
            try:
                return float(m2.group(0))
            except:
                return None
    return None


# ---------- unit conversion helpers ----------
# A small conversion table (observed_unit -> standard_unit) -> multiplier applied to observed to become standard
# e.g., observed "g/L" -> standard "g/dL" factor 0.1 (g/L * 0.1 = g/dL)
CONVERSION_FACTORS = {
    # hemoglobin g/L -> g/dL
    ("g/l", "g/dl"): 0.1,
    ("g/dl", "g/l"): 10.0,
    # hematocrit L/L -> % (if standard is percent)
    ("l/l", "%"): 100.0,
    ("%","l/l"): 0.01,
    # RBC 10^6/uL and 10^12/L often compatible (1 10^6/uL = 10^12/L)
    ("10^6/ul", "10^12/l"): 1000.0,
    ("10^12/l", "10^6/ul"): 0.001,
    # WBC 10^3/uL <-> 10^9/L (1 10^3/uL = 10^9/L)
    ("10^3/ul", "10^9/l"): 1.0,
    ("10^9/l", "10^3/ul"): 1.0,
    # creatinine mg/dL <-> µmol/L (common factor ~88.4); user should expand mapping as needed
    ("mg/dl", "umol/l"): 88.4,
    ("umol/l", "mg/dl"): 1.0/88.4,
    # triglycerides mg/dL <-> mmol/L (factor 0.01129)
    ("mg/dl", "mmol/l"): 0.01129,
    ("mmol/l", "mg/dl"): 1/0.01129,
}

def _norm_unit(u: Optional[str]) -> str:
    if u is None:
        return ""
    return str(u).strip().lower()

def convert_value(value: Optional[float], obs_unit: str, std_unit: str) -> Optional[float]:
    """Convert observed numeric value to standard unit if conversion factor exists."""
    if value is None:
        return None
    obs = _norm_unit(obs_unit)
    std = _norm_unit(std_unit)
    if obs == "" or std == "" or obs == std:
        return value
    # Try exact match in table
    f = CONVERSION_FACTORS.get((obs, std))
    if f is not None:
        try:
            return float(value) * float(f)
        except Exception:
            return value
    # Try fallback: if obs contains std as substring or vice versa, skip
    if std in obs or obs in std:
        # no conversion known -> return value (assume compatible)
        return value
    # No known conversion -> return original (caller can flag unit mismatch)
    return value


# ---------- read_structured_csv ----------
def read_structured_csv(structured_path: Path) -> pd.DataFrame:
    """
    Read a wide structured CSV (the one created from extraction) and convert to long format.

    Expected wide CSV columns:
      filename, patient_id, age, gender, <param1>, <param2>, ...
    This function melts parameter columns and returns long DataFrame with columns:
      filename, patient_id, age, gender, parameter, canonical, raw_value
    where `canonical` is the canonical name taken from PARAM_MAP keys when we can match, else parameter text.
    """
    p = Path(structured_path)
    if not p.exists():
        raise FileNotFoundError(p)

    dfw = pd.read_csv(p, dtype=str).fillna("")
    # expected patient-level fields
    meta_cols = ["filename", "patient_id", "age", "gender"]
    for c in meta_cols:
        if c not in dfw.columns:
            dfw[c] = ""  # ensure present

    # find parameter columns (anything not in meta_cols)
    param_cols = [c for c in dfw.columns if c not in meta_cols]

    # melt
    rows = []
    for _, row in dfw.iterrows():
        meta = {c: row.get(c, "") for c in meta_cols}
        for param in param_cols:
            raw_val = row.get(param, "")
            if raw_val == "":
                # still include empty rows (so we preserve parameter list) — but we may drop later
                pass
            # map param -> canonical if alias exists
            pkey = str(param).strip().lower()
            canonical = None
            if pkey in ALIAS_TO_CANON:
                canonical = ALIAS_TO_CANON[pkey]
            else:
                # try exact match against canonical keys
                if pkey in CANONICAL_KEYS:
                    canonical = CANONICAL_KEYS[pkey]
                else:
                    # try fuzzy/simple substring: check if any canonical contains param token
                    for kk in CANONICAL_KEYS:
                        if kk in pkey and len(kk) >= 3:
                            canonical = CANONICAL_KEYS[kk]
                            break
            rows.append({
                "filename": meta["filename"],
                "patient_id": meta["patient_id"],
                "age": meta["age"],
                "gender": meta["gender"],
                "parameter": param,
                "canonical": canonical or param,
                "raw_value": raw_val,
            })

    df_long = pd.DataFrame(rows)
    # normalize columns
    # keep ordering stable
    cols = ["patient_id", "filename", "age", "gender", "parameter", "canonical", "raw_value"]
    df_long = df_long[cols]
    return df_long


# ---------- standardize_dataframe ----------
def standardize_dataframe(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Given the long-form dataframe, extract numeric values, normalize units & produce:
      - value_std (original extracted numeric string optionally normalized)
      - value_num (float)
      - unit_std (string: preferred unit from param_map.json or observed)
      - valid (bool), invalid_reason (str or empty)
    Returns a new DataFrame (copy) with added columns.
    """
    df = df_long.copy()

    # ensure columns exist
    for c in ["patient_id", "filename", "age", "gender", "parameter", "canonical", "raw_value"]:
        if c not in df.columns:
            df[c] = ""

    value_nums = []
    value_std = []
    unit_std = []
    valid_flags = []
    invalid_reasons = []

    for idx, r in df.iterrows():
        raw = r.get("raw_value", "")
        # sometimes param_map includes a unit field per canonical
        canon = r.get("canonical") or ""
        canon_key = str(canon).strip()
        pm_entry = None
        if canon_key:
            # find param map entry case-insensitively
            for k, v in PARAM_MAP.items():
                if k.lower() == str(canon_key).strip().lower() or (isinstance(v, dict) and v.get("param_id") and str(v.get("param_id")).lower() == str(canon_key).lower()):
                    pm_entry = v
                    break

        # preferred unit from param map
        preferred_unit = ""
        if isinstance(pm_entry, dict):
            preferred_unit = pm_entry.get("unit") or pm_entry.get("range", {}).get("units") or ""

        # Attempt to parse number
        num = parse_number(raw)

        # try detect unit suffix in raw (e.g., "13 g/dL", "13mg/dL", "13 %")
        detected_unit = ""
        if isinstance(raw, str) and raw.strip():
            # capture trailing non-numeric tokens
            m = re.search(r'[A-Za-z%µμμμ^0-9/\. ]+$', raw.strip())
            if m:
                candidate = m.group(0).strip()
                # clean candidate
                candidate = candidate.replace("µ", "u").replace("μ","u")
                # pick only token that contains letters or % or slash
                if any(ch.isalpha() or ch in "%/" for ch in candidate):
                    detected_unit = candidate

        # normalize detected unit
        detected_unit_norm = _norm_unit(detected_unit)
        preferred_unit_norm = _norm_unit(preferred_unit)

        # If numeric exists and preferred unit different, attempt conversion if factor found
        converted_num = num
        unit_to_report = detected_unit_norm or preferred_unit_norm or ""

        if num is not None and preferred_unit_norm and detected_unit_norm and detected_unit_norm != preferred_unit_norm:
            # convert numeric if mapping exists
            conv = CONVERSION_FACTORS.get((detected_unit_norm, preferred_unit_norm))
            if conv is not None:
                try:
                    converted_num = float(num) * float(conv)
                    unit_to_report = preferred_unit_norm
                except Exception:
                    converted_num = num
            else:
                # try other heuristics: e.g., percent vs ratio L/L
                if detected_unit_norm == "l/l" and preferred_unit_norm == "%":
                    converted_num = float(num) * 100.0
                    unit_to_report = preferred_unit_norm
                # else leave as is and report both in units_used later

        # If numeric is None, but raw contains only decimals with % etc, attempt to strip and parse
        if num is None and isinstance(raw, str) and raw.strip():
            # sometimes value is like "<0.5" etc - parse_number covers it but just in case
            try:
                # fallback: get all digits and decimal, e.g. "ND" or "—" will remain None
                token = re.search(r'-?\d+(?:[.,]\d+)?', raw)
                if token:
                    num = float(token.group(0).replace(",", "."))
                    converted_num = num
            except Exception:
                pass

        # determine validity
        if num is None:
            valid = False
            reason = "no_numeric"
        else:
            valid = True
            reason = ""

        # final values appended
        value_nums.append(None if converted_num is None else float(converted_num))
        # keep a string version for display (prefer the numeric cleaned)
        value_std.append("" if converted_num is None else str(converted_num))
        unit_std.append(unit_to_report)
        valid_flags.append(valid)
        invalid_reasons.append(reason)

    df["value_std"] = value_std
    df["value_num"] = value_nums
    df["unit_std"] = unit_std
    df["valid"] = valid_flags
    df["invalid_reason"] = invalid_reasons

    # preserve other columns; ensure types
    # cast age to numeric if possible
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")

    return df
