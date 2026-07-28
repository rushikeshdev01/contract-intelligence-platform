from typing import TypedDict, List, Dict, Any


class ClauseRisk(TypedDict):
    clause: str
    risk_level: str  # "low" | "medium" | "high"
    risk_score: int  # 0-100, finer-grained than risk_level
    reason: str
    type: str  # "present" | "missing"
    legal_reference: str  # optional — e.g. "Indian Contract Act, 1872, Section 27"


class BenchmarkRow(TypedDict):
    provision: str
    contract_value_days: float
    standard_range: str
    status: str  # "green" | "yellow" | "red"


class ContractState(TypedDict):
    """
    Shared state object passed between agents in the LangGraph pipeline.
    Each agent reads what it needs and writes its own output field —
    nobody overwrites another agent's field.
    """
    raw_text: str                  # set by extraction step (before graph runs)
    user_position: str             # set before graph runs — which party the user is (e.g. "vendor", "customer")
    document_type: str             # set by DocClassifier — e.g. "NDA", "SaaS / Software Agreement"
    clauses: List[str]             # set by ClauseSegmenter
    risk_flags: List[ClauseRisk]   # set by RiskAnalyzer
    benchmarks: List[BenchmarkRow] # set by BenchmarkAnalyzer
    summary: str                   # set by Summarizer
    error: str                     # set if any agent fails, so the graph can stop cleanly