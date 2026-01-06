from typing import List

def recommendations_node(state):
    """
    Rule-based health recommendations derived from detected patterns.
    Deterministic and safe.
    """

    patterns = state.patterns or []
    recommendations = []

    if "Microcytic anemia" in patterns or "Normocytic anemia" in patterns or "Macrocytic anemia" in patterns:
        recommendations.append("Consult a physician for further evaluation of anemia.")
        recommendations.append("Additional blood tests such as iron studies or vitamin levels may be required if advised by a doctor.")

    if "Leukocytosis" in patterns or "Neutrophilia" in patterns:
        recommendations.append("Clinical correlation is advised to rule out infection or inflammation.")

    if "Thrombocytopenia" in patterns:
        recommendations.append("Avoid activities with bleeding risk and consult a healthcare professional promptly.")

    if not recommendations:
        recommendations.append("Maintain a balanced diet, adequate hydration, and routine health checkups.")
        recommendations.append("Seek medical advice if symptoms such as fatigue, fever, or weakness develop.")

    return {
        "recommendations": recommendations
    }
