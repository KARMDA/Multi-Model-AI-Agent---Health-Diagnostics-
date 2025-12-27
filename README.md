
# 🧠 Multi-Model AI Agent for Automated Health Diagnostics (Medicube)

A **production-grade, research-oriented multi-model AI system** for automated blood report analysis.  
The system integrates **OCR, deterministic clinical reasoning, knowledge-graph–based inference, and LLM-powered narrative synthesis** into a single, auditable pipeline, exposed via a **Streamlit UI** and packaged in a **single Docker image**.

> ⚠️ **Medical Disclaimer**  
> This platform is strictly an **assistive decision-support system** intended for educational and research use.  
> It does **not** provide diagnoses, prescriptions, or treatment recommendations.  
> All outputs must be reviewed by a qualified medical professional.

---

## ✨ Key Capabilities

- 📄 Accepts **PDF / Image / JSON** blood reports  
- 🔍 OCR with robust parameter extraction  
- 🧪 Parameter-level clinical interpretation (Normal / Low / High)  
- 🧠 Deterministic pattern detection & probabilistic risk inference  
- 🧩 Knowledge-graph–based causal reasoning  
- ✍️ LLM-based **explainable medical narratives** (with safety guardrails)  
- 🖥️ Interactive **Streamlit UI**  
- 🐳 **Single unified Docker image** for reproducibility

---

## 🧭 System Architecture

```
Input (PDF / Image / JSON)
        ↓
Extractor (OCR + Parsing)
        ↓
Model-1 (Clinical Parameter Normalization)
        ↓
Model-2 (Pattern, Risk & Causal Reasoning)
        ↓
Model-3 (LLM Narrative Synthesis)
        ↓
Final Report + Auditable Artifacts
```

> The system is intentionally **layered**, ensuring that:
> - Clinical facts are determined deterministically
> - Inference is explainable and traceable
> - LLMs are used only for **synthesis and communication**, not diagnosis

---

## 🧩 Component Breakdown

---

### 1️⃣ Extractor — OCR & Structuring

**Location:** `extractor/process_file.py`

**Responsibilities**
- OCR for scanned PDFs and images  
- Text normalization and cleanup  
- Parameter detection with plausibility checks  
- Conversion into structured CSV format  

**Outputs**
```
outputs/structured_per_report/<file>.structured.csv
outputs/model1_per_report/<file>.model1_final.csv
```

---

### 2️⃣ Model‑1 — Clinical Parameter Normalization

**Purpose:** Deterministic interpretation of extracted lab values

**Key Functions**
- Compares values against reference ranges  
- Assigns status labels:
  - Normal
  - Low
  - High
- Produces parameter-level notes for downstream reasoning

**Output**
```
outputs/model1_per_report/<file>.model1_final.csv
```

> Model‑1 contains **no probabilistic logic** — it establishes factual ground truth.

---

### 3️⃣ Model‑2 — Pattern, Risk & Causal Reasoning

**Location:** `model2/`

**Design Philosophy**
- Fully **deterministic and auditable**
- No LLM dependency
- Designed to be medically traceable

**Core Concepts**
- Pattern detection (e.g., anemia, thrombocytopenia)
- Derived metrics (ratios, trends)
- Knowledge-graph–based causal links
- Probabilistic priors over medical hypotheses
- Confidence scoring based on evidence completeness

**Key Files**
```
model2/
├── model2_runner.py        # Pipeline orchestrator
├── serializer.py           # Artifact persistence
├── verifier.py             # Output validation
└── pipeline/
    ├── loader.py
    ├── pattern_engine.py
    ├── probable_causes.py
    ├── knowledge_graph.py
    ├── risk_engine.py
    ├── confidence.py
    ├── priors.py
    └── guardrails.py
```

**Outputs**
```
outputs/model2_outputs/<file>.model2.json
outputs/model2_outputs/<file>.model2.txt
```

> Model‑2 performs **reasoning**, not narration.

---

### 4️⃣ Model‑3 — LLM Narrative Synthesis

**Location:** `model3/`

**Design Philosophy**
- LLM used **only for synthesis and explanation**
- No hard medical thresholds
- No diagnostic assertions
- Deterministic fallback if LLM fails

**Why no rule-based escalation here?**  
Hard thresholds and escalation logic are intentionally excluded to:
- Avoid duplicating deterministic logic already handled upstream
- Preserve LLM flexibility for context-aware explanation
- Prevent brittle rule explosion across parameters

**Key Files**
```
model3/
├── model3_runner.py        # Orchestration
├── prompts.py              # Prompt construction
├── schema_model3.json      # Strict output schema
├── guardrails.py           # Safety filters
├── gemini_client.py        # LLM interface
└── .env                    # API keys (not committed)
```

**Outputs**
```
outputs/model3/<file>.model3.json
outputs/model3/<file>.model3.txt
outputs/model3/<file>.model3.prompt.txt
```

---

## 🖥️ Streamlit Application

**Entry Point:** `app.py`

**Features**
- File upload (PDF / Image / JSON)
- Patient & lifestyle context input
- Step-by-step pipeline execution
- Detailed Model‑2 reasoning visualization
- Structured Model‑3 narrative output
- Artifact downloads
- Debug & audit views

Run locally:
```bash
streamlit run app.py
```

---

## 🐳 Docker Setup (Single Image)

This project intentionally uses **one unified Docker image** for:
- Reproducibility
- Simplicity
- Academic & research deployment

**Key Files**
```
Dockerfile.ui
requirements.ui.txt
```

**Build**
```bash
docker build -f Dockerfile.ui -t medicube-ai .
```

**Run**
```bash
docker run -p 8501:8501 medicube-ai
```

Open:
```
http://localhost:8501
```

---

## 📁 Full Project Structure

```
.
├── app.py
├── Dockerfile.ui
├── requirements.ui.txt
├── extractor/
│   └── process_file.py
├── model2/
│   ├── model2_runner.py
│   ├── serializer.py
│   ├── verifier.py
│   └── pipeline/
├── model3/
│   ├── model3_runner.py
│   ├── prompts.py
│   ├── schema_model3.json
│   ├── guardrails.py
│   └── gemini_client.py
├── samples/
├── docs/
│   └── architecture_flow.png
└── outputs/        # ignored in git
```

---

## 🔐 Safety & Guardrails

- No prescriptions or dosages generated
- Conservative language enforced
- Strict JSON schema validation
- Deterministic fallback when LLM fails
- Full audit trail (inputs, prompts, outputs)

---

## 🚀 Project Status

✔ End-to-end pipeline complete  
✔ Deterministic reasoning core stable  
✔ LLM integration guarded & auditable  
✔ Streamlit UI functional  
✔ Dockerized & reproducible  

---

## 📄 License

For academic, educational, and research use only.
