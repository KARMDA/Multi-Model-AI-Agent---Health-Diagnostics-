import streamlit as st
import pandas as pd
import json
import io
import fitz  # PyMuPDF

from data_processor import (
    process_file_full,
    run_milestone_2_models,
    run_milestone_3,
    extract_text_per_page
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="AI Health Diagnostics Agent", layout="wide")

st.title("🩸 AI Health Diagnostics Agent")
st.markdown("**Upload your blood report → Get instant analysis → Chat with your personal AI health assistant **")

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
if "report_analyzed" not in st.session_state:
    st.session_state.report_analyzed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "classified_data" not in st.session_state:
    st.session_state.classified_data = None
if "m2_out" not in st.session_state:
    st.session_state.m2_out = None
if "m3_out" not in st.session_state:
    st.session_state.m3_out = None
if "user_context" not in st.session_state:
    st.session_state.user_context = {}

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Blood Report (PDF or Image)",
    type=["pdf", "jpg", "jpeg", "png"]
)

final_file_to_process = uploaded_file

# -------------------------------------------------
# MULTI-PAGE PDF HANDLING
# -------------------------------------------------
if uploaded_file is not None:
    st.info(f"Uploaded: **{uploaded_file.name}**")

    if uploaded_file.type == "application/pdf":
        with st.spinner("Scanning PDF pages..."):
            pages_text = extract_text_per_page(uploaded_file)

        if len(pages_text) > 1:
            st.warning(f"Multiple pages detected ({len(pages_text)}). Please select pages belonging to ONE report.")

            selected_pages = st.multiselect(
                "Select pages for analysis",
                options=[p["page"] for p in pages_text],
                default=[1]
            )

            if not selected_pages:
                st.stop()

            for page_num in selected_pages:
                page_data = next(p for p in pages_text if p["page"] == page_num)
                with st.expander(f"Preview Page {page_num}"):
                    st.text(page_data["text_preview"])

            doc = fitz.open(stream=io.BytesIO(uploaded_file.getvalue()))
            new_doc = fitz.open()

            for p in sorted(selected_pages):
                new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)

            processed = io.BytesIO()
            new_doc.save(processed)
            processed.name = "selected_report.pdf"
            processed.type = "application/pdf"
            final_file_to_process = processed

            st.success("Selected pages prepared for analysis")

# -------------------------------------------------
# USER CONTEXT
# -------------------------------------------------
st.subheader("Optional: Your Details (Helps personalize advice)")
c1, c2, c3, c4 = st.columns(4)
age = c1.number_input("Age", min_value=0, max_value=120, value=30, step=1)
gender = c2.selectbox("Gender", ["", "Male", "Female"])
smoking = c3.selectbox("Do you smoke?", ["", "Yes", "No"])
family_history = c4.selectbox("Family history of Diabetes/Heart Disease?", ["", "Yes", "No"])

# -------------------------------------------------
# RUN ANALYSIS
# -------------------------------------------------
if st.button("🚀 Start Analysis", type="primary") and final_file_to_process:
    with st.spinner("Analyzing your blood report... This may take 30–60 seconds"):
        try:
            classified_data, metrics = process_file_full(final_file_to_process)

            m2_out = run_milestone_2_models(
                classified_data,
                age=age if age > 0 else None,
                gender=gender or None,
                smoking=smoking or None,
                family_history=family_history or None
            )

            m3_out = run_milestone_3(
                classified_data,
                m2_out,
                age=age if age > 0 else None,
                gender=gender or None,
                smoking=smoking or None,
                family_history=family_history or None
            )

            st.session_state.metrics = metrics
            st.session_state.classified_data = classified_data
            st.session_state.m2_out = m2_out
            st.session_state.m3_out = m3_out
            st.session_state.user_context = {
                "age": age if age > 0 else None,
                "gender": gender or None,
                "smoking": smoking or None,
                "family_history": family_history or None
            }
            st.session_state.report_analyzed = True
            st.success("✅ Analysis Complete!")

        except Exception as e:
            st.error(f"Analysis error: {e}")

