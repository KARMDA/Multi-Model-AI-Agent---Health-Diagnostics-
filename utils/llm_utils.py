from langchain_groq import ChatGroq
import os

# ⚠️ TEMPORARY FOR PROJECT DEMO
GROQ_API_KEY = "your_api_key_here"
'''or'''
#GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024
    )
