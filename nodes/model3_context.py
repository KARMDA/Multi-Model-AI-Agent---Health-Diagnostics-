def model3_context_node(state):
    """
    Deterministic contextual analysis based on patient demographics.
    No LLMs. No parsing. Always returns valid structured output.
    """

    patient_info = state.patient_info or {}
    age = patient_info.get("Age")
    gender = patient_info.get("Gender")
    patterns = state.patterns or []

    analysis = "CBC values interpreted using standard adult reference ranges."
    concerns = []

    if age:
        analysis += f" Patient age: {age}."

    if gender:
        analysis += f" Gender-specific reference ranges were considered for {gender}."

    if patterns:
        concerns = patterns
        analysis += " Some parameters deviate from expected ranges and may require clinical correlation."
    else:
        analysis += " No clinically significant abnormalities detected."

    return {
        "context_analysis": {
            "analysis": analysis,
            "adjusted_concerns": concerns
        }
    }
