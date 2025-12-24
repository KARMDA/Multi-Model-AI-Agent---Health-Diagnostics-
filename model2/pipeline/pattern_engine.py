# model2/pipeline/pattern_engine.py
"""
Pattern detection using deterministic rules.
Uses:
- severity.label_from_range to detect low/high states
- simple rules to detect patterns (isolated thrombocytopenia, microcytic anemia, macrocytic anemia, neutrophilia, lymphocytosis, dyslipidemia, metabolic syndrome signals)
"""

from typing import Dict, Any, List
from .severity import label_from_range

def detect_patterns(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
    {
      "patterns": {
         "anemia": {"present": True, "type": "microcytic", "support": ["Hemoglobin_LOW", "MCV_LOW"]},
         "thrombocytopenia": {"present": True, "isolated": True, ...}
         ...
      }
    }
    """
    patterns = {}
    age = params.get("age")
    gender = params.get("gender")

    # compute labels for core CBC metrics
    hb = label_from_range("Hemoglobin", params.get("Hemoglobin"), age=age, gender=gender)
    mcv = label_from_range("MCV", params.get("MCV"), age=age, gender=gender)
    rdw = label_from_range("RDW", params.get("RDW"), age=age, gender=gender)
    plate = label_from_range("Platelets", params.get("Platelets"), age=age, gender=gender)
    neut = label_from_range("Neutrophils", params.get("Neutrophils"), age=age, gender=gender)
    lymph = label_from_range("Lymphocytes", params.get("Lymphocytes"), age=age, gender=gender)

    # Anemia detection
    anemia_present = hb["label"].startswith("low") or hb["label"].startswith("very_severe") or hb["label"] in ("severe_low","very_severe_low")
    anemia_type = None
    support = []
    if anemia_present:
        support.append("Hemoglobin_LOW")
        if mcv["label"].startswith("low"):
            anemia_type = "microcytic"
            support.append("MCV_LOW")
        elif mcv["label"].startswith("high"):
            anemia_type = "macrocytic"
            support.append("MCV_HIGH")
        else:
            anemia_type = "normocytic"
        # RDW can help interpret iron deficiency vs mixed
        if rdw["label"].startswith("high"):
            support.append("RDW_HIGH")

    patterns["anemia"] = {"present": anemia_present, "type": anemia_type, "support": support, "severity": hb["label"], "note": hb["note"]}

    # Thrombocytopenia
    thromb_present = plate["label"].startswith("low") or plate["label"] in ("severe_low","very_severe_low")
    # isolated vs part of pancytopenia: check WBC and Hemoglobin not low
    wbc = label_from_range("WBC", params.get("WBC"), age=age, gender=gender)
    is_isolated = thromb_present and not (wbc["label"].startswith("low") or anemia_present)
    patterns["thrombocytopenia"] = {"present": thromb_present, "isolated": is_isolated, "severity": plate["label"], "support": ["Platelets_LOW"] if thromb_present else [] }

    # Neutrophilia / lymphocytosis (infection indicators)
    patterns["neutrophilia"] = {"present": neut["label"].startswith("high"), "severity": neut["label"], "support": ["Neutrophils_HIGH"] if neut["label"].startswith("high") else []}
    patterns["lymphocytosis"] = {"present": lymph["label"].startswith("high"), "severity": lymph["label"], "support": ["Lymphocytes_HIGH"] if lymph["label"].startswith("high") else []}

    # Dyslipidemia: rely on cholesterol and HDL/TG
    tc_label = label_from_range("Total_Cholesterol", params.get("Total_Cholesterol"))
    ldl_label = label_from_range("LDL", params.get("LDL"))
    tg_label = label_from_range("Triglycerides", params.get("Triglycerides"))
    dyslipid = False
    dys_support=[]
    if tc_label["label"].startswith("high") or ldl_label["label"].startswith("high") or tg_label["label"].startswith("high"):
        dyslipid = True
        if tc_label["label"].startswith("high"):
            dys_support.append("Total_Cholesterol_HIGH")
        if ldl_label["label"].startswith("high"):
            dys_support.append("LDL_HIGH")
        if tg_label["label"].startswith("high"):
            dys_support.append("Triglycerides_HIGH")
    patterns["dyslipidemia"] = {"present": dyslipid, "support": dys_support, "details": {"tc": tc_label, "ldl": ldl_label, "tg": tg_label}}

    # Metabolic syndrome signals: high TG, low HDL, high fasting glucose or HbA1c
    glucose = params.get("Glucose_Fasting")
    hba1c = params.get("HbA1c")
    metabolic_signs = False
    metab_support = []
    if tg_label["label"].startswith("high") or (label_from_range("HDL", params.get("HDL"))["label"].startswith("low")):
        metabolic_signs = True
        metab_support.append("TG_HIGH_or_HDL_LOW")
    if (hba1c and float(hba1c) >= 5.7) or (glucose and float(glucose) >= 100):
        metabolic_signs = True
        metab_support.append("Glucose_pre-diabetes_or_hyperglycemia")
    patterns["metabolic_syndrome_signals"] = {"present": metabolic_signs, "support": metab_support}

    return {"patterns": patterns}
