def contextualize_patterns(patterns, age, gender):
    insights = []

    for p in patterns:

        # ---- Infection / stress pattern ----
        if "neutrophilia" in p.lower():
            insights.append(
                f"Suggests possible infection or stress response in a {age}-year-old {gender.lower()}"
            )

        # ---- Anemia ----
        elif "low hemoglobin" in p.lower() or "anemia" in p.lower():
            if gender.lower() == "female":
                insights.append(
                    "Low hemoglobin may indicate iron deficiency, which is more common in females"
                )
            else:
                insights.append(
                    "Low hemoglobin may suggest mild anemia; dietary iron intake should be reviewed"
                )

        # ---- High PCV ----
        elif "high pcv" in p.lower():
            insights.append(
                "Elevated PCV may be associated with dehydration or reduced plasma volume"
            )

        # ---- Borderline platelets ----
        elif "borderline platelet" in p.lower():
            insights.append(
                "Borderline platelet count may be transient; monitoring and repeat testing can be considered"
            )

        # ---- High MCHC ----
        elif "high mchc" in p.lower():
            insights.append(
                f"Elevated MCHC in {gender.lower()} patients may indicate dehydration or RBC membrane disorders"
            )

    return insights
