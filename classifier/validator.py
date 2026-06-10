# ─────────────────────────────────────────────
# validator.py — JSON schema validation
# Strip extra fields, check required fields,
# validate types and ranges, trigger retry logic
# ─────────────────────────────────────────────

from classifier.config import THEMES, REQUIRED_LLM_FIELDS, SCORE_MIN, SCORE_MAX
from monitoring.logger import log_event


REQUIRED_SCHEMA = {
    "description_scores": dict,
    "activity_scores": list,
    "bolded_terms": list,
    "reasoning": str,
}


def validate_and_clean(
    parsed: dict,
    package_id: str,
    attempt: int = 1
) -> tuple[dict | None, list[str], list[str]]:
    """
    Validate LLM output against required schema.
    Strip extra fields silently.
    Return missing fields for retry decision.

    Args:
        parsed: Parsed dict from LLM response
        package_id: For logging
        attempt: 1 = first run, 2 = retry

    Returns:
        (cleaned dict or None, missing_fields list, warnings list)
    """
    if not isinstance(parsed, dict):
        log_event(package_id, "parse_failure", [], "human_review", False, attempt)
        return None, ["entire_response"], []

    missing = []
    warnings = []
    cleaned = {}

    # ── Check required fields ─────────────────
    for field, expected_type in REQUIRED_SCHEMA.items():
        if field not in parsed:
            missing.append(field)
        elif not isinstance(parsed[field], expected_type):
            missing.append(field)
            warnings.append(f"Field '{field}' has wrong type: expected {expected_type.__name__}")
        else:
            cleaned[field] = parsed[field]

    # ── Strip extra fields ────────────────────
    extra_fields = [k for k in parsed if k not in REQUIRED_SCHEMA]
    if extra_fields:
        log_event(package_id, "extra_fields", extra_fields, "strip", True, attempt)
        warnings.append(f"Stripped extra fields: {extra_fields}")

    if missing:
        action = "rerun" if attempt == 1 else "human_review"
        resolved = attempt == 2 and len(missing) == 0
        log_event(package_id, "missing_fields", missing, action, resolved, attempt)
        return None, missing, warnings

    # ── Validate description_scores ───────────
    desc_scores = cleaned.get("description_scores", {})
    for theme in THEMES:
        if theme not in desc_scores:
            missing.append(f"description_scores.{theme}")
        else:
            score = desc_scores[theme]
            if not isinstance(score, (int, float)):
                warnings.append(f"description_scores.{theme} is not a number — defaulting to 0")
                cleaned["description_scores"][theme] = 0
            else:
                cleaned["description_scores"][theme] = max(SCORE_MIN, min(SCORE_MAX, int(score)))

    # ── Validate activity_scores ──────────────
    valid_activities = []
    for i, act in enumerate(cleaned.get("activity_scores", [])):
        if not isinstance(act, dict):
            warnings.append(f"Activity {i} is not a dict — skipped")
            continue

        act_name = act.get("activity_name", f"Activity {i+1}")
        duration = act.get("duration_hours", 0)
        scores = act.get("scores", {})

        if not isinstance(scores, dict):
            warnings.append(f"Activity '{act_name}' has no valid scores — skipped")
            continue

        clean_scores = {}
        for theme in THEMES:
            s = scores.get(theme, 0)
            clean_scores[theme] = max(SCORE_MIN, min(SCORE_MAX, int(s) if isinstance(s, (int, float)) else 0))

        valid_activities.append({
            "activity_name": str(act_name),
            "duration_hours": float(duration) if isinstance(duration, (int, float)) else 0.0,
            "scores": clean_scores,
        })

    cleaned["activity_scores"] = valid_activities

    # ── Validate bolded_terms ─────────────────
    bolded = cleaned.get("bolded_terms", [])
    cleaned["bolded_terms"] = [str(t) for t in bolded if t]

    # ── Validate reasoning ────────────────────
    if not cleaned.get("reasoning", "").strip():
        cleaned["reasoning"] = "No reasoning provided."
        warnings.append("Reasoning field was empty — defaulted.")

    return cleaned, missing, warnings
