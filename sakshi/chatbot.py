from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chatbot_answer(user_question: str, context: str) -> str:
    prompt = f"""
You are a medical report chatbot.

Context (use only this information):
{context}

User question:
{user_question}

STRICT INSTRUCTIONS:
- Answer in **maximum 4 bullet points**
- Each bullet must be **one short sentence**
- Be **clear, reassuring, and concise**
- Do NOT explain each parameter
- Do NOT include headings
- Do NOT repeat the context
- If the question is about seriousness, start with reassurance
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a concise medical assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=120
    )

    return response.choices[0].message.content
