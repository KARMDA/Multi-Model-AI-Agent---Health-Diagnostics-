import io
import re
from typing import List, Dict, Any, Tuple
import pdfplumber
import pandas as pd
import fitz # PyMuPDF
import pytesseract
from PIL import Image

from model2_pattern import model_2_pattern_risk_analysis
from model3_pattern import apply_contextual_adjustments
from synthesizer import synthesize_findings, generate_personalized_recommendations

# --- CONFIGURATION & GROUND TRUTH ---

# Known parameters and their highly flexible regex patterns
PARAMETER_PATTERNS = {
    "Hemoglobin": r"(Hemoglobin|HB|Hgb)[^\\n\\d]*?([\d\.,\-<]+)\s*(g/dL|g/dl|g/L)?",
    "Glucose": r"Glucose[^\\n\\d]*?([\d\.,\-<]+)\s*(mg/dL|mmol/L|mmol/l)?",
    "Cholesterol": r"Cholesterol[^\\n\\d]*?([\d\.,\-<]+)\s*(mg/dL|mmol/L|mmol/l)?",
    "WBC": r"(WBC|White Blood Cell|Leukocyte)[^\\n\\d]*?([\d\.,\-<]+)\s*(K/mcL|10\^9/L|x10\^9/L|/mm3|cells/µL|cells/uL|/µL|x10e3/ul)?",
    "RBC": r"(RBC|Red Blood Cell)[^\\n\\d]*?([\d\.,\-<]+)\s*(M/mcL|mill/cumm|10\^12/L|mil/cumm|million/mm3)?",
    "Platelet": r"(Platelet[s]?\s*(Count)?)[^\\n\\d]*?([\d\.,\-<]+)\s*(K/mcL|cumm|/mm3|cells/µL|x10\^3/uL|x10e3/ul)?",
    "PCV": r"(PCV|Packed Cell Volume|Hematocrit|Hct)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent)?",
    "MCV": r"MCV[^\\n\\d]*?([\d\.,\-<]+)\s*(fL)?",
    "MCH": r"MCH[^\\n\\d]*?([\d\.,\-<]+)\s*(pg)?",
    "MCHC": r"MCHC[^\\n\\d]*?([\d\.,\-<]+)\s*(g/dL)?",
    "RDW": r"RDW[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|CV)?",
    # Absolute counts and percentages
    "Neutrophils": r"(Neutrophil[s]?|Absolute Neutrophil)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|K/mcL)?",
    "Lymphocytes": r"(Lymphocyte[s]?|Absolute Lymphocyte)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|K/mcL)?",
    "Monocyte": r"(Monocyte[s]?|Absolute Monocyte)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|K/mcL)?",
    "Eosinophils": r"(Eosinophil[s]?|Absolute Eosinophil)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|K/mcL)?",
    "Basophils": r"(Basophil[s]?|Absolute Basophil)[^\\n\\d]*?([\d\.,\-<]+)\s*(%|percent|K/mcL)?",
}

# Aliases for robust table lookup
PARAMETER_ALIASES = {
    "Hemoglobin": ["hemoglobin", "hb", "hgb"],
    "Glucose": ["glucose", "blood glucose", "sugar", "gluc"],
    "Cholesterol": ["cholesterol", "chol", "total cholesterol"],
    "WBC": ["wbc", "white blood cell", "leukocytes", "wbc count"],
    "RBC": ["rbc", "red blood cell", "rbc count"],
    "Platelet": ["platelet", "platelets", "platelet count"],
    "PCV": ["pcv", "packed cell volume", "hematocrit", "hct"],
    "MCV": ["mcv", "mean cell volume"], # Updated alias
    "MCH": ["mch", "mean cell hemoglobin"], # Updated alias
    "MCHC": ["mchc", "mean cell hb conc"], # Updated alias
    "RDW": ["rdw", "red cell dist width", "rdw-cv"], # Updated alias
    "Neutrophils": ["neutrophils", "neutrophil", "neut", "absolute neutrophil"],
    "Lymphocytes": ["lymphocytes", "lymphocyte", "lymph", "absolute lymphocyte"],
    "Monocyte": ["monocytes", "monocyte", "mono", "absolute monocyte"],
    "Eosinophils": ["eosinophils", "eosinophil", "eos", "absolute eosinophil"], 
    "Basophils": ["basophils", "basophil", "baso", "absolute basophil"],     
}

