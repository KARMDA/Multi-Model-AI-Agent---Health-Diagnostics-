from langchain_groq import ChatGroq

def get_llm():
    return ChatGroq(
        api_key="",
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024
    )
