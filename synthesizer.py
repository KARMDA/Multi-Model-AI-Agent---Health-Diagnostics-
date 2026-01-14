# synthesizer.py
"""
Milestone 3: Synthesis of findings + Personalized actionable recommendations
"""
def synthesize_findings(classified_data, patterns, user_context=None):
    """
    Creates a comprehensive, readable summary of the entire analysis.
    """
    # Key individual abnormalities
    abnormalities = []
    for item in classified_data:
        if item["Classification"] in ["Low", "High"]:
            abnormalities.append(
                f"{item['Parameter']} is {item['Classification'].lower()} "
                f"({item['Value']} {item.get('Unit', '')})"
            )

    # Key patterns
    pattern_list = []
    high_risk_patterns = []
    for p in patterns:
        pattern_name = p["Pattern"]
        risk = p.get("Adjusted_Risk_Score", p.get("Risk_Score", "N/A"))
        pattern_list.append(f"{pattern_name} (Risk Score: {risk})")
        if isinstance(risk, (int, float)) and risk >= 0.7:
            high_risk_patterns.append(pattern_name)

    summary_parts = []

    if abnormalities:
        summary_parts.append("**Key Abnormal Parameters:**\n- " + "\n- ".join(abnormalities))
    else:
        summary_parts.append("**All measured blood parameters are within normal reference ranges.**")

    if pattern_list:
        summary_parts.append("**Detected Clinical Patterns:**\n- " + "\n- ".join(pattern_list))
        if high_risk_patterns:
            summary_parts.append(f"\n⚠️ **Higher concern patterns detected:** {', '.join(high_risk_patterns)}")
    else:
        summary_parts.append("**No significant clinical patterns detected.**")

    # Optional: Add user context to make summary more personalized
    if user_context:
        context_items = [f"{k.capitalize()}: {v}" for k, v in user_context.items() if v is not None]
        if context_items:
            summary_parts.append("**User Context:** " + "; ".join(context_items))

    full_summary = "\n\n".join(summary_parts)

    return full_summary

