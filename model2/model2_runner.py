# model2/model2_runner.py
"""
Orchestrator for Model-2 pipeline.
Usage:
    python model2_runner.py --input path/to/clean_00001.model1_final.csv --output_dir ./outputs
Produces:
  - model2_outputs/<basename>.model2.json
  - model2_outputs/<basename>.model2.txt
  - copies the raw input into model2_outputs/raw_input_<basename>.csv (traceability)
"""

import argparse
import os
import json
import logging
import shutil
from typing import Dict, Any

from pipeline.loader import load_input
from pipeline.pattern_engine import detect_patterns
from pipeline.risk_engine import compute_derived, cardio_risk_band
from pipeline.severity import label_from_range
from pipeline.probable_causes import infer_probable_causes
from pipeline.confidence import compute_confidence
from pipeline.guardrails import sanitize_output
from pipeline.priors import BASE_PRIORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model2_runner")

META_IGNORE = {"age", "gender", "patient_id", "filename", "report_date"}

def run(input_path: str, output_dir: str):
    try:
        os.makedirs(output_dir, exist_ok=True)
        model2_dir = os.path.join(output_dir, "model2_outputs")
        os.makedirs(model2_dir, exist_ok=True)

        base = os.path.basename(input_path)
        base_noext = os.path.splitext(base)[0]

        # copy raw input into model2_outputs for traceability
        try:
            shutil.copy2(input_path, os.path.join(model2_dir, f"raw_input_{base}"))
        except Exception:
            logger.debug("Could not copy raw input (maybe input is inside container). Continuing.")

        # load and get structured dict
        model1_struct = load_input(input_path)
        logger.info(f"Loaded model1 structured keys: {list(model1_struct.keys())}")

        # build flat params for downstream modules (these expect param-name keys)
        flat_params: Dict[str, Any] = {}
        flat_params.update(model1_struct.get("parameters", {}) or {})
        # attach age/gender if present (downstream may use)
        if "age" in model1_struct:
            flat_params["age"] = model1_struct.get("age")
        if "gender" in model1_struct:
            flat_params["gender"] = model1_struct.get("gender")

        # compute missing params (only expected numeric param keys)
        missing_params = [k for k, v in (model1_struct.get("parameters") or {}).items() if v is None]

        # 1. Derived metrics (use flat_params)
        derived = compute_derived(flat_params)

        # 2. Patterns detection
        patterns = detect_patterns(flat_params)

        # 3. Probable causes using KG
        observations = []
        # convert pattern supports into observation nodes for KG
        for pname, pinfo in patterns.get("patterns", {}).items():
            if pinfo.get("present"):
                observations.extend(pinfo.get("support", []))

        # prefer Model-1 status flags when available
        status_map = model1_struct.get("status", {}) or {}
        key_params = ("Hemoglobin", "Platelets", "MCV", "RDW", "LDL", "Total_Cholesterol",
                      "Triglycerides", "HDL", "Creatinine", "CRP", "Glucose_Fasting", "HbA1c",
                      "Neutrophils", "Lymphocytes")

        for param in key_params:
            st = status_map.get(param)
            if st:
                st_up = str(st).upper()
                if "LOW" in st_up:
                    observations.append(f"{param}_LOW")
                elif "HIGH" in st_up:
                    observations.append(f"{param}_HIGH")
            else:
                # fallback to lightweight label_from_range only if no status
                val = flat_params.get(param)
                if isinstance(val, (int, float)):
                    lab_label = label_from_range(param, val, age=flat_params.get("age"), gender=flat_params.get("gender"))
                    lbl = lab_label.get("label", "")
                    if isinstance(lbl, str) and (lbl.startswith("low") or lbl.startswith("high") or "severe" in lbl):
                        node = f"{param}_LOW" if lbl.startswith("low") else f"{param}_HIGH"
                        observations.append(node)

        probable = infer_probable_causes(observations, patterns, priors=BASE_PRIORS)

        # 4. Cardio risk
        cardio = cardio_risk_band(flat_params, derived)

        # 5. Severity per numeric parameter only
        severity_map = {}
        for param, val in (model1_struct.get("parameters") or {}).items():
            if isinstance(val, (int, float)):
                severity_map[param] = label_from_range(param, val, age=flat_params.get("age"), gender=flat_params.get("gender"))

        # 6. Confidence
        confidence = compute_confidence(flat_params, patterns, probable, missing_params)

        # 7. Assemble final structured output
        output = {
            "metadata": {"input_file": input_path, "base": base_noext},
            "parameters": model1_struct.get("parameters", {}),
            "status": model1_struct.get("status", {}),
            "notes": model1_struct.get("notes", {}),
            "derived": derived,
            "patterns": patterns,
            "probable_causes": probable,
            "cardio": cardio,
            "severity": severity_map,
            "confidence": confidence,
            "notes": "Model-2 deterministic + KG reasoning. This output is not a diagnosis. Refer to clinician.",
        }

        # 8. Sanitize
        safe_output = sanitize_output(output)

        # 9. Persist outputs inside model2_outputs
        out_json_path = os.path.join(model2_dir, base_noext + ".model2.json")
        out_txt_path = os.path.join(model2_dir, base_noext + ".model2.txt")
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump(safe_output, f, indent=2, ensure_ascii=False)
        with open(out_txt_path, "w", encoding="utf-8") as f:
            f.write(human_summary(safe_output))

        logger.info(f"Model-2 outputs written: {out_json_path}, {out_txt_path}")
        return safe_output

    except Exception as e:
        logger.exception("Model-2 run failed")
        with open(os.path.join(output_dir, "error_log.txt"), "a", encoding="utf-8") as ef:
            ef.write(f"INPUT: {input_path}\nERROR: {str(e)}\n\n")
        raise

def human_summary(out: dict) -> str:
    lines = []
    md = out.get("metadata", {})
    lines.append(f"Report: {md.get('base')}")
    lines.append("")
    lines.append("Key Patterns Detected:")
    pats = out.get("patterns", {}).get("patterns", {})
    for pname, pinfo in pats.items():
        if pinfo.get("present"):
            lines.append(f"- {pname}: {pinfo.get('type') or pinfo.get('severity') or ''} (support: {', '.join(pinfo.get('support',[])[:3])})")
    lines.append("")
    lines.append("Top Probable Causes:")
    for c in out.get("probable_causes", {}).get("causes", [])[:5]:
        lines.append(f"- {c['cause']} (score: {c['score']}) support: {', '.join(c.get('support',[])[:2])}")
    lines.append("")
    lines.append(f"Cardiovascular risk band: {out.get('cardio',{}).get('band')} (score {out.get('cardio',{}).get('score')})")
    conf = out.get("confidence", {})
    lines.append(f"Overall confidence: {conf.get('score')}")
    if conf.get("explanation"):
        lines.append(f"Confidence explanation: {conf.get('explanation')}")
    lines.append("")
    lines.append("Notes:")
    lines.append(out.get("notes",""))
    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Model-2 pipeline on Model-1 outputs")
    parser.add_argument("--input", "-i", required=True, help="Path to Model-1 output (csv/json)")
    parser.add_argument("--output_dir", "-o", required=True, help="Directory to write Model-2 outputs")
    args = parser.parse_args()
    run(args.input, args.output_dir)
