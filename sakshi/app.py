# app.py
# Run with: streamlit run app.py

import io
import re
from typing import List, Optional

import streamlit as st
import pandas as pd
from PIL import Image, ImageFilter, ImageOps

import pdfplumber
import pytesseract
import json

# =========================
# MILESTONE-2 ORCHESTRATOR
# =========================
from analyzer import run_milestone2

from milestone3_synthesis import synthesize_findings, generate_recommendations
from llm_groq import generate_summary_and_recommendations

from chatbot import chatbot_answer

from pdf2image import convert_from_bytes

st.set_page_config(
    page_title="Multi-Model AI Agent for Automated Health Diagnostics",
    layout="wide"
)

# =========================
# CBC STANDARDIZATION MAP
# =========================
CBC_KEYS = {
    "hemoglobin": "Hemoglobin",
    "hb": "Hemoglobin",
    "total rbc": "RBC",
    "rbc": "RBC",
    "packed cell volume": "PCV",
    "pcv": "PCV",
    "hematocrit": "PCV",
    "mcv": "MCV",
    "mch": "MCH",
    "mchc": "MCHC",
    "rdw": "RDW",
    "total wbc": "WBC",
    "wbc": "WBC",
    "platelet": "Platelets"
}

# =========================
# SAFE GLOBAL INIT
# =========================
df_result = pd.DataFrame()

# ------------------------------------------------
# 1. PARSING HELPERS
# ------------------------------------------------
def clean_number_token(tok: str) -> Optional[float]:
    tok = tok.replace(",", "").strip().rstrip(",:;%")
    try:
        return float(tok)
    except ValueError:
        return None


def parse_lab_text_to_dataframe(lines: List[str]) -> pd.DataFrame:
    rows = []

    for raw_line in lines:
        line = raw_line.strip()

        # Ignore headers and patient info
        if any(x in line.lower() for x in [
            "patient", "id", "name", "age", "gender", "report", "lab", "----"
        ]):
            continue

        # Match patterns like: "Hemoglobin (Hb): 12.5 g/dL"
        match = re.search(r"([A-Za-z ()]+)\s*[:\-]\s*([\d,.]+)", line)
        if not match:
            continue

        name = match.group(1).strip()
        value = match.group(2).replace(",", "")

        try:
            value = float(value)
        except ValueError:
            continue

        rows.append({
            "Parameter": name,
            "Value": value
        })

    return pd.DataFrame(rows)

# ------------------------------------------------
# 2. IMAGE OCR (NO POPPLER)
# ------------------------------------------------
def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    img = image.convert("L")
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img

def ocr_image_to_lines(image: Image.Image) -> List[str]:
    enhanced = enhance_image_for_ocr(image)
    text = pytesseract.image_to_string(
        enhanced,
        config="--oem 3 --psm 6"
    )
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def pdf_to_df_ocr(pdf_bytes: bytes) -> pd.DataFrame:
    images = convert_from_bytes(pdf_bytes)
    all_lines = []

    for img in images:
        lines = ocr_image_to_lines(img)
        all_lines.extend(lines)

    if not all_lines:
        return pd.DataFrame()

    return parse_lab_text_to_dataframe(all_lines)

# ------------------------------------------------
# 3. PDF TEXT EXTRACTION (TEXT PDF ONLY)
# ------------------------------------------------
def pdf_to_df_text(pdf_bytes: bytes) -> pd.DataFrame:
    all_lines = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                all_lines.extend(lines)

    if not all_lines:
        return pd.DataFrame()

    return parse_lab_text_to_dataframe(all_lines)


