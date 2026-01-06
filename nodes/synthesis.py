from utils.llm_utils import get_llm

def synthesis_node(state):
    params = state.param_interpretation or {}
    patterns = state.patterns or []

    if not params:
        return {"synthesis_report": "No laboratory data available for synthesis."}

    lines = ["CBC Summary Report:\n"]

    for name, info in params.items():
        val = info.get("value")
        unit = info.get("unit", "")
        status = info.get("status", "unknown")
        lines.append(f"- {name}: {val} {unit} ({status})")

    if patterns:
        lines.append("\nIdentified Patterns:")
        for p in patterns:
            lines.append(f"- {p}")

    lines.append("\nClinical correlation is advised.")

    return {"synthesis_report": "\n".join(lines)}
