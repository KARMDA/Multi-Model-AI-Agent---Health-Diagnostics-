# milestone3_synthesis.py

def synthesize_findings(model1_output, milestone2_output):
    """
    Convert technical model outputs into a clear human-readable summary.
    This is the Findings Synthesis Engine (Milestone 3).
    """

    summary_points = []

    # ---- Model 1 (Individual parameters) ----
    for param, info in model1_output.items():
        status = info.get("status", "").lower()
        value = info.get("value")

        if status != "normal":
            summary_points.append(
                f"{param} is {status} with a value of {value}."
            )

    # ---- Model 2 & 3 (Patterns + Context) ----
    patterns = milestone2_output.get("identified_patterns", [])
    contextual = milestone2_output.get("contextual_insights", [])

    if patterns:
        summary_points.append(
            "Identified clinical patterns include: " + ", ".join(patterns) + "."
        )

    for insight in contextual:
        summary_points.append(insight)

    if not summary_points:
        summary_points.append(
            "All analyzed blood parameters appear to be within normal limits."
        )

    return " ".join(summary_points)


def generate_recommendations(summary_text, age=None, gender=None):
    """
    Generate short, safe, actionable recommendations based on synthesized findings.
    This simulates short prompting behavior.
    """

    recommendations = []

    summary_lower = summary_text.lower()

    # ---- Anemia / Hemoglobin ----
    if "hemoglobin" in summary_lower or "anemia" in summary_lower:
        recommendations.extend([
            "Include iron-rich foods such as leafy greens, lentils, and dates.",
            "Avoid skipping meals and maintain a balanced diet.",
            "Consult a healthcare professional if fatigue or weakness persists."
        ])

    # ---- Platelets ----
    if "platelet" in summary_lower:
        recommendations.extend([
            "Stay well hydrated throughout the day.",
            "Avoid smoking and excessive alcohol consumption.",
            "Follow up with a doctor if unusual bruising or clotting occurs."
        ])

    # ---- Infection / WBC ----
    if "wbc" in summary_lower or "infection" in summary_lower:
        recommendations.extend([
            "Ensure adequate rest and hydration.",
            "Monitor for fever or signs of infection.",
            "Seek medical advice if symptoms worsen."
        ])

    # ---- Age-based advice ----
    if age and age > 45:
        recommendations.append(
            "Regular health check-ups are recommended due to increased age-related risks."
        )

    # ---- Gender-based advice ----
    if gender and gender.lower() == "female":
        recommendations.append(
            "Ensure adequate iron and calcium intake as nutritional needs may be higher."
        )

    # ---- Default fallback ----
    if not recommendations:
        recommendations.append(
            "Maintain a healthy lifestyle with a balanced diet and regular physical activity."
        )

    return list(dict.fromkeys(recommendations))  # remove duplicates
