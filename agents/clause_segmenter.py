from agents.state import ContractState
from services.groq_client import call_groq_json

SYSTEM_PROMPT = """You are a legal document parsing assistant.
Split the given contract text into distinct clauses/sections.
Return ONLY valid JSON in this exact shape:
{"clauses": ["clause 1 text", "clause 2 text", ...]}
Each clause should be a self-contained chunk (a paragraph or numbered section).
Do not summarize or alter the text — preserve original wording."""


def segment_clauses(state: ContractState) -> ContractState:
    if not state.get("raw_text"):
        return {**state, "error": "No raw_text found for clause segmentation"}

    result = call_groq_json(SYSTEM_PROMPT, state["raw_text"])

    if "error" in result:
        return {**state, "error": result["error"]}

    return {**state, "clauses": result.get("clauses", [])}
