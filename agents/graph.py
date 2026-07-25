from langgraph.graph import StateGraph, END
from agents.state import ContractState
from agents.clause_segmenter import segment_clauses
from agents.risk_analyzer import analyze_risk
from agents.summarizer import summarize_contract


def build_graph():
    workflow = StateGraph(ContractState)

    workflow.add_node("segment_clauses", segment_clauses)
    workflow.add_node("analyze_risk", analyze_risk)
    workflow.add_node("summarize", summarize_contract)

    workflow.set_entry_point("segment_clauses")
    workflow.add_edge("segment_clauses", "analyze_risk")
    workflow.add_edge("analyze_risk", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()


# Compiled once, reused across requests
contract_graph = build_graph()


def run_pipeline(raw_text: str) -> ContractState:
    """Entry point called by main.py — runs the full agent pipeline on extracted text."""
    initial_state: ContractState = {
        "raw_text": raw_text,
        "clauses": [],
        "risk_flags": [],
        "summary": "",
        "error": "",
    }
    return contract_graph.invoke(initial_state)
