from services.groq_client import call_groq

SYSTEM_PROMPT_TEMPLATE = """You are a contract Q&A assistant. Answer the
user's question using ONLY the contract clauses provided below — do not
invent facts not present in the text. If the contract doesn't address the
question, say so plainly rather than guessing.

The contract has been classified as: {document_type}
The user's position in this contract is: {user_position}

When your answer is grounded in a specific clause, reference it like
"According to Clause {{n}}...". Keep the answer concise (2-4 sentences) and
in plain English — the user is not a lawyer.

Contract clauses:
{clauses_text}
"""


def answer_question(clauses: list, question: str, document_type: str = "", user_position: str = "") -> str:
    if not clauses:
        return "No contract has been analyzed yet, so I don't have any clauses to answer from."

    clauses_text = "\n\n".join(f"Clause {i+1}: {c}" for i, c in enumerate(clauses))
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        document_type=document_type or "Unknown",
        user_position=user_position or "Not specified",
        clauses_text=clauses_text,
    )
    return call_groq(system_prompt, question, json_mode=False)