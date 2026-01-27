"""
Milestone 3: Synthesis of findings + Personalized actionable recommendations
Multi-organ, multi-panel clinical intelligence engine
"""

# -------------------------------------------------
# SYNTHESIS ENGINE
# -------------------------------------------------
def synthesize_findings(classified_data, patterns, user_context=None):
    """
    Creates a comprehensive, organ-wise clinical summary.
    """

    # Abnormal parameters
    abnormalities = []
    for item in classified_data:
        if item["Classification"] in ["Low", "High"]:
            abnormalities.append(
                f"{item['Parameter']} is {item['Classification'].lower()} "
                f"({item['Value']} {item.get('Unit', '')})"
            )

    # Patterns
    pattern_list = []
    high_risk_patterns = []
    for p in patterns:
        name = p["Pattern"]
        risk = p.get("Adjusted_Risk_Score", p.get("Risk_Score", "N/A"))
        pattern_list.append(f"{name} (Risk Score: {round(risk, 2) if isinstance(risk, (int, float)) else risk})")
        if isinstance(risk, (int, float)) and risk >= 0.7:
            high_risk_patterns.append(name)

    summary_parts = []

    # ---------------- PARAMETER SUMMARY ----------------
    if abnormalities:
        summary_parts.append("🧪 **Key Abnormal Parameters Detected:**\n- " + "\n- ".join(abnormalities))
    else:
        summary_parts.append("🧪 **All measured laboratory parameters are within normal reference ranges.**")

    # ---------------- PATTERN SUMMARY ----------------
    if pattern_list:
        summary_parts.append("🧠 **Detected Clinical Patterns:**\n- " + "\n- ".join(pattern_list))
        if high_risk_patterns:
            summary_parts.append(f"\n⚠️ **Higher concern patterns:** {', '.join(high_risk_patterns)}")
    else:
        summary_parts.append("🧠 **No significant clinical patterns detected.**")

    # ---------------- ORGAN-WISE INTERPRETATION ----------------
    pattern_names = [p["Pattern"] for p in patterns]

    if any("Anemia" in p for p in pattern_names):
        summary_parts.append("🩸 **Blood Health:** Findings suggest altered red blood cell or hemoglobin levels consistent with anemia-related patterns.")

    if any("Infection" in p or "Leuk" in p for p in pattern_names):
        summary_parts.append("🦠 **Immune System:** White blood cell patterns indicate possible infection or immune activation.")

    if any("Diabetes" in p or "Hyperglycemia" in p for p in pattern_names):
        summary_parts.append("🍬 **Glucose Metabolism:** Blood sugar control appears impaired, suggesting dysglycemia or diabetes risk.")

    if any("Cholesterol" in p or "Dyslipidemia" in p or "Cardio" in p for p in pattern_names):
        summary_parts.append("🫀 **Cardiovascular Risk:** Lipid profile patterns suggest increased cardiovascular risk factors.")

    if any("Renal" in p or "Kidney" in p for p in pattern_names):
        summary_parts.append("🟤 **Kidney Function:** Markers indicate possible reduced renal clearance or kidney stress.")

    if any("Liver" in p or "Hepatic" in p for p in pattern_names):
        summary_parts.append("🟠 **Liver Function:** Liver enzymes or bilirubin levels suggest hepatic stress or inflammation.")

    if any("Thyroid" in p for p in pattern_names):
        summary_parts.append("🟡 **Thyroid Function:** Thyroid hormone regulation may be altered.")

    if any("Electrolyte" in p or "Sodium" in p or "Potassium" in p for p in pattern_names):
        summary_parts.append("🔵 **Electrolyte Balance:** Electrolyte disturbances may affect cardiac and neurological function.")

    # ---------------- USER CONTEXT ----------------
    if user_context:
        context_items = [f"{k.capitalize()}: {v}" for k, v in user_context.items() if v is not None]
        if context_items:
            summary_parts.append("👤 **User Context Considered:** " + "; ".join(context_items))

    return "\n\n".join(summary_parts)