# --- REFERENCE DATABASE (COMPREHENSIVE) ---
REFERENCE_DATABASE = {
    "Hemoglobin": {"range": (12.0, 16.0), "unit": "g/dL"},
    "Glucose": {"range": (70.0, 100.0), "unit": "mg/dL"},
    "Cholesterol": {"range": (125.0, 200.0), "unit": "mg/dL"},
    "WBC": {"range": (4.5, 11.0), "unit": "x10^9/L"},
    "RBC": {"range": (4.2, 5.8), "unit": "x10^12/L"},
    "Platelet": {"range": (150.0, 450.0), "unit": "x10^3/uL"},
    "PCV": {"range": (36.0, 52.0), "unit": "%"},
    "MCV": {"range": (80.0, 100.0), "unit": "fL"},
    "MCH": {"range": (27.0, 33.0), "unit": "pg"},
    "MCHC": {"range": (32.0, 36.0), "unit": "g/dL"},
    "RDW": {"range": (11.5, 14.5), "unit": "%"},
    "Neutrophils": {"range": (40.0, 70.0), "unit": "%"}, # Percentage
    "Lymphocytes": {"range": (20.0, 40.0), "unit": "%"}, # Percentage
    "Monocyte": {"range": (0.0, 8.0), "unit": "%"},     # Percentage
    "Eosinophils": {"range": (0.0, 6.0), "unit": "%"},   
    "Basophils": {"range": (0.0, 2.0), "unit": "%"},     
}

# --- GROUND TRUTH FOR ACCURACY METRICS (Milestone 1 Evaluation) ---
# Hardcoded ground truth for CBC-sample-report-with-notes_0.pdf
GROUND_TRUTH_CORE = {
    "WBC": {"Value": 6.9, "Classification": "Normal"},  # 6.9 x10^9/L (Range 4.5-11.0)
    "RBC": {"Value": 1.8, "Classification": "Low"},    # 1.8 M/mcL -> 1.8 x10^12/L (Range 4.2-5.8)
    "Hemoglobin": {"Value": 6.5, "Classification": "Low"}, # 6.5 g/dL (Range 12.0-16.0)
    "PCV": {"Value": 19.5, "Classification": "Low"},   # 19.5 % (Range 36.0-52.0)
    "MCV": {"Value": 109.6, "Classification": "High"}, # 109.6 fL (Range 80.0-100.0)
    "MCH": {"Value": 36.5, "Classification": "High"},  # 36.5 pg (Range 27.0-33.0)
    "MCHC": {"Value": 33.3, "Classification": "Normal"}, # 33.3 g/dL (Range 32.0-36.0)
    "RDW": {"Value": 16.0, "Classification": "High"},  # 16.0 % (Range 11.5-14.5)
    "Platelet": {"Value": 180.0, "Classification": "Normal"}, # 180 K/mcL -> 180 x10^3/uL (Range 150.0-450.0)
}

# --- UTILITY FUNCTIONS ---
def _clean_numeric_string(s: str) -> str:
    """Cleans a string to prepare it for float conversion, taking the first value in a range."""
    if s is None:
        return ""
    s = str(s).replace('<', '').replace('>', '').replace(',', '').strip()
    if '-' in s and len(s.split('-')) == 2:
        return s.split('-')[0].strip()
    return s

def _to_float(v):
    """Safely converts a cleaned string value to a float."""
    try:
        return float(_clean_numeric_string(v))
    except ValueError:
        return None

# --- STAGE 1: DATA EXTRACTION ENGINE ---

