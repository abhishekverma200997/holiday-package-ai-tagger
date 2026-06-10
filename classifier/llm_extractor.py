# ─────────────────────────────────────────────
# llm_extractor.py — Layer 2: LLM signal extraction
# Calls Groq API with Llama 3.1
# Returns raw signal scores only — no weights,
# no overall score, no routing decision.
# All computation happens downstream in scorer.py
# ─────────────────────────────────────────────

import os
import json
import re
from groq import Groq
from classifier.config import (
    LLM_MODEL, LLM_TEMPERATURE, LLM_RETRY_TEMP, LLM_MAX_TOKENS
)
from prompts.extraction_prompt import SYSTEM_PROMPT, build_user_prompt


def extract_signals(
    package: dict,
    city_priors: dict = None,
    is_retry: bool = False
) -> tuple[dict | None, str]:
    """
    Call the LLM and return raw signal scores.

    Args:
        package: Full package metadata dict
        city_priors: Optional city-to-theme priors from multi-city lookup
        is_retry: If True, uses temperature 0 for maximum determinism

    Returns:
        (raw_llm_output dict or None, error_message string)
    """
    client = _get_client()
    if client is None:
        return None, "GROQ_API_KEY not set. Add it to your .env file."

    temperature = LLM_RETRY_TEMP if is_retry else LLM_TEMPERATURE
    user_prompt = build_user_prompt(package, city_priors)

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            temperature=temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
        )
        raw_text = response.choices[0].message.content
        return raw_text, None

    except Exception as e:
        return None, f"LLM call failed: {str(e)}"


def _get_client() -> Groq | None:
    """Initialise Groq client from environment variable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def parse_llm_response(raw_text: str) -> tuple[dict | None, str]:
    """
    Parse raw LLM text output into a Python dict.
    Strips markdown fences before attempting json.loads().

    Returns:
        (parsed dict or None, error message)
    """
    if not raw_text:
        return None, "Empty response from LLM"

    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()
    cleaned = cleaned.strip("`").strip()

    # Find first { and last } — extract JSON block
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        return None, "No JSON object found in LLM response"

    json_str = cleaned[start:end]

    try:
        parsed = json.loads(json_str)
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {str(e)}"
