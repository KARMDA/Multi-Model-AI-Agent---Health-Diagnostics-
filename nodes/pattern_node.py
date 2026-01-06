import json
from utils.llm_utils import get_llm

def pattern_recognition_node(state):
    """
    Model 2: Pattern Recognition & Risk Assessment
    """
    extracted = state.extracted_params
    if not extracted:
        return {
            "patterns": [],
            "risk_assessment": {"score": 0, "rationale": []}
        }

    llm = get_llm()

    prompt = f"""
You are a clinical pattern recognition system.

Based on the following extracted lab parameters:

{extracted}

Identify any clinically relevant patterns.

Return ONLY valid JSON in this format:

{{
  "patterns": ["Pattern 1", "Pattern 2"],
  "risk_score": 5,
  "risk_rationale": ["Reason 1", "Reason 2"]
}}

Rules:
- Patterns should be short phrases
- Risk score must be 0–10
- Rationale should justify the risk score
"""

    try:
        response = llm.invoke(prompt)

        # 🔥 THIS IS THE KEY CHANGE
        data = json.loads(response)

        patterns = data.get("patterns", [])
        risk_score = data.get("risk_score", 0)
        risk_rationale = data.get("risk_rationale", [])

        return {
            "patterns": patterns,
            "risk_assessment": {
                "score": risk_score,
                "rationale": risk_rationale
            }
        }

    except Exception as e:
        return {
            "patterns": [],
            "risk_assessment": {"score": 0, "rationale": []},
            "errors": state.errors + [f"Model 2 (Patterns) failed: {str(e)}"]
        }