def _parse_tables_for_parameters(pdf: pdfplumber.PDF) -> List[Dict[str, str]]:
    """Extracts data from PDF tables using pdfplumber (PRIMARY METHOD with flexible settings)."""
    extracted_data: List[Dict[str, str]] = []
    alias_map = {alias: param_name for param_name, aliases in PARAMETER_ALIASES.items() for alias in aliases}
    
    # Custom table settings to handle non-standard delimiters (like large spaces)
    custom_settings = {
        "vertical_strategy": "text", 
        "horizontal_strategy": "text",
        "snap_tolerance": 5, 
        "join_tolerance": 5, 
    }

    for page in pdf.pages:
        tables_default = page.extract_tables()
        tables_custom = page.extract_tables(custom_settings)
        
        for table in tables_default + tables_custom:
            if not table or len(table) < 2: continue

            header = [str(c).lower().strip() for c in table[0] if c is not None]
            p_col, v_col, u_col = -1, -1, -1
            
            v_col = next((i for i, h in enumerate(header) if any(v in h for v in ["value", "result", "reading"])), -1)
            p_col = next((i for i, h in enumerate(header) if any(p in h for p in ["test", "parameter", "name"])), -1)
            u_col = next((i for i, h in enumerate(header) if any(u in h for u in ["unit", "uom"])), -1)

            if p_col == -1: p_col = 0
            if v_col == -1 and len(header) >= 2 and p_col < len(header) - 1: v_col = p_col + 1
            if v_col == -1 or p_col == v_col: continue

            for row in table[1:]:
                if not row or all(c is None for c in row): continue
                
                try:
                    raw_param_name = str(row[p_col]).strip() if p_col < len(row) and row[p_col] else ""
                    raw_value = str(row[v_col]).strip() if v_col < len(row) and row[v_col] else ""
                    raw_unit = str(row[u_col]).strip() if u_col != -1 and u_col < len(row) and row[u_col] else ""
                    
                    if not raw_param_name or not raw_value or _to_float(raw_value) is None: continue

                    standard_param_name = next(
                        (param for alias, param in alias_map.items() if alias in raw_param_name.lower()),
                        None
                    )
                    
                    if standard_param_name:
                        extracted_data.append({
                            "Parameter": standard_param_name,
                            "Raw_Value": _clean_numeric_string(raw_value),
                            "Raw_Unit": raw_unit,
                        })
                except Exception:
                    continue

    return extracted_data


def _parse_text_for_parameters(text_content: str) -> List[Dict[str, str]]:
    """Search the text for known parameter patterns (FALLBACK METHOD with highly specific matching)."""
    extracted_data: List[Dict[str, str]] = []

    for param_name, pattern in PARAMETER_PATTERNS.items():
        # Find all matches, focusing on Group 2 (value) and Group 3 (unit)
        for match in re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE):
            
            # The value is always the first captured numeric group after the parameter label
            raw_value = match.group(2) if match.lastindex >= 2 else "" 
            raw_unit = ""
            # The unit is the last captured group, which is often group 3
            if match.lastindex >= 3:
                 raw_unit = match.group(match.lastindex) or ""
            
            if _to_float(raw_value) is not None:
                if not any(d['Parameter'] == param_name for d in extracted_data):
                    extracted_data.append({
                        "Parameter": param_name,
                        "Raw_Value": _clean_numeric_string(raw_value).strip(),
                        "Raw_Unit": (raw_unit or "").strip(),
                    })
            
    return extracted_data


def extract_and_parse_data(uploaded_file) -> List[Dict[str, Any]]:
    """
    Manages the extraction pipeline: Table -> Text/Regex -> OCR (fallback).
    """
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    file_obj = io.BytesIO(file_bytes)

    all_raw_data: List[Dict[str, str]] = []
    full_text = ""
    
    # --- STAGE 1: PDF TEXT/TABLE EXTRACTION (Primary - using pdfplumber) ---
    try:
        with pdfplumber.open(file_obj) as pdf:
            all_raw_data.extend(_parse_tables_for_parameters(pdf))
            
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
    except Exception:
        # --- STAGE 1.5: PDF TEXT EXTRACTION (Fallback - using PyMuPDF/fitz) ---
        try:
             doc = fitz.open(stream=file_bytes, filetype="pdf")
             for page_num in range(doc.page_count):
                 page = doc.load_page(page_num)
                 full_text += page.get_text() + "\n"
        except Exception:
            pass 

    # --- STAGE 2: TEXT/REGEX EXTRACTION ---
    raw_text_data = _parse_text_for_parameters(full_text)
    
    # Merge text-extracted data only if the parameter wasn't found by tables
    for item in raw_text_data:
        if not any(d['Parameter'] == item['Parameter'] for d in all_raw_data):
            all_raw_data.append(item)

    # --- STAGE 3: OCR EXTRACTION (Deep Fallback) ---
    if not all_raw_data and uploaded_file.type in ["image/jpeg", "image/png"]:
        try:
             img = Image.open(file_obj)
             ocr_text = pytesseract.image_to_string(img)
             raw_ocr_data = _parse_text_for_parameters(ocr_text)
             all_raw_data.extend(raw_ocr_data)
        except Exception:
            pass 

    if not all_raw_data:
        raise ValueError("No valid key blood parameters were extracted from the report. Please ensure the file is legible.")

    final_raw_data = []
    seen_params = set()
    for item in all_raw_data:
        if item["Parameter"] not in seen_params and _to_float(item.get('Raw_Value')) is not None:
            final_raw_data.append(item)
            seen_params.add(item["Parameter"])
    
    if not final_raw_data:
        raise ValueError("Extraction was successful but yielded no valid numeric data for core parameters.")

    return final_raw_data


