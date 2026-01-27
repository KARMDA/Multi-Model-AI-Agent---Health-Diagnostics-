# model2_pattern.py
"""
Model 2: Pattern Recognition & Risk Assessment
Expanded with research-based patterns from CBC (e.g., NIH/Mayo sources).
Includes calculations (NLR, ANC) and simple CVD risk proxy.
"""

import numpy as np

# Expanded from research: anemia subtypes, infections via differentials, dyslipidemia, etc.
PATTERN_RULES = {
    "Anemia (General)": {
        "conditions_any": {"Hemoglobin": "Low", "RBC": "Low", "PCV": "Low"},
        "risk_score_base": 0.6,
        "description": "Low hemoglobin/RBC/hematocrit suggests anemia — common causes include iron deficiency, vitamin B12/folate deficiency, or chronic disease (NIH)."
    },
    "Microcytic Anemia": {
        "conditions_all": {"Hemoglobin": "Low", "MCV": "Low"},
        "risk_score_base": 0.8,
        "description": "Low MCV with anemia typically indicates iron deficiency or thalassemia (Cleveland Clinic)."
    },
    "Macrocytic Anemia": {
        "conditions_all": {"Hemoglobin": "Low", "MCV": "High"},
        "risk_score_base": 0.8,
        "description": "High MCV with anemia often due to B12/folate deficiency, liver disease, or alcohol use (Mayo Clinic)."
    },
    "Normocytic Anemia": {
        "conditions_all": {"Hemoglobin": "Low", "MCV": "Normal"},
        "risk_score_base": 0.7,
        "description": "Normal MCV anemia may suggest chronic disease, kidney issues, or acute blood loss (NCBI)."
    },
    "Polycythemia": {
        "conditions_any": {"Hemoglobin": "High", "RBC": "High", "PCV": "High"},
        "risk_score_base": 0.7,
        "description": "High red cell counts may be due to dehydration, smoking, or polycythemia vera — increases clot risk (NIH)."
    },
    "Leukocytosis": {
        "conditions_any": {"WBC": "High"},
        "risk_score_base": 0.7,
        "description": "High white blood cells often indicate infection, inflammation, or stress (Mayo Clinic)."
    },
    "Leukopenia": {
        "conditions_any": {"WBC": "Low"},
        "risk_score_base": 0.7,
        "description": "Low white cells can increase infection risk — may be from viral illness or medications (Cleveland Clinic)."
    },
    "Neutrophilia (Bacterial Infection Suspected)": {
        "conditions_any": {"Neutrophils": "High"},
        "risk_score_base": 0.75,
        "description": "Elevated neutrophils commonly seen in bacterial infections or acute stress."
    },
    "Lymphocytosis (Viral Infection Suspected)": {
        "conditions_any": {"Lymphocytes": "High"},
        "risk_score_base": 0.7,
        "description": "High lymphocytes often associated with viral infections or chronic conditions."
    },
    "Eosinophilia (Allergy/Parasite)": {
        "conditions_any": {"Eosinophils": "High"},
        "risk_score_base": 0.6,
        "description": "Elevated eosinophils frequently linked to allergies, asthma, or parasitic infections."
    },
    "Thrombocytopenia": {
        "conditions_any": {"Platelet": "Low"},
        "risk_score_base": 0.7,
        "description": "Low platelets increase bleeding risk — causes include immune disorders or medications."
    },
    "Thrombocytosis": {
        "conditions_any": {"Platelet": "High"},
        "risk_score_base": 0.7,
        "description": "High platelets can raise clotting risk — often due to inflammation or iron deficiency."
    },
    "Pancytopenia": {
        "conditions_all": {"RBC": "Low", "WBC": "Low", "Platelet": "Low"},
        "risk_score_base": 0.9,
        "description": "Low counts in all three lines may indicate bone marrow suppression — requires urgent evaluation."
    },
    "Hyperglycemia": {
        "conditions_any": {"Glucose": "High"},
        "risk_score_base": 0.8,
        "description": "High blood glucose may suggest diabetes or prediabetes (ADA guidelines)."
    },
    "Dyslipidemia": {
        "conditions_any": {"Cholesterol": "High"},
        "risk_score_base": 0.75,
        "description": "Elevated cholesterol increases cardiovascular risk (AHA)."
    },
    "Dehydration Suspected": {
        "conditions_any": {"Hemoglobin": "High", "PCV": "High"},
        "risk_score_base": 0.6,
        "description": "Concentrated blood values can indicate dehydration."
    },
    "Inflammation Marker": {
        "conditions_any": {"RDW": "High", "Monocyte": "High"},
        "risk_score_base": 0.7,
        "description": "High RDW and monocytes can be markers of ongoing inflammation."
    },
    "Cardiovascular Risk Combination": {
        "conditions_any": {"Cholesterol": "High", "Glucose": "High", "Hemoglobin": "Low"},
        "risk_score_base": 0.85,
        "description": "Combination of high cholesterol/glucose and low hemoglobin significantly raises heart disease risk (AHA/PMC studies)."
    },
    "Prediabetes": {
        "conditions_all": {"Fasting Glucose": "High"},
        "risk_score_base": 0.6,
        "description": "Elevated fasting glucose suggests prediabetic state."
    },

    "Diabetes Suspected": {
        "conditions_all": {"HbA1c": "High"},
        "risk_score_base": 0.8,
        "description": "High HbA1c indicates poor long-term glucose control."
    },
    "Hypercholesterolemia": {
        "conditions_any": {"Total Cholesterol": "High", "LDL": "High"},
        "risk_score_base": 0.7,
        "description": "Elevated cholesterol levels increase cardiovascular risk."
    },

    "Low HDL Risk": {
        "conditions_all": {"HDL": "Low"},
        "risk_score_base": 0.6,
        "description": "Low HDL reduces protective effect against heart disease."
    },
    "Renal Dysfunction Suspected": {
        "conditions_any": {"Creatinine": "High", "Urea": "High"},
        "risk_score_base": 0.8,
        "description": "Elevated kidney markers suggest impaired renal function."
    },
    "Hepatic Injury Pattern": {
        "conditions_any": {"SGOT": "High", "SGPT": "High"},
        "risk_score_base": 0.75,
        "description": "Elevated liver enzymes suggest liver inflammation or injury."
    },

    "Cholestasis Pattern": {
        "conditions_all": {"ALP": "High", "Total Bilirubin": "High"},
        "risk_score_base": 0.7,
        "description": "Raised ALP and bilirubin may indicate bile flow obstruction."
    },
    "Hypothyroidism Suspected": {
        "conditions_all": {"TSH": "High"},
        "risk_score_base": 0.75,
        "description": "Elevated TSH suggests reduced thyroid hormone production."
    },

    "Hyperthyroidism Suspected": {
        "conditions_all": {"TSH": "Low"},
        "risk_score_base": 0.75,
        "description": "Low TSH may indicate excess thyroid hormone levels."
    },
    "Hyponatremia": {
        "conditions_all": {"Sodium": "Low"},
        "risk_score_base": 0.7,
        "description": "Low sodium levels may affect neurological and cardiac function."
    },

    "Hyperkalemia": {
        "conditions_all": {"Potassium": "High"},
        "risk_score_base": 0.8,
        "description": "High potassium can cause dangerous heart rhythm disturbances."
    },
    "Iron Deficiency Pattern": {
        "conditions_any": {"Serum Iron": "Low", "Ferritin": "Low"},
        "risk_score_base": 0.75,
        "description": "Low iron stores suggest iron deficiency anemia risk."
    },

    "Hypercalcemia": {
        "conditions_all": {"Calcium": "High"},
        "risk_score_base": 0.7,
        "description": "Elevated calcium may indicate parathyroid or metabolic disorder."
    },
    


}