# -------------------------------------------------
# RECOMMENDATION ENGINE (FULLY PERSONALIZED)
# -------------------------------------------------
def generate_personalized_recommendations(patterns, age=None, gender=None, smoking=None, family_history=None):
    """
    Uses Groq AI to generate fully personalized lifestyle & preventive recommendations.
    """

    try:
        from groq import Groq
        import streamlit as st

        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        pattern_names = [p["Pattern"] for p in patterns]

        prompt = f"""
You are a preventive healthcare lifestyle advisor.

Patient Details:
Age: {age}
Gender: {gender}
Smoking: {smoking}
Family History: {family_history}

Detected Clinical Patterns:
{pattern_names}

Task:
Generate personalized lifestyle and preventive health recommendations.

Include:
- Diet suggestions
- Exercise guidance
- Habits to avoid
- Follow-up advice

Rules:
- Do NOT mention medicines or drug names
- Do NOT diagnose
- Keep tone calm and encouraging
- Provide 6–10 bullet points
- End with a short medical disclaimer
"""

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional healthcare lifestyle advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )

        return completion.choices[0].message.content

    except Exception as e:
        # 🔒 SAFE FALLBACK (if API fails)
        return (
            "✅ Maintain a balanced diet and regular physical activity.\n"
            "✅ Ensure adequate hydration and quality sleep.\n"
            "⚠️ Always consult your doctor for personalized medical advice."
        )
    
    
    recommendations = []
    pattern_names = [p["Pattern"] for p in patterns]

    # ---------------- BASE HEALTH FOUNDATION ----------------
    recommendations.extend([
        "✅ Maintain a balanced diet with fruits, vegetables, whole grains, and lean proteins.",
        "✅ Drink sufficient water daily and aim for 7–8 hours of quality sleep.",
        "✅ Engage in regular physical activity (at least 30 minutes most days)."
    ])

    # ---------------- BLOOD / ANEMIA ----------------
    if any("Iron Deficiency" in p or "Microcytic" in p for p in pattern_names):
        recommendations.append("🥬 Iron deficiency suspected: include spinach, lentils, red meat, dates, and vitamin C–rich fruits to improve absorption.")

    if "Macrocytic Anemia" in pattern_names:
        recommendations.append("🥚 Macrocytic pattern detected: increase vitamin B12 and folate sources such as eggs, dairy, fish, leafy greens, and legumes.")

    if "Hemolytic Anemia Suspected" in pattern_names:
        recommendations.append("🍎 Include antioxidant-rich foods (berries, nuts) and avoid oxidative stress triggers. Medical evaluation is important.")

    # ---------------- DIABETES / GLUCOSE ----------------
    if any("Diabetes" in p or "Hyperglycemia" in p or "Prediabetes" in p for p in pattern_names):
        recommendations.append("🍎 Reduce refined sugar and high-glycemic foods. Prefer oats, vegetables, legumes, and pair carbohydrates with fiber and protein.")
        recommendations.append("🚶 Walking for 15–30 minutes after meals can significantly improve glucose control.")

    # ---------------- LIPID / CARDIOVASCULAR ----------------
    if any("Dyslipidemia" in p or "Cholesterol" in p or "Cardio" in p for p in pattern_names):
        recommendations.append("🥑 Adopt a heart-healthy diet: use olive oil, nuts, seeds, avocado, and fatty fish. Avoid fried and processed foods.")
        recommendations.append("🫀 Regular aerobic exercise and weight control help reduce cardiovascular risk.")

    # ---------------- KIDNEY ----------------
    if any("Renal" in p or "Kidney" in p for p in pattern_names):
        recommendations.append("💧 Maintain proper hydration and limit excess salt and protein intake. Periodic kidney function monitoring is advised.")

    # ---------------- LIVER ----------------
    if any("Liver" in p or "Hepatic" in p for p in pattern_names):
        recommendations.append("🍺 Avoid alcohol and fatty foods. Include antioxidant-rich foods such as berries, turmeric, and green leafy vegetables.")

    # ---------------- THYROID ----------------
    if "Hypothyroidism Suspected" in pattern_names:
        recommendations.append("🦋 Thyroid underactivity suspected: ensure adequate iodine intake and schedule endocrinology follow-up testing.")

    if "Hyperthyroidism Suspected" in pattern_names:
        recommendations.append("🔥 Thyroid overactivity suspected: avoid excess caffeine and consult an endocrinologist for hormone regulation.")

    # ---------------- ELECTROLYTES ----------------
    if "Hyponatremia" in pattern_names:
        recommendations.append("🧂 Low sodium detected: maintain balanced fluid and salt intake under medical supervision.")

    if "Hyperkalemia" in pattern_names:
        recommendations.append("🍌 High potassium detected: avoid excess potassium-rich foods temporarily and seek medical advice promptly.")

    # ---------------- IRON / MINERALS ----------------
    if "Hypercalcemia" in pattern_names:
        recommendations.append("🥛 Elevated calcium detected: avoid excess supplements and consider parathyroid evaluation.")

    # ---------------- INFECTION / IMMUNITY ----------------
    if any("Infection" in p or "Leukocytosis" in p or "Neutropenia" in p for p in pattern_names):
        recommendations.append("🛌 Prioritize rest, hygiene, and immune-supporting foods (yogurt, garlic, citrus). Seek medical care if fever persists.")

    # ---------------- CONTEXTUAL PERSONALIZATION ----------------
    if smoking and smoking.lower() == "yes":
        recommendations.append("🚭 Quitting smoking is strongly advised — it reduces cardiovascular, lung, and cancer risks dramatically.")

    if family_history and family_history.lower() == "yes":
        recommendations.append("👨‍⚕️ With family history present, regular preventive screenings and annual check-ups are highly recommended.")

    if age and age > 50:
        recommendations.append("🩺 Age above 50: consider regular heart, bone density, and cancer screenings. Maintain calcium and vitamin D intake.")

    if age and age > 60:
        recommendations.append("🚶 Focus on balance and strength exercises to prevent falls and maintain mobility.")

    if gender and gender.lower() == "female":
        recommendations.append("🌸 Monitor iron and calcium needs closely, especially during menstruation, pregnancy, or menopause.")

    if gender and gender.lower() == "male":
        recommendations.append("💪 Maintain prostate and cardiovascular health through regular exercise and annual health check-ups.")

    # ---------------- FINAL DISCLAIMER ----------------
    recommendations.append("\n⚠️ **Important Disclaimer:**\n"
                           "This AI system provides educational insights only and does NOT provide medical diagnosis or treatment. "
                           "Always consult a qualified healthcare professional for accurate interpretation and personalized medical advice.")

    return "\n".join(recommendations)
