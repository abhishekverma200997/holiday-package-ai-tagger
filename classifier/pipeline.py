# ─────────────────────────────────────────────
# classifier/pipeline.py
# Main orchestrator — runs a package through
# all three layers and returns full result
# ─────────────────────────────────────────────

from classifier.hard_rules import check_hard_rules, check_city_rule
from classifier.llm_extractor import extract_signals, parse_llm_response
from classifier.validator import validate_and_clean
from classifier.scorer import compute_scores
from classifier.router import route
from monitoring.logger import log_classification


def classify_package(package: dict) -> dict:
    """
    Full classification pipeline for a single package.

    Layer 1: Hard rules (keyword + city)
    Layer 2: LLM signal extraction + validation
    Layer 3: Scoring + routing decision

    Returns complete result dict for UI rendering.
    """
    package_id = package.get("id", "UNKNOWN")
    result = {
        "package_id":    package_id,
        "package_name":  package.get("name", ""),
        "layer_fired":   None,
        "hard_rule":     None,
        "city_rule":     None,
        "city_priors":   None,
        "llm_output":    None,
        "scores":        None,
        "routing":       None,
        "validation_warnings": [],
        "error":         None,
    }

    # ── Layer 1a: Hard rule keyword check ─────
    hard_match = check_hard_rules(package)
    if hard_match:
        result["layer_fired"] = "hard_rule"
        result["hard_rule"]   = hard_match
        routing = {
            "decision":       "auto_assign",
            "assigned_theme": hard_match["theme"],
            "human_review":   False,
            "reason":         f"Hard rule triggered by keyword '{hard_match['trigger']}' "
                              f"found in {hard_match['source']}. "
                              f"Theme auto-assigned at 100% confidence. Scoring bypassed.",
            "themes_crossed": [hard_match["theme"]],
            "threshold_detail": {},
        }
        result["routing"] = routing
        log_classification(
            package_id, "auto_assign", hard_match["theme"],
            100.0, [hard_match["theme"]], "hard_rule"
        )
        return result

    # ── Layer 1b: City rule check ─────────────
    city_match = check_city_rule(package)
    if city_match and city_match.get("matched"):
        result["layer_fired"] = "city_rule"
        result["city_rule"]   = city_match
        routing = {
            "decision":       "auto_assign",
            "assigned_theme": city_match["theme"],
            "human_review":   False,
            "reason":         f"Single city '{city_match['trigger'].title()}' matched "
                              f"hardcoded city-theme map → {city_match['theme'].title()}. "
                              f"Assigned at 90% confidence.",
            "themes_crossed": [city_match["theme"]],
            "threshold_detail": {},
        }
        result["routing"] = routing
        log_classification(
            package_id, "auto_assign", city_match["theme"],
            90.0, [city_match["theme"]], "city_rule"
        )
        return result

    # Store city priors for LLM context if multi-city
    if city_match and city_match.get("multi_city"):
        result["city_priors"] = city_match.get("city_priors", {})

    # ── Layer 2: LLM signal extraction ────────
    result["layer_fired"] = "llm"
    city_priors = result.get("city_priors")

    raw_text, error = extract_signals(package, city_priors, is_retry=False)
    if error:
        result["error"] = error
        return _human_review_result(result, f"LLM call failed: {error}")

    parsed, parse_error = parse_llm_response(raw_text)
    if parse_error:
        # Retry once at temperature 0
        raw_text, error = extract_signals(package, city_priors, is_retry=True)
        if error:
            return _human_review_result(result, f"LLM retry failed: {error}")
        parsed, parse_error = parse_llm_response(raw_text)
        if parse_error:
            return _human_review_result(result, "JSON parse failed after retry.")

    # ── Validate + clean LLM output ───────────
    cleaned, missing, warnings = validate_and_clean(parsed, package_id, attempt=1)
    result["validation_warnings"] = warnings

    if missing:
        # Retry for this package only at temperature 0
        raw_text, error = extract_signals(package, city_priors, is_retry=True)
        if not error:
            parsed2, _ = parse_llm_response(raw_text)
            if parsed2:
                cleaned, missing2, warnings2 = validate_and_clean(parsed2, package_id, attempt=2)
                result["validation_warnings"] += warnings2
                if missing2:
                    return _human_review_result(
                        result, f"Required fields still missing after retry: {missing2}"
                    )
            else:
                return _human_review_result(result, "JSON invalid after retry.")
        else:
            return _human_review_result(result, f"Retry failed: {error}")

    result["llm_output"] = cleaned

    # ── Layer 3: Scoring ───────────────────────
    group_type = package.get('group_type', 'unspecified')
    scores = compute_scores(cleaned, package, group_type)
    result["scores"] = scores

    # ── Layer 3: Routing ───────────────────────
    routing = route(scores["theme_scores"])
    result["routing"] = routing

    log_classification(
        package_id,
        routing["decision"],
        routing["assigned_theme"],
        scores["overall_score"],
        routing["themes_crossed"],
        "llm"
    )

    return result


def _human_review_result(result: dict, reason: str) -> dict:
    result["routing"] = {
        "decision":        "human_review",
        "assigned_theme":  None,
        "human_review":    True,
        "reason":          reason,
        "themes_crossed":  [],
        "threshold_detail": {},
    }
    log_classification(
        result["package_id"], "human_review", None, 0.0, [], "validation_failure"
    )
    return result