# ------------------------------------------------
# 4. BUILD CLEAN CBC DATA (CRITICAL FIX)
# ------------------------------------------------
def build_clean_cbc_data(df):
    clean = {}

    for _, row in df.iterrows():
        param = str(row["Parameter"]).lower()
        value = row["Value"]

        # 🚫 Skip demographic fields from OCR
        if any(x in param for x in ["age", "sex", "gender", "male", "female"]):
            continue

        if "hemoglobin" in param or "hb" in param:
            clean["Hemoglobin"] = value
        elif "wbc" in param or "leukocyte" in param or "white blood" in param:
            clean["WBC"] = value
        elif "platelet" in param:
            clean["Platelets"] = value
        elif "rbc" in param or "red blood" in param:
            clean["RBC"] = value
        elif "neutrophil" in param:
            clean["Neutrophils"] = value
        elif "lymphocyte" in param:
            clean["Lymphocytes"] = value
        elif "mchc" in param:
            clean["MCHC"] = value
        elif "pcv" in param or "packed cell volume" in param:
            clean["PCV"] = value


    return clean
 

def normalize_units(clean_data: dict) -> dict:
    normalized = {}

    for k, v in clean_data.items():
        if k == "Platelets":
            # If OCR extracted value is too small, scale it
            if v < 100000:
                normalized[k] = v * 10
            else:
                normalized[k] = v
        else:
            normalized[k] = v

    return normalized

def normalize_param_name(name: str) -> str:
    name = name.lower()

    if "hemoglobin" in name or "hb" in name:
        return "Hemoglobin"
    if "pcv" in name or "packed cell volume" in name:
        return "PCV"
    if "platelet" in name:
        return "Platelets"
    if "wbc" in name:
        return "WBC"
    if "rbc" in name:
        return "RBC"
    if "neutrophil" in name:
        return "Neutrophils"
    if "lymphocyte" in name:
        return "Lymphocytes"
    if "mchc" in name:
        return "MCHC"
    if "mcv" in name:
        return "MCV"
    if "mch" in name:
        return "MCH"
    if "rdw" in name:
        return "RDW"
    if "esr" in name:
        return "ESR"

    return None  # ignore everything else

# ------------------------------------------------
# 5. STREAMLIT UI
# ------------------------------------------------
st.title("🩺 Multi-Model AI Agent for Automated Health Diagnostics")

uploaded = st.file_uploader(
    "Upload blood report (PDF / Image / JSON)",
    type=["pdf", "png", "jpg", "jpeg", "json"]
)

def pdf_has_text(pdf_bytes: bytes) -> bool:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    return True
    except Exception:
        return False
    return False

if uploaded:
    file_bytes = uploaded.read()
    file_name = uploaded.name.lower()

    try:
        # ---------- PDF ----------
        if file_name.endswith(".pdf"):
            if pdf_has_text(file_bytes):
                df_result = pdf_to_df_text(file_bytes)
           # else:
               # st.info("Scanned PDF detected. Applying OCR...")
               # df_result = pdf_to_df_ocr(file_bytes)

            if df_result.empty:
                st.error("Unable to extract lab data from the PDF.")

        # ---------- JSON ----------
        elif file_name.endswith(".json"):
            data = json.loads(file_bytes.decode())
            df_result = pd.DataFrame([
                {"Parameter": k, "Value": v.get("value")}
                for k, v in data.items()
            ])

        # ---------- IMAGE ----------
        else:
            image = Image.open(io.BytesIO(file_bytes))
            st.image(image, caption="Uploaded Image")
            lines = ocr_image_to_lines(image)
            df_result = parse_lab_text_to_dataframe(lines)

    except Exception as e:
        st.error(f"Processing error: {e}")
        df_result = pd.DataFrame()


# ------------------------------------------------
# DISPLAY EXTRACTED DATA
# ------------------------------------------------
if df_result.empty:
    st.stop()

st.subheader("📄 Extracted Results")
st.dataframe(df_result, width="stretch", height=300 )

# ------------------------------------------------
# MODEL-1: INDIVIDUAL PARAMETER VIEW
# ------------------------------------------------
st.subheader("🔬 Individual Parameter Analysis")

REFERENCE_RANGES = {
    "Hemoglobin": (13.0, 17.0),
    "PCV": (40.0, 50.0),
    "Platelets": (150000, 410000),
    "WBC": (4000, 11000),
}

