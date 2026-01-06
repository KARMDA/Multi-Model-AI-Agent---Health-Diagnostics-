from langchain_groq import ChatGroq

# ⚠️ TEMPORARY FOR PROJECT DEMO
GROQ_API_KEY = "your_api_key_here"

def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024
    )
