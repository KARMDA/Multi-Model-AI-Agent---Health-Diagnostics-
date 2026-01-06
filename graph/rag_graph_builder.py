from langgraph.graph import StateGraph, END
from graph.graph_state import ReportState
from nodes.rag_node import rag_indexing_node

def build_rag_graph():
    workflow = StateGraph(ReportState)

    workflow.add_node("rag_indexing", rag_indexing_node)

    workflow.set_entry_point("rag_indexing")
    workflow.add_edge("rag_indexing", END)

    return workflow.compile()