def generate_personalized_recommendations(patterns, age=None, gender=None, smoking=None, family_history=None):
    recommendations = []
    
    pattern_names = [p["Pattern"] for p in patterns]

    # Base healthy advice
    recommendations.append("✅ Eat a balanced diet with plenty of fruits, vegetables, whole grains, and lean proteins.")
    recommendations.append("✅ Stay hydrated and aim for 7–8 hours of sleep.")
    recommendations.append("✅ Include regular physical activity (30 minutes most days).")

    # Highly specific based on patterns
    if any("Anemia" in p for p in pattern_names):
        recommendations.append("🥬 Focus on iron-rich foods: spinach, lentils, red meat, beans. Pair with vitamin C (oranges, peppers) for better absorption.")
    if "Macrocytic Anemia" in pattern_names:
        recommendations.append("🥚 Include B12-rich foods: eggs, dairy, fish, fortified cereals. Leafy greens for folate.")
    if "Microcytic Anemia" in pattern_names:
        recommendations.append("🍖 Prioritize iron sources and avoid tea/coffee with meals (they block absorption).")

    if "Hyperglycemia" in pattern_names or "Diabetes" in pattern_names:
        recommendations.append("🍎 Choose low-glycemic foods, control portions, and pair carbs with protein/fiber. Walking after meals helps.")
    
    if "Dyslipidemia" in pattern_names or "Cholesterol" in pattern_names:
        recommendations.append("🥑 Use healthy fats: avocado, nuts, olive oil, fatty fish. Limit fried and processed foods.")

    if any("Infection" in p for p in pattern_names):
        recommendations.append("🛌 Rest well and practice good hygiene. Include immune-supporting foods like yogurt, garlic, citrus.")

    if "Thrombocytopenia" in pattern_names:
        recommendations.append("🥦 Eat vitamin K-rich foods (kale, broccoli) and avoid high-injury activities until reviewed.")

    if "Dehydration" in pattern_names:
        recommendations.append("💧 Drink more water throughout the day. Include electrolyte sources like bananas.")

    # User context personalization
    if smoking and smoking.lower() == "yes":
        recommendations.append("🚭 Quitting smoking is one of the best things you can do for your health — it dramatically lowers risk.")
    
    if family_history and family_history.lower() == "yes":
        recommendations.append("👨‍⚕️ Regular check-ups are especially important with family history — early detection matters.")

    if age and age > 50:
        recommendations.append("🩺 Consider age-appropriate screenings (heart, bone density, cancer). Include calcium and vitamin D.")

    if age and age > 60:
        recommendations.append("🚶 Gentle exercises like walking or swimming help maintain strength and balance.")

    if gender == "Female":
        recommendations.append("🌸 Pay attention to iron and calcium needs, especially during menstruation or pregnancy.")

    # Final disclaimer
    recommendations.append("\n**Important**: These are general suggestions based on your report patterns. Always consult your doctor for personalized medical advice.")

    return "\n".join(recommendations)
    """
    Generates safe, evidence-based, personalized lifestyle/health recommendations.
    Always includes disclaimer and advice to consult doctor.
    """
    recommendations = [
        "✅ Maintain a balanced diet rich in fruits, vegetables, whole grains, and lean proteins.",
        "✅ Stay hydrated and aim for at least 7–8 hours of sleep nightly.",
        "✅ Engage in regular physical activity (e.g., 30 minutes of moderate exercise most days).",
        "⚠️ **These are general suggestions based on blood report patterns. "
        "They are NOT a substitute for professional medical advice.**"
    ]

    # Pattern-specific recommendations (expanded for uniqueness)
    pattern_names = [p["Pattern"] for p in patterns]

    if any("Anemia" in p for p in pattern_names):
        recommendations.insert(1, "🥬 Consider iron-rich foods (spinach, red meat, lentils) or fortified cereals. "
                                   "Vitamin C helps iron absorption (e.g., oranges with meals).")
    if "Macrocytic Anemia" in pattern_names:
        recommendations.insert(1, "🥚 Include foods rich in Vitamin B12 (eggs, dairy, fish) and folate (leafy greens, beans).")
    if "Microcytic Anemia" in pattern_names:
        recommendations.insert(1, "🍊 Focus on iron sources and avoid tea/coffee with meals (they inhibit absorption).")

    if "Hemolytic Anemia Suspected" in pattern_names:  # New
        recommendations.insert(1, "🍎 Eat antioxidant-rich foods (berries, nuts) to support red cell health; avoid oxidative stress triggers like certain meds.")

    if any("Hyperglycemia" in p or "Diabetes" in p for p in pattern_names):
        recommendations.insert(1, "🍎 Monitor carbohydrate intake. Choose low-glycemic foods (oats, veggies) and pair with fiber/protein.")
        recommendations.insert(2, "🏃 Regular exercise like walking helps improve insulin sensitivity.")

    if any("Dyslipidemia" in p or "Cardiovascular" in p for p in pattern_names):
        recommendations.insert(1, "🥑 Focus on heart-healthy fats (avocado, nuts, olive oil). Limit fried and processed foods.")
        recommendations.insert(2, "🐟 Include omega-3 sources like fatty fish (salmon, sardines) twice a week.")

    if any("Infection" in p or "Leukocytosis" in p for p in pattern_names):
        recommendations.insert(1, "🛌 Prioritize rest and good hygiene to support immune recovery. Include probiotic foods (yogurt, kefir).")

    if "Neutropenia" in pattern_names:  # New
        recommendations.insert(1, "🧼 Practice strict hygiene to avoid infections; eat immune-boosting foods like garlic, ginger, and citrus.")

    if "Thrombocytopenia" in pattern_names:
        recommendations.insert(1, "🥑 Avoid activities with high injury risk until evaluated by a doctor. Include vitamin K-rich foods (kale, broccoli).")

    if "Thrombocytosis" in pattern_names:  # New
        recommendations.insert(1, "💧 Stay hydrated and avoid dehydration; include anti-inflammatory foods like turmeric and fatty fish to reduce clotting risk.")

    if "Pancytopenia" in pattern_names:  # New
        recommendations.insert(1, "🍲 Focus on nutrient-dense foods (bone broth, nuts, seeds) to support overall blood health; prioritize medical follow-up.")

    if "Dehydration Suspected" in pattern_names:  # New
        recommendations.insert(1, "💦 Increase water intake (aim for 8–10 glasses daily); include electrolyte-rich foods like bananas and coconut water.")

    if "Bone Marrow Suppression" in pattern_names:  # New
        recommendations.insert(1, "🥦 Eat folate-rich foods (avocados, asparagus) and get adequate rest to support marrow recovery.")

    if "Autoimmune Suspected" in pattern_names:  # New
        recommendations.insert(1, "🌿 Include anti-inflammatory foods (turmeric, green tea); manage stress with yoga or meditation.")

    if "Leukemia/Lymphoma Suspected" in pattern_names:  # New (high risk, emphasize consult)
        recommendations.insert(1, "⚠️ Prioritize immediate doctor consultation; maintain a gentle routine with light walks and balanced nutrition.")

    # Context-specific (enhanced for more uniqueness)
    if smoking and smoking.lower() == "yes":
        recommendations.insert(1, "🚭 **Strongly recommended:** Quit smoking to significantly reduce cardiovascular and inflammation risks. Consider nicotine aids or support groups.")

    if family_history and family_history.lower() == "yes":
        recommendations.insert(1, "👨‍⚕️ Regular health screenings are especially important due to family history. Track blood pressure and cholesterol annually.")

    if age and age > 50:
        recommendations.insert(1, "🩺 Schedule routine check-ups and age-appropriate screenings (e.g., bone density, colon cancer). Include calcium-rich foods for bone health.")

    if age and age < 18:
        recommendations.insert(1, "👦 Growth and development monitoring is important. Discuss with a pediatrician; ensure balanced meals for kids.")

    if age and age > 60:
        recommendations.insert(1, "🚶 Stay active with low-impact exercises like swimming; focus on fall prevention and joint health.")

    if gender and gender.lower() == "female":
        recommendations.insert(1, "🌸 Consider calcium and iron needs, especially if menstruating or pregnant; include dairy or alternatives.")

    if gender and gender.lower() == "male":
        recommendations.insert(1, "💪 Focus on prostate health with foods like tomatoes (lycopene); regular exercise supports testosterone levels.")

    # Always end with strong disclaimer
    recommendations.append("\n**Important Disclaimer:**\n"
                          "This AI system provides educational insights only. "
                          "It does **NOT** provide medical diagnosis or treatment. "
                          "Always consult a qualified healthcare professional for interpretation "
                          "and personalized medical advice.")

    return "\n".join(recommendations)

    """
    Generates safe, evidence-based, personalized lifestyle/health recommendations.
    Always includes disclaimer and advice to consult doctor.
    """
    recommendations = [
        "✅ Maintain a balanced diet rich in fruits, vegetables, whole grains, and lean proteins.",
        "✅ Stay hydrated and aim for at least 7–8 hours of sleep nightly.",
        "✅ Engage in regular physical activity (e.g., 30 minutes of moderate exercise most days).",
        "⚠️ **These are general suggestions based on blood report patterns. "
        "They are NOT a substitute for professional medical advice.**"
    ]

    # Pattern-specific recommendations
    pattern_names = [p["Pattern"] for p in patterns]

    if any("Anemia" in p for p in pattern_names):
        recommendations.insert(1, "🥬 Consider iron-rich foods (spinach, red meat, lentils) or fortified cereals. "
                                   "Vitamin C helps iron absorption.")

    if "Macrocytic Anemia" in pattern_names:
        recommendations.insert(1, "🥚 Include foods rich in Vitamin B12 (eggs, dairy, fish) and folate (leafy greens).")

    if any("Hyperglycemia" in p or "Diabetes" in p for p in pattern_names):
        recommendations.insert(1, "🍎 Monitor carbohydrate intake. Choose low-glycemic foods and pair with fiber/protein.")
        recommendations.insert(2, "🏃 Regular exercise helps improve insulin sensitivity.")

    if any("Dyslipidemia" in p or "Cardiovascular" in p for p in pattern_names):
        recommendations.insert(1, "🥑 Focus on heart-healthy fats (avocado, nuts, olive oil). Limit fried and processed foods.")
        recommendations.insert(2, "🐟 Include omega-3 sources like fatty fish (salmon, sardines).")

    if any("Infection" in p or "Leukocytosis" in p for p in pattern_names):
        recommendations.insert(1, "🛌 Prioritize rest and good hygiene to support immune recovery.")
    if any("Anemia" in p or "Hemoglobin" in p for p in pattern_names):
        recommendations.insert(1, "To help with low hemoglobin/anemia, include iron-rich foods (spinach, red meat, lentils) and vitamin C sources. Avoid tea/coffee with meals as they inhibit absorption.")

    if any("Thrombocytopenia" in p for p in pattern_names):
        recommendations.insert(1, "🥑 Avoid activities with high injury risk until evaluated by a doctor.")

    # Context-specific
    if smoking and smoking.lower() == "yes":
        recommendations.insert(1, "🚭 **Strongly recommended:** Quit smoking to significantly reduce cardiovascular and inflammation risks.")

    if family_history and family_history.lower() == "yes":
        recommendations.insert(1, "👨‍⚕️ Regular health screenings are especially important due to family history.")

    if age and age > 50:
        recommendations.insert(1, "🩺 Schedule routine check-ups and age-appropriate screenings (e.g., bone density, cancer screening).")

    if age and age < 18:
        recommendations.insert(1, "👦 Growth and development monitoring is important. Discuss with a pediatrician.")

    # Always end with strong disclaimer
    recommendations.append("\n**Important Disclaimer:**\n"
                          "This AI system provides educational insights only. "
                          "It does **NOT** provide medical diagnosis or treatment. "
                          "Always consult a qualified healthcare professional for interpretation "
                          "and personalized medical advice.")

    return "\n".join(recommendations)       
