from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_summary_and_recommendations(findings_text: str) -> str:
    prompt = f"""
You are a medical report summarization assistant.

Tasks:
1. Generate a concise clinical summary.
2. Provide exactly three lifestyle or follow-up recommendations.

Rules:
- Do NOT diagnose diseases
- Do NOT prescribe medicines
- Use a professional, neutral medical tone
- Output strictly in bullet points

Format:

Clinical Summary:
• point 1
• point 2

Recommendations:
• recommendation 1
• recommendation 2
• recommendation 3

Clinical Findings:
{findings_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a careful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    return response.choices[0].message.content
