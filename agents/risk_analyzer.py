from agents.state import ContractState
from services.groq_client import call_groq_json
from services.checklists import get_checklist

BASE_INSTRUCTIONS = """You are a contract risk analysis assistant.

Do TWO things:

1. PRESENT-CLAUSE RISK: For each clause given, assess its risk level FOR THE
   USER'S STATED POSITION (given below) — not a generic neutral view. The same
   clause can be low-risk for one party and high-risk for the other (e.g. a
   vendor-favorable liability cap is low-risk for the vendor, high-risk for the
   customer). Focus especially on: liability caps, indemnity, auto-renewal,
   termination penalties, exclusivity, and unusual payment terms. Alongside the
   "low|medium|high" label, also give a numeric "risk_score" from 0-100 (0 =
   no risk, 100 = severe risk) so clauses within the same level can still be
   ranked against each other.

2. MISSING-PROVISION RISK: A contract that never mentions a critical
   protection is often riskier than one that states it explicitly, because the
   risk is hidden. This contract has been classified as: "{document_type}".
   Check whether it addresses each of the following (the checklist for this
   specific contract type), and if a given protection is NOT mentioned
   anywhere, add a risk flag for it:
{checklist_items}
   If a check is genuinely not applicable to this contract, skip it rather
   than forcing a flag. Give missing-provision flags a "risk_score" too, using
   the same 0-100 scale.

Return ONLY valid JSON in this exact shape:
{{"risk_flags": [{{"clause": "...", "risk_level": "low|medium|high", "risk_score": 0-100, "reason": "...", "type": "present|missing"}}]}}
For missing-provision flags, set "clause" to the name of the missing provision
(e.g. "Cap on Liability") and "type" to "missing". Keep "reason" to one concise
sentence."""


LEVEL_DEFAULT_SCORE = {"low": 20, "medium": 60, "high": 90}


def build_system_prompt(user_position: str, document_type: str) -> str:
    checklist = get_checklist(document_type)
    checklist_items = "\n".join(f"   - {item}" for item in checklist)
    prompt = BASE_INSTRUCTIONS.format(document_type=document_type, checklist_items=checklist_items)

    if user_position and user_position.strip().lower() != "not specified":
        position_line = f'\nThe user\'s position in this contract is: "{user_position}". Assess every risk from this party\'s point of view.\n'
    else:
        position_line = "\nThe user has not specified which party they are — give a balanced, neutral assessment.\n"
    return prompt + position_line


def analyze_risk(state: ContractState) -> ContractState:
    clauses = state.get("clauses", [])
    if not clauses:
        return {**state, "error": "No clauses found for risk analysis"}

    numbered = "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(clauses))
    document_type = state.get("document_type", "Other / General Commercial Agreement")
    system_prompt = build_system_prompt(state.get("user_position", ""), document_type)
    result = call_groq_json(system_prompt, numbered)

    if "error" in result:
        return {**state, "error": result["error"]}

    flags = result.get("risk_flags", [])
    # Backfill a default numeric score if the model omits it, so the UI never breaks
    for flag in flags:
        if "risk_score" not in flag or not isinstance(flag.get("risk_score"), (int, float)):
            flag["risk_score"] = LEVEL_DEFAULT_SCORE.get(flag.get("risk_level", "").lower(), 50)

    return {**state, "risk_flags": flags}