from agents.state import ContractState
from services.groq_client import call_groq_json
from services.checklists import DOCUMENT_TYPES

SYSTEM_PROMPT = f"""You are a contract classification assistant.
Read the contract text and classify it into exactly ONE of these categories:
{", ".join(DOCUMENT_TYPES)}

Return ONLY valid JSON in this exact shape:
{{"document_type": "one of the categories above"}}
If none fit well, use "Other / General Commercial Agreement"."""


def classify_document(state: ContractState) -> ContractState:
    raw_text = state.get("raw_text", "")
    if not raw_text:
        return {**state, "error": "No raw_text found for document classification"}

    result = call_groq_json(SYSTEM_PROMPT, raw_text[:6000])  # first ~6000 chars is enough to classify

    doc_type = result.get("document_type", "Other / General Commercial Agreement")
    if doc_type not in DOCUMENT_TYPES:
        doc_type = "Other / General Commercial Agreement"

    return {**state, "document_type": doc_type}