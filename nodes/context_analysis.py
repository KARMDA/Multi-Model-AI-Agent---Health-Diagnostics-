def context_analysis_node(state):
    params = state.param_interpretation or {}
    patterns = state.patterns or []

    if not params:
        return {
            "context_analysis": {
                "analysis": "No laboratory data available for contextual analysis.",
                "adjusted_concerns": "Insufficient data."
            }
        }

    if not patterns:
        return {
            "context_analysis": {
                "analysis": (
                    "The reported CBC parameters are within typical adult reference ranges. "
                    "No overt anemia, infection, or hematological abnormality is suggested "
                    "by the available values."
                ),
                "adjusted_concerns": (
                    "Clinical interpretation should still consider patient age, sex, "
                    "symptoms, medications, and comorbid conditions."
                )
            }
        }

    return {
        "context_analysis": {
            "analysis": (
                "Certain CBC parameters show deviations from reference ranges, which may "
                "warrant further clinical correlation."
            ),
            "adjusted_concerns": "; ".join(patterns)
        }
    }
