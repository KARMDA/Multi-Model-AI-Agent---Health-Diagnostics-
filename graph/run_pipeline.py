from graph.graph_builder import build_graph
from graph.rag_graph_builder import build_rag_graph
from graph.graph_state import ReportState
from dotenv import load_dotenv

# Ensure env vars are loaded for Qdrant Cloud
load_dotenv()

def run_full_pipeline(file_path):
    # 1. Run Analysis Graph
    graph_app = build_graph()
    initial_state = ReportState(raw_file_path=file_path)
    final_state = graph_app.invoke(initial_state)

    # LangGraph may return a plain dict; normalize to ReportState
    if isinstance(final_state, dict):
        final_state = ReportState(**final_state)

    # 2. Run RAG Indexing Graph using the state from the first graph
    # We pass the final_state which contains the raw_text needed for indexing
    print("--- STARTING RAG INDEXING GRAPH ---")
    rag_app = build_rag_graph()
    # Invoke RAG graph with the state from the previous graph
    rag_state = rag_app.invoke(final_state)
    
    # Merge RAG results back if needed (though we mostly care about the side effect of indexing)
    if isinstance(rag_state, dict):
        if "rag_collection_name" in rag_state:
            final_state.rag_collection_name = rag_state["rag_collection_name"]
        if "errors" in rag_state and rag_state["errors"]:
            if not final_state.errors: final_state.errors = []
            final_state.errors.extend(rag_state["errors"])

    return final_state