# --- STAGE 2: DATA VALIDATION & STANDARDIZATION ---

def validate_and_standardize(raw_data_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Standardizes units and converts raw strings to numeric values."""
    standardized_list: List[Dict[str, Any]] = []

    for item in raw_data_list:
        param = item.get("Parameter")
        raw_val = item.get("Raw_Value", "")
        raw_unit = (item.get("Raw_Unit") or "").strip()

        if not param or param not in REFERENCE_DATABASE:
            continue

        ref_info = REFERENCE_DATABASE[param]
        standard_unit = ref_info["unit"]
        value = _to_float(raw_val)

        if value is None:
            continue
        
        # --- UNIT CONVERSION LOGIC (Comprehensive) ---
        raw_unit_lower = raw_unit.lower().replace(" ", "").replace(",", "")

        if param == "Glucose" and raw_unit_lower in ("mmol/l", "mmol/l"):
            value = value * 18.018
        
        elif param == "Hemoglobin" and raw_unit_lower in ("g/l", "g/l"):
            value = value / 10.0
            
        # WBC: Divide by 1000 if the value is clearly an absolute number (e.g., 4000) or unit is K/mcL
        elif param == "WBC":
            if raw_unit_lower in ("k/mcl", "/mm3", "cells/µl", "cells/ul", "x10^3/ul", "x10e3/ul") and value > 20: # Use 20 as a safer threshold
                value = value / 1000.0
            elif raw_unit_lower in ("k/mcl") and value < 20:
                pass # Already on the correct x10^9/L scale

        # RBC: Convert M/mcL to x10^12/L (They are the same scale) - check for large numbers
        elif param == "RBC" and value > 1000:
            value = value / 1000000.0 # Extreme fallback if reported as absolute millions

        # Platelet: Divide by 1000 if the value is clearly an absolute number (e.g., 150000)
        elif param == "Platelet":
            if raw_unit_lower in ("k/mcl", "/mm3", "cumm", "cells/µl", "cells/ul", "/µl") and value > 1000:
                value = value / 1000.0
            elif raw_unit_lower in ("k/mcl") and value < 1000:
                 pass # Already on the correct x10^3/uL scale

        standardized_list.append({
            "Parameter": param,
            "Value": round(value, 2),
            "Unit": standard_unit,
            "Reference_Range_Min": ref_info["range"][0],
            "Reference_Range_Max": ref_info["range"][1],
            "Raw_Unit_Used": raw_unit or standard_unit,
        })

    return standardized_list


# --- STAGE 3: MODEL 1 (PARAMETER CLASSIFICATION) ---

def classify_parameters(standardized_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compares standardized values against reference ranges to classify them."""
    for item in standardized_data_list:
        value = item.get("Value")
        min_range = item.get("Reference_Range_Min")
        max_range = item.get("Reference_Range_Max")

        classification = "Normal"
        if value is None or min_range is None or max_range is None:
            classification = "Unknown"
        else:
            if value < min_range:
                classification = "Low"
            elif value > max_range:
                classification = "High"

        item["Classification"] = classification
        
        # Placeholder for Milestone 2: Diagnosis/Interpretation
        item["Diagnosis"] = f"Initial finding: {item['Parameter']} is {classification}."

    return standardized_data_list


# --- STAGE 4: ACCURACY METRICS (Milestone 1 Evaluation) ---

def calculate_accuracy_metrics(final_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates extraction and classification accuracy against a hardcoded ground truth
    for the provided CBC-sample-report-with-notes_0.pdf.
    """
    extracted_params = {item["Parameter"]: item for item in final_results}
    
    # 1. Extraction Accuracy
    total_expected = len(GROUND_TRUTH_CORE)
    correctly_extracted = 0
    
    for param_name in GROUND_TRUTH_CORE.keys():
        if param_name in extracted_params:
            correctly_extracted += 1
            
    extraction_accuracy = correctly_extracted / total_expected if total_expected > 0 else 0.0

    # 2. Classification Accuracy (only for successfully extracted core parameters)
    correctly_classified = 0
    total_classified = 0

    for param_name, gt_data in GROUND_TRUTH_CORE.items():
        if param_name in extracted_params and gt_data["Classification"] != "Unknown":
            total_classified += 1
            extracted_classification = extracted_params[param_name]["Classification"]
            
            # Simple check against ground truth classification
            if extracted_classification == gt_data["Classification"]:
                correctly_classified += 1
    
    classification_accuracy = correctly_classified / total_classified if total_classified > 0 else 0.0

    return {
        "Total_Expected_Core_Parameters": total_expected,
        "Total_Extracted_Core_Parameters": correctly_extracted,
        "Extraction_Accuracy": round(extraction_accuracy * 100, 2), # Percentage for easy comparison
        "Classification_Accuracy": round(classification_accuracy * 100, 2), # Percentage
    }

def process_file_full(uploaded_file) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """Convenience wrapper: extract raw -> standardize -> classify -> calculate metrics."""
    raw = extract_and_parse_data(uploaded_file)
    standardized = validate_and_standardize(raw)
    classified = classify_parameters(standardized)
    metrics = calculate_accuracy_metrics(classified)
    return classified, metrics

def run_milestone_2_models(classified_data, age=None, gender=None):
    """
    Runs Model 2 (Pattern Recognition)
    and Model 3 (Contextual Analysis).
    """

    # Model 2
    detected_patterns = model_2_pattern_risk_analysis(classified_data)

    # Model 3 (optional)
    contextual_output = apply_contextual_adjustments(
        detected_patterns,
        age=age,
        gender=gender
    )

    return contextual_output
# In data_processor.py – REPLACE the existing run_milestone_2_models with this:

def run_milestone_2_models(classified_data, age=None, gender=None, smoking=None, family_history=None):
    """
    Runs Model 2 (Pattern Recognition) + Model 3 (Contextual Adjustments) + LLM Reasoning
    """
    # Model 2: Detect raw patterns
    detected_patterns = model_2_pattern_risk_analysis(classified_data)

    # Ensure it's a list
    if not isinstance(detected_patterns, list):
        detected_patterns = []

    # Model 3: Apply contextual adjustments (age, gender, smoking, family history)
    adjusted_patterns = apply_contextual_adjustments(
        detected_patterns,
        age=age,
        gender=gender,
        smoking=smoking,
        family_history=family_history
    )

    # Safety: ensure all are dicts
    safe_patterns = [p for p in adjusted_patterns if isinstance(p, dict)]


    return {
        "patterns": safe_patterns,
        
    }

## In data_processor.py – ADD or REPLACE this function:

def run_milestone_3(classified_data, milestone2_output, age=None, gender=None, smoking=None, family_history=None):
    """
    Milestone 3: Full synthesis and personalized recommendations
    """
    patterns = milestone2_output.get("patterns", [])
    

    summary = synthesize_findings(classified_data, patterns, user_context={"age": age, "gender": gender, "smoking": smoking, "family_history": family_history})
    recommendations = generate_personalized_recommendations(
        patterns,
        age=age,
        gender=gender,
        smoking=smoking,
        family_history=family_history
    )

    return {
        "comprehensive_summary": summary,
        "personalized_recommendations": recommendations
    }

# data_processor.py – ADD this new function

def extract_text_per_page(uploaded_file):
    """
    Extracts text from each page of a PDF and returns a list of (page_num, text)
    Useful for detecting multiple reports in one PDF.
    """
    import pdfplumber
    import io

    pages_text = []

    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text = text.strip()
                else:
                    text = ""
                pages_text.append({
                    "page": i + 1,
                    "text_preview": text[:500] + "..." if len(text) > 500 else text,
                    "full_text": text
                })
    else:
        # For images: treat as single "page"
        pages_text.append({
            "page": 1,
            "text_preview": "Image file – OCR will be applied during full analysis.",
            "full_text": None
        })

    return pages_text