model1_output = {}

for _, row in df_result.iterrows():
    raw_param = row["Parameter"]
    value = row["Value"]

    param = normalize_param_name(raw_param)
    if param is None:
        continue  # skip non-lab fields

    status = "normal"

    if param in REFERENCE_RANGES:
        low, high = REFERENCE_RANGES[param]

        if value < low:
            status = "low"
        elif value > high:
            status = "high"
        elif param == "Platelets" and value <= 180000:
            status = "borderline"

    model1_output[param] = {
        "value": value,
        "status": status
    }

st.json(model1_output)



# Ensure milestone2_results exists even if user hasn't provided context yet
milestone2_results = {}

# ------------------------------------------------
# CONTEXT INPUT
# ------------------------------------------------
st.subheader("🧍 Contextual Information")

age = st.number_input("Age", min_value=1, max_value=120, value=None)
gender_options = ["", "Male", "Female"]
gender = st.selectbox("Gender", gender_options, index=0)

# Only show pattern recognition if age and gender are provided
if age is not None and gender and gender != "":

    st.write(f"**Patient Details:** Age {age}, Gender {gender}")

    # ------------------------------------------------
    # MODEL-2: PATTERN RECOGNITION (CORRECT)
    # ------------------------------------------------
    st.subheader("📊 Pattern Recognition & Risk Assessment")

    clean_data = normalize_units(build_clean_cbc_data(df_result))

    st.write("**Cleaned CBC Data:**")
    st.json(clean_data)

    milestone2_results = run_milestone2(
        clean_data=clean_data,
        age=age,
        gender=gender
    )

    st.write("**Analysis Results:**")
    st.json(milestone2_results)

    # ------------------------------------------------
    # MILESTONE-3: FINDINGS SYNTHESIS (AFTER PATTERN RECOGNITION)
    # ------------------------------------------------
    st.subheader("🧠 Synthesized Clinical Summary")

    summary_text = synthesize_findings(
        model1_output=model1_output,
        milestone2_output=milestone2_results
    )

    st.write("\n")
    for point in summary_text.split(". "):
            if point.strip():
                st.write("• " + point.strip() + ".")

    # ------------------------------------------------
    # SEVERITY INDICATOR
    # ------------------------------------------------
    if milestone2_results.get("identified_patterns"):
        st.warning("⚠️ Severity Level: Moderate - clinical correlation recommended")
    else:
        st.info("✅ Severity Level: Normal - no significant abnormalities detected")

    # ------------------------------------------------
    # RECOMMENDATIONS
    # ------------------------------------------------
    st.subheader("✅ Personalized Health Recommendations (Lifestyle & Follow-up)")

    recommendations = generate_recommendations(
        summary_text=summary_text,
        age=age,
        gender=gender
    )

    for rec in recommendations:
        st.write("•", rec)


else:
    st.info("Please provide age and gender to see pattern recognition, synthesized summary, and recommendations.")

# ------------------------------------------------
# UI STYLING
# ------------------------------------------------
    st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
}
h1, h2, h3 {
    color: #0e3c68;
}
</style>
""", unsafe_allow_html=True)
# ------------------------------------------------
# CHATBOT: REPORT Q&A
# ------------------------------------------------
st.subheader("💬 Ask Questions About Your Report")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_question = st.text_input("Ask a question about your health report")

if st.button("Ask"):
    if user_question.strip():
        context_text = f"""
Clinical Summary:
{summary_text}

Individual Parameter Analysis:
{model1_output}

Pattern & Risk Assessment:
{milestone2_results}
"""

        answer = chatbot_answer(user_question, context_text)

        st.session_state.chat_history.append({
            "question": user_question,
            "answer": answer
        })

# ---- Display chat history ----
for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['question']}")
    st.markdown(f"**AI:** ")
    for point in chat['answer'].split('•'):
        if point.strip():
            st.write("•", point.strip())
