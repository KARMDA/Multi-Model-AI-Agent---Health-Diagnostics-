# model2_pattern.py

def pattern_risk_analysis(data: dict):
    risks = []

    hb = data.get("Hemoglobin")
    rbc = data.get("RBC")
    wbc = data.get("WBC")
    platelets = data.get("Platelets")
    neut = data.get("Neutrophils")
    lymph = data.get("Lymphocytes")
    mchc = data.get("MCHC")

    # Hemoglobin analysis
    if hb is not None:
        if hb < 12:
            risks.append("Low hemoglobin - possible anemia")
        elif hb > 16:
            risks.append("High hemoglobin - possible dehydration or polycythemia")
        else:
            risks.append("Hemoglobin within normal range")

    # WBC analysis
    if wbc is not None:
        if wbc < 4000:
            risks.append("Low WBC count - possible immunosuppression")
        elif wbc > 11000:
            risks.append("High WBC count - possible infection or inflammation")
        else:
            risks.append("WBC count within normal range")

    # Platelet analysis
    if platelets is not None:
        if platelets < 150000:
            risks.append("Low platelet count - bleeding risk")
        elif platelets > 450000:
            risks.append("High platelet count - thrombosis risk")
        else:
            risks.append("Platelet count within normal range")

    # Differential analysis
    if neut is not None and lymph is not None:
        if neut > 75 and lymph < 20:
            risks.append("Neutrophilia with lymphopenia - possible infection or stress response")
        elif neut < 50 and lymph > 40:
            risks.append("Neutropenia with lymphocytosis - possible viral infection")

    # MCHC analysis
    if mchc is not None:
        if mchc > 35:
            risks.append("High MCHC - possible dehydration or RBC membrane disorder")
        elif mchc < 32:
            risks.append("Low MCHC - possible iron deficiency or thalassemia")
        else:
            risks.append("MCHC within normal range")

    # If no specific risks, add general assessment
    if not risks:
        risks.append("All parameters appear within normal ranges")

    return risks

def detect_patterns(data):
    patterns = []

    if data.get("Hemoglobin", 100) < 13:
     patterns.append("Low hemoglobin (possible mild anemia)")

    if data.get("PCV", 0) > 50:
      patterns.append("High PCV (possible dehydration or hemoconcentration)")

    if 150000 <= data.get("Platelets", 0) <= 180000:
     patterns.append("Borderline platelet count")


    return patterns
