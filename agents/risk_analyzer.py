from agents.state import ContractState
from services.groq_client import call_groq_json

SYSTEM_PROMPT = """You are a contract risk analysis assistant.
For each clause given, assess its risk level for the party signing the contract.
Return ONLY valid JSON in this exact shape:
{"risk_flags": [{"clause": "...", "risk_level": "low|medium|high", "reason": "..."}]}
Focus especially on: liability caps, indemnity, auto-renewal, termination penalties,
exclusivity, and unusual payment terms. Keep "reason" to one concise sentence."""


def analyze_risk(state: ContractState) -> ContractState:
    clauses = state.get("clauses", [])
    if not clauses:
        return {**state, "error": "No clauses found for risk analysis"}

    numbered = "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(clauses))
    result = call_groq_json(SYSTEM_PROMPT, numbered)

    if "error" in result:
        return {**state, "error": result["error"]}

    return {**state, "risk_flags": result.get("risk_flags", [])}
