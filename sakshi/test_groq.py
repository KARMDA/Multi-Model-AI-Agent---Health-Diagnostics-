from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

res = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Say hello"}]
)

print(res.choices[0].message.content)
