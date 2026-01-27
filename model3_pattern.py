# model3_pattern.py

def apply_contextual_adjustments(patterns, age=None, gender=None, smoking=None, family_history=None):
    """
    Adjusts risks with context (expanded for CVD/diabetes per AHA/Mayo).
    """
    updated = []

    for item in patterns:
        score = item["Risk_Score"]
        notes = item.get("Context_Notes", [])  # Preserve any existing

        if age:
            if age > 60:
                score += 0.15 if "Cardiovascular" in item["Pattern"] else 0.1
                notes.append("Age >60 increases CVD and overall risk (Framingham/ASCVD).")
            elif age < 18:
                score -= 0.05
                notes.append("Younger age; pediatric ranges may apply (adjust cautiously).")

        if gender:
            if gender.lower() == "male":
                score += 0.1 if "Cardiovascular" in item["Pattern"] else 0.05
                notes.append("Males have higher baseline CVD risk (AHA).")
            elif gender.lower() == "female":
                notes.append("Females: consider hormonal factors in anemia/dyslipidemia.")

        if smoking and smoking.lower() == "yes":
            score += 0.2 if "Cardiovascular" in item["Pattern"] or "Dyslipidemia" in item["Pattern"] else 0.1
            notes.append("Smoking significantly elevates CVD and inflammation risk (Mayo).")

        if family_history and family_history.lower() == "yes":
            score += 0.15 if "Cardiovascular" in item["Pattern"] or "Hyperglycemia" in item["Pattern"] else 0.1
            notes.append("Family history raises genetic risk for CVD/diabetes (Cleveland Clinic).")

        score = min(round(score, 2), 1.0)

        updated.append({
            **item,
            "Adjusted_Risk_Score": score,
            "Context_Notes": notes
        })

    return updated
