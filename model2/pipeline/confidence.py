# model2/pipeline/confidence.py
"""
Combine several signals into an overall confidence for the model2 output.
Signals:
- proportion of parameters present vs expected
- severity weight of detected patterns
- KG top candidate strength
This is a simple, explainable aggregator.
"""

from typing import Dict, Any, List

def compute_confidence(
    params: Dict[str, Any],
    patterns: Dict[str, Any],
    probable_causes: Dict[str, Any],
    missing_params: List[str]
) -> Dict[str, Any]:

    presence_score = _parameter_presence_score(params)
    pattern_score = _pattern_strength(patterns)
    kg_score = _kg_top_score(probable_causes)

    # weighted sum (do NOT change)
    score = round(0.4 * presence_score + 0.4 * pattern_score + 0.2 * kg_score, 3)

    return {
        "score": score,
        "components": {
            "presence": presence_score,
            "pattern": pattern_score,
            "kg": kg_score
        },
        "explanation": build_confidence_explanation(
            presence_score,
            pattern_score,
            missing_params
        )
    }


def _parameter_presence_score(params: Dict[str, Any]) -> float:
    IGNORED = {"age", "gender", "patient_id", "filename", "report_date"}

    total = 0
    present = 0

    for k, v in params.items():
        if k in IGNORED:
            continue
        total += 1
        if v is not None:
            present += 1

    if total == 0:
        return 0.0

    return round(min(1.0, present / total), 3)


def _pattern_strength(patterns: Dict[str, Any]) -> float:
    p = patterns.get("patterns", {})
    if not p:
        return 0.0

    weight = 0.0
    count = 0

    for _, info in p.items():
        if info.get("present"):
            count += 1
            sev = info.get("severity", "")
            if sev and ("severe" in sev):
                weight += 1.0
            else:
                weight += 0.5

    if count == 0:
        return 0.0

    return round(min(1.0, weight / count), 3)


def _kg_top_score(probable_causes: Dict[str, Any]) -> float:
    causes = probable_causes.get("causes", [])
    if not causes:
        return 0.0
    return float(causes[0].get("score", 0.0))


def build_confidence_explanation(
    presence: float,
    pattern: float,
    missing_params: List[str]
) -> str:

    reasons = []

    if presence < 0.5:
        reasons.append(
            "several relevant laboratory parameters are missing, limiting diagnostic certainty"
        )

    if pattern < 0.7:
        reasons.append(
            "some detected patterns overlap or lack confirmatory markers"
        )

    if missing_params:
        reasons.append(
            "missing parameters include: "
            + ", ".join(missing_params[:6])
            + ("..." if len(missing_params) > 6 else "")
        )

    if not reasons:
        return "High confidence due to complete and consistent laboratory evidence."

    return "Moderate confidence because " + "; ".join(reasons) + "."