def model_2_pattern_risk_analysis(classified_data):
    """
    Detects patterns with dynamic scoring and calculations.
    """
    # Maps for status, values, ranges
    param_status = {item.get("Parameter", ""): item.get("Classification", "") for item in classified_data}
    param_values = {item.get("Parameter", ""): item.get("Value", None) for item in classified_data}
    param_ranges = {item.get("Parameter", ""): (item.get("Reference_Range_Min", 0), item.get("Reference_Range_Max", 0)) for item in classified_data}

    detected_patterns = []

    for pattern_name, rule in PATTERN_RULES.items():
        matched = False

        if "conditions_all" in rule:
            matched = all(param_status.get(param, "") == expected for param, expected in rule.get("conditions_all", {}).items())
        if not matched and "conditions_any" in rule:
            matched = any(param_status.get(param, "") == expected for param, expected in rule.get("conditions_any", {}).items())

        if matched:
            risk_score = rule["risk_score_base"]
            # Dynamic adjustment: add 0.1 per param deviation >10%
            for param in {**rule.get("conditions_all", {}), **rule.get("conditions_any", {})}:
                val = param_values.get(param)
                if val is not None:
                    min_r, max_r = param_ranges.get(param, (0, 100))
                    if max_r > min_r:  # Avoid div zero
                        deviation = max(0, (val - max_r) / (max_r - min_r) if val > max_r else (min_r - val) / (max_r - min_r) if val < min_r else 0)
                        risk_score += deviation * 0.2  # Stronger adjustment

            risk_score = min(risk_score, 1.0)

            # Calculations for infection/inflammation
            calc_notes = []
            if "Infection" in pattern_name or "Inflammation" in pattern_name or "Leuk" in pattern_name:
                if "Neutrophils" in param_values and "Lymphocytes" in param_values:
                    n = param_values["Neutrophils"]
                    l = param_values["Lymphocytes"]
                    if l != 0:
                        nlr = n / l
                        calc_notes.append(f"Neutrophil-Lymphocyte Ratio (NLR): {nlr:.2f} (elevated if >3, suggests inflammation; NCBI).")
                        if nlr > 3:
                            risk_score += 0.1

                # ANC: If neutrophils % (unit "%"), estimate absolute = (neut % /100) * WBC
                if "Neutrophils" in param_values and "WBC" in param_values:
                    unit_n = REFERENCE_DATABASE.get("Neutrophils", {}).get("unit", "")
                    n = param_values["Neutrophils"]
                    wbc = param_values["WBC"]
                    if "%" in unit_n:
                        anc = (n / 100) * wbc
                        calc_notes.append(f"Estimated Absolute Neutrophil Count (ANC): {anc:.2f} x10^9/L (normal 1.5-8.0; low risks infection).")
                        if anc < 1.5:
                            risk_score += 0.1

            detected_patterns.append({
                "Pattern": pattern_name,
                "Risk_Score": round(risk_score, 2),
                "Description": rule["description"],
                "Calc_Notes": calc_notes if calc_notes else []
            })

    return detected_patterns
