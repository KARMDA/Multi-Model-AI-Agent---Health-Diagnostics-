# model2/pipeline/probable_causes.py
"""
Combine deterministic observations and KG inference to produce ranked probable causes.
Outputs structured list of causes with:
- score (0-1)
- supporting_evidence (list of observation -> edge -> target strings)
- source (kg|rule)
"""

from typing import Dict, Any, List, Tuple
from .knowledge_graph import KnowledgeGraph, build_medical_kg

def infer_probable_causes(observations: List[str], pattern_details: Dict[str,Any], priors: Dict[str,float]=None) -> Dict[str,Any]:
    """
    observations: list of observation node names e.g., ["Hemoglobin_LOW","MCV_LOW","Platelets_LOW"]
    pattern_details: patterns detected by pattern_engine (optional; used to boost or reduce candidate scores)
    priors: base prior weights for causes (optional)
    returns:
      {
        "causes": [
          {"cause": "Iron_Deficiency", "score":0.78, "support": ["MCV_LOW->possible_cause->Iron_Deficiency"], "source":"kg"}
        ],
        "raw_scores": {...}
      }
    """
    kg: KnowledgeGraph = build_medical_kg()
    kg_scores = kg.infer_causes(observations)  # candidate -> score

    # incorporate priors if given
    if priors is None:
        priors = {}

    combined: Dict[str, float] = {}
    support: Dict[str, List[str]] = {}

    for obs in observations:
        edges = kg.query(obs)
        for e in edges:
            targ = e["target"]
            w = e["weight"]
            # base = max(existing, w)
            # NEW aggregation: sum evidence with damping, cap at 1.0
            existing = combined.get(targ, 0.0)
            combined[targ] = min(1.0, existing + (w * 0.8))

            support.setdefault(targ, []).append(f"{obs}->{e['relation']}->{targ}")

    # multiply by priors (simple fusion)
    for c in list(combined.keys()):
        p = priors.get(c, 0.0)
        # fused = combined* (1 + prior) / 2 (simple)
        fused = combined[c] * (1.0 + p)
        combined[c] = min(round(fused, 3), 1.0)

    # normalize relative to max
    mx = max(combined.values()) if combined else 0.0
    if mx > 0:
        for k in combined:
            combined[k] = round(combined[k] / mx, 3)

    # prepare sorted list
    sorted_causes = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)
    causes_out = []
    for cause, score in sorted_causes:
        causes_out.append({
            "cause": cause,
            "score": score,
            "support": support.get(cause, []),
            "source": "kg"
        })

    return {"causes": causes_out, "raw_scores": combined}
