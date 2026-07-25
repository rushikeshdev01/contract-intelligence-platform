import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Centralized model choice — change once here, applies everywhere
MODEL = "llama-3.3-70b-versatile"


def call_groq(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """
    Shared helper every agent uses to call Groq.
    json_mode=True forces the model to return valid JSON only —
    critical for agents like RiskAnalyzer whose output must be parseable.
    """
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )
    return response.choices[0].message.content


def call_groq_json(system_prompt: str, user_prompt: str) -> dict:
    """Convenience wrapper: calls Groq in JSON mode and parses the result safely."""
    raw = call_groq(system_prompt, user_prompt, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse model output as JSON", "raw": raw}
