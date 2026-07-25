from agents.state import ContractState
from services.groq_client import call_groq_json

SYSTEM_PROMPT = """You are a contract risk analysis assistant.

Do TWO things:

1. PRESENT-CLAUSE RISK: For each clause given, assess its risk level for the
   party signing the contract. Focus especially on: liability caps, indemnity,
   auto-renewal, termination penalties, exclusivity, and unusual payment terms.

2. MISSING-PROVISION RISK: A contract that never mentions a critical
   protection is often riskier than one that states it explicitly, because the
   risk is hidden. Check whether the contract addresses each of these, and if
   a given protection is NOT mentioned anywhere, add a risk flag for it:
   - Cap on liability
   - Termination for convenience (either party can exit without cause)
   - Governing law / jurisdiction
   - Confidentiality / data handling
   - Indemnification terms
   If a check is genuinely not applicable to this contract type, skip it rather
   than forcing a flag.

Return ONLY valid JSON in this exact shape:
{"risk_flags": [{"clause": "...", "risk_level": "low|medium|high", "reason": "...", "type": "present|missing"}]}
For missing-provision flags, set "clause" to the name of the missing provision
(e.g. "Cap on Liability") and "type" to "missing". Keep "reason" to one concise
sentence."""


def analyze_risk(state: ContractState) -> ContractState:
    clauses = state.get("clauses", [])
    if not clauses:
        return {**state, "error": "No clauses found for risk analysis"}

    numbered = "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(clauses))
    result = call_groq_json(SYSTEM_PROMPT, numbered)

    if "error" in result:
        return {**state, "error": result["error"]}

    return {**state, "risk_flags": result.get("risk_flags", [])}