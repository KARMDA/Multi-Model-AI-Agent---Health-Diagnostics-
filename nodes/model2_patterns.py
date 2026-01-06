def model2_patterns_node(state):
    """
    Rule-based clinical pattern recognition for CBC reports.
    Deterministic, explainable, no LLM dependency.
    """

    validated = state.validated_params or {}

    patterns = []
    rationale = []

    # Extract validated values safely
    hb = validated.get("Hemoglobin", {}).get("value")
    mcv = validated.get("MCV", {}).get("value")
    wbc = validated.get("Total WBC count", {}).get("value")
    neut = validated.get("Neutrophils", {}).get("value")
    lymph = validated.get("Lymphocytes", {}).get("value")
    platelets = validated.get("Platelet Count", {}).get("value")

    # ---- Anemia patterns ----
    if hb is not None and hb < 12:
        if mcv is not None:
            if mcv < 80:
                patterns.append("Microcytic anemia")
                rationale.append("Low hemoglobin with low MCV")
            elif mcv > 100:
                patterns.append("Macrocytic anemia")
                rationale.append("Low hemoglobin with high MCV")
            else:
                patterns.append("Normocytic anemia")
                rationale.append("Low hemoglobin with normal MCV")
        else:
            patterns.append("Anemia")
            rationale.append("Low hemoglobin detected")

    # ---- Infection / inflammation ----
    if wbc is not None and wbc > 11000:
        patterns.append("Leukocytosis")
        rationale.append("Elevated total WBC count")

    if neut is not None and neut > 75:
        patterns.append("Neutrophilia")
        rationale.append("High neutrophil percentage")

    if lymph is not None and lymph > 40:
        patterns.append("Lymphocytosis")
        rationale.append("High lymphocyte percentage")

    # ---- Platelet disorders ----
    if platelets is not None and platelets < 150000:
        patterns.append("Thrombocytopenia")
        rationale.append("Low platelet count")

    # ---- Risk scoring ----
    risk_score = min(len(patterns) * 2, 10)

    if not patterns:
        rationale = [
        "All evaluated CBC parameters fall within expected reference ranges",
        "No clinically significant hematologic abnormalities detected"
        ]


    return {
        "patterns": patterns,
        "risk_assessment": {
            "score": risk_score,
            "rationale": rationale
        }
    }
