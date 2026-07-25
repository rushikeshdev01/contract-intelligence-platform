from typing import TypedDict, List, Dict


class ClauseRisk(TypedDict):
    clause: str
    risk_level: str  # "low" | "medium" | "high"
    reason: str


class ContractState(TypedDict):
    """
    Shared state object passed between agents in the LangGraph pipeline.
    Each agent reads what it needs and writes its own output field —
    nobody overwrites another agent's field.
    """
    raw_text: str                  # set by extraction step (before graph runs)
    clauses: List[str]             # set by ClauseSegmenter
    risk_flags: List[ClauseRisk]   # set by RiskAnalyzer
    summary: str                   # set by Summarizer
    error: str                     # set if any agent fails, so the graph can stop cleanly
