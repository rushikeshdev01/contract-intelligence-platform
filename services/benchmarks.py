from agents.state import ContractState
from services.groq_client import call_groq_json
from services.benchmarks import BENCHMARKS, evaluate_status

SYSTEM_PROMPT = """You are a contract data extraction assistant.
Read the contract text and try to find the following provisions. For each one
that IS present in the contract, extract its duration and convert it to a
number of days (e.g. "12 months" -> 365, "90 days" -> 90, "2 years" -> 730,
"1 month" -> 30). If a provision is not mentioned, omit it from the output
entirely — do not guess or invent a value.

Provisions to look for:
- liability_cap: the liability cap duration (often stated as "X months' fees")
- auto_renewal_notice: notice period required before auto-renewal
- termination_notice: notice period required to terminate the agreement
- non_compete_duration: length of any non-compete obligation
- confidentiality_duration: length of confidentiality/NDA obligations
- cure_period: time allowed to fix a breach before termination

Return ONLY valid JSON in this exact shape (omit keys that aren't found):
{"liability_cap": 365, "termination_notice": 60}
"""


def analyze_benchmarks(state: ContractState) -> ContractState:
    raw_text = state.get("raw_text", "")
    if not raw_text:
        return state  # nothing to do, don't block the pipeline over this

    extracted = call_groq_json(SYSTEM_PROMPT, raw_text)

    if "error" in extracted:
        # Benchmarking is a bonus feature — don't fail the whole pipeline over it
        return {**state, "benchmarks": []}

    rows = []
    for key, value_days in extracted.items():
        if key not in BENCHMARKS:
            continue
        try:
            value_days = float(value_days)
        except (TypeError, ValueError):
            continue

        status = evaluate_status(key, value_days)
        rows.append({
            "provision": BENCHMARKS[key]["label"],
            "contract_value_days": value_days,
            "standard_range": f'{BENCHMARKS[key]["standard_min"]}-{BENCHMARKS[key]["standard_max"]} days',
            "status": status,  # "green" | "yellow" | "red"
        })

    return {**state, "benchmarks": rows}