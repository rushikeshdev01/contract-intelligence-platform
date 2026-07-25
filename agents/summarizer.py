from agents.state import ContractState
from services.groq_client import call_groq

SYSTEM_PROMPT = """You are a contract summarization assistant.
Given the contract text and a list of flagged risky clauses, write a concise,
plain-English executive summary (under 200 words) covering:
- What the contract is for
- Key obligations of each party
- The most important risk flags to be aware of
Write for a non-lawyer reader."""


def summarize_contract(state: ContractState) -> ContractState:
    if state.get("error"):
        return state  # don't summarize if an earlier agent failed

    risk_flags = state.get("risk_flags", [])
    risk_context = "\n".join(
        f"- [{r['risk_level'].upper()}] {r['reason']}" for r in risk_flags
    )

    user_prompt = f"""CONTRACT TEXT:
{state.get('raw_text', '')}

FLAGGED RISKS:
{risk_context}"""

    summary = call_groq(SYSTEM_PROMPT, user_prompt, json_mode=False)
    return {**state, "summary": summary}
