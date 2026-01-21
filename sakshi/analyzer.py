# analyzer.py

from model2_pattern import detect_patterns
from model3_context import contextualize_patterns

def run_milestone2(clean_data, age=None, gender=None):
    patterns = detect_patterns(clean_data)

    contextual_insights = []
    if age and gender:
        contextual_insights = contextualize_patterns(
            patterns,
            age,
            gender
        )

    return {
        "identified_patterns": patterns,
        "contextual_insights": contextual_insights
    }
