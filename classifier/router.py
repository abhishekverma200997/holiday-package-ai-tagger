# ─────────────────────────────────────────────
# router.py — Layer 3: Routing decision engine
# Checks theme scores against per-theme thresholds
# Determines: auto-assign, human review, reason
# The LLM never makes this decision — code does.
# ─────────────────────────────────────────────

from classifier.config import THEMES, THRESHOLDS


def route(scores: dict) -> dict:
    """
    Apply per-theme thresholds to determine routing.

    Rules:
      - Hard rule fired earlier → auto-assign (handled before this)
      - Exactly one theme crosses threshold → auto-assign
      - Zero themes cross threshold → human review (low confidence)
      - Two or more themes cross threshold → human review (conflict)

    Args:
        scores: dict of {theme: score} from scorer.py

    Returns:
        {
            "decision": "auto_assign" | "human_review",
            "assigned_theme": "romantic" | None,
            "human_review": True | False,
            "reason": str,
            "themes_crossed": list of themes that crossed threshold,
            "threshold_detail": {theme: {score, threshold, crossed}}
        }
    """
    threshold_detail = {}
    themes_crossed = []

    for theme in THEMES:
        score     = scores.get(theme, 0)
        threshold = THRESHOLDS[theme]
        crossed   = score >= threshold

        threshold_detail[theme] = {
            "score":     score,
            "threshold": threshold,
            "crossed":   crossed,
            "gap_to_threshold": round(score - threshold, 1),
        }

        if crossed:
            themes_crossed.append(theme)

    # ── Routing logic ─────────────────────────
    if len(themes_crossed) == 1:
        theme = themes_crossed[0]
        return {
            "decision":        "auto_assign",
            "assigned_theme":  theme,
            "human_review":    False,
            "reason":          f"{theme.title()} crossed its threshold "
                               f"({threshold_detail[theme]['score']} ≥ {THRESHOLDS[theme]}). "
                               f"Auto-assigned with confidence.",
            "themes_crossed":  themes_crossed,
            "threshold_detail": threshold_detail,
        }

    elif len(themes_crossed) == 0:
        top_theme = max(scores, key=scores.get)
        top_score = scores[top_theme]
        return {
            "decision":        "human_review",
            "assigned_theme":  None,
            "human_review":    True,
            "reason":          f"No theme crossed its threshold. "
                               f"Highest score: {top_theme.title()} at {top_score} "
                               f"(threshold: {THRESHOLDS[top_theme]}). "
                               f"Insufficient confidence — flagged for review.",
            "themes_crossed":  themes_crossed,
            "threshold_detail": threshold_detail,
        }

    else:
        crossed_str = " and ".join(
            f"{t.title()} ({threshold_detail[t]['score']})"
            for t in themes_crossed
        )
        return {
            "decision":        "human_review",
            "assigned_theme":  None,
            "human_review":    True,
            "reason":          f"Multi-theme conflict: {crossed_str} all crossed their thresholds. "
                               f"System cannot resolve — flagged for human review.",
            "themes_crossed":  themes_crossed,
            "threshold_detail": threshold_detail,
        }
