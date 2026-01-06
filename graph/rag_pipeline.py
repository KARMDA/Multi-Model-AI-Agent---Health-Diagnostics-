from nodes.rag_node import rag_retrieve_and_answer, get_chat_history
from typing import Any


def run_rag_pipeline(question: str, collection_name: str, session_id: str = None, report_context: Any = None) -> str:
    """
    Executes the RAG pipeline for a given question.
    This wrapper function allows for modular execution of the chat component.
    """
    return rag_retrieve_and_answer(question, collection_name, session_id, report_context)