# -------------------------------------------------
# DISPLAY RESULTS
# -------------------------------------------------
if st.session_state.report_analyzed:
    data = st.session_state.classified_data
    metrics = st.session_state.metrics
    m2_out = st.session_state.m2_out
    m3_out = st.session_state.m3_out
    context = st.session_state.user_context

    st.header("📊 Extracted Blood Parameters")
    col1, col2, col3 = st.columns(3)
    col1.metric("Extraction Accuracy", f"{metrics.get('Extraction_Accuracy', 0):.1f}%")
    col2.metric("Classification Accuracy", f"{metrics.get('Classification_Accuracy', 0):.1f}%")
    col3.metric("Parameters Detected", len(data))

    df = pd.DataFrame(data)

    def highlight_classification(val):
        if val == "High":
            return "background-color:#ffebee; color:#721c24"
        if val == "Low":
            return "background-color:#fff3e0; color:#856404"
        if val == "Normal":
            return "background-color:#e8f5e8; color:#155724"
        return ""

    st.dataframe(df.style.applymap(highlight_classification, subset=["Classification"]), use_container_width=True)

    st.header("🔍 Detected Clinical Patterns")
    patterns = m2_out.get("patterns", [])
    if patterns:
        for p in patterns:
            risk = p.get("Adjusted_Risk_Score", p.get("Risk_Score", 0))
            with st.expander(f"**{p['Pattern']}** — Risk Score: {risk:.2f}", expanded=False):
                st.write(p["Description"])
                if p.get("Calc_Notes"):
                    st.caption("**Calculations:** " + " | ".join(p["Calc_Notes"]))
                if p.get("Context_Notes"):
                    st.caption("**Personal Context:** " + " | ".join(p["Context_Notes"]))
    else:
        st.success("No concerning clinical patterns detected — that's great!")

    st.header("📝 Your Health Summary & Recommendations")
    st.markdown(m3_out["comprehensive_summary"])
    st.markdown("### 💡 Personalized Lifestyle Suggestions")
    st.markdown(m3_out["personalized_recommendations"])

    st.download_button(
        "📄 Download Full Report (JSON)",
        data=json.dumps({"parameters": data, "patterns": patterns, **m3_out}, indent=2),
        file_name="health_report.json",
        mime="application/json"
    )
    st.download_button(
        "📜 Download Summary (Text)",
        data=f"HEALTH REPORT SUMMARY\n\n{m3_out['comprehensive_summary']}\n\nRECOMMENDATIONS\n{m3_out['personalized_recommendations']}\n\n⚠️ Educational use only. Consult your doctor.",
        file_name="health_summary.txt",
        mime="text/plain"
    )

# -------------------------------------------------
# PERSONAL AI CHATBOT (Groq Powered)
# -------------------------------------------------
if st.session_state.report_analyzed:
    st.markdown("---")
    st.header("💬 Your Personal Health Assistant")

    greeting = "Hello"
    if context.get("gender") == "Male":
        greeting += ", sir"
    elif context.get("gender") == "Female":
        greeting += ", ma'am"
    st.caption(f"{greeting}! I'm your caring health assistant. Ask me anything about your report.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about risks, diet, values, or anything..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking with Groq AI..."):
                data = st.session_state.classified_data
                context = st.session_state.user_context
                patterns = m2_out.get("patterns", [])
                m3_out = st.session_state.m3_out

                abnormalities = [f"{d['Parameter']} is {d['Classification']} ({d['Value']})"
                                 for d in data if d['Classification'] in ['Low', 'High']]

                try:
                    from groq import Groq

                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

                    system_prompt = f"""
You are a calm, empathetic health assistant.
Answer briefly and naturally (3–5 sentences).
Do NOT diagnose — say 'may suggest'.
Use the patient's actual report values.

USER CONTEXT:
{context}

ABNORMAL PARAMETERS:
{abnormalities if abnormalities else 'All normal'}

PATTERNS:
{patterns if patterns else 'None'}

SUMMARY:
{m3_out['comprehensive_summary']}

RECOMMENDATIONS:
{m3_out['personalized_recommendations']}
"""

                    chat_completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",  # Correct working model
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1024
                    )
                    response = chat_completion.choices[0].message.content

                except Exception as e:
                    response = f"Groq error: {str(e)[:200]}\n\nCheck your API key and internet connection."

                response += "\n\n⚠️ *This AI provides educational information only.*"

                st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    st.info("👆 Upload and analyze a blood report to enable the AI assistant")

st.caption("🔒 Private • Fast • Ethical")
