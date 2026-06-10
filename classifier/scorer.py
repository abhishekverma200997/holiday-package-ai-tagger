# ─────────────────────────────────────────────
# scorer.py — Weighted scoring engine
# Applies description weight, activity weight,
# time boost, bolded term multiplier.
# Computes final theme scores and overall score.
# Model-agnostic — no LLM calls here.
# ─────────────────────────────────────────────

import re
from classifier.config import (
    THEMES, WEIGHTS, TIME_BOOST, BOLD_MULTIPLIER,
    GROUP_COMPOSITION_MULTIPLIER, SCORE_MIN, SCORE_MAX
)


def compute_scores(llm_output: dict, package: dict, group_type: str = 'unspecified') -> dict:
    """
    Compute final weighted theme scores from validated LLM output.

    Pipeline:
      1. Description scores x description weight (0.35)
      2. Activity scores weighted by time share x activity weight (0.50)
         Each activity contributes proportionally to its share of total hours
         so combined activity score stays within 0-100 range
      3. Bolded term bonus applied to description scores
      4. Combined weighted score per theme — capped at 100
      5. Group composition multiplier applied to Romantic or Family score
      6. Overall score = top score + gap bonus
    """
    description  = package.get("description", "")
    bolded_terms = llm_output.get("bolded_terms", [])
    desc_scores  = llm_output.get("description_scores", {})
    act_scores   = llm_output.get("activity_scores", [])

    # ── Step 1: Description scores with bold boost ──
    bold_boosts  = _detect_bold_boost(description, bolded_terms, desc_scores)
    desc_weighted = {}
    for theme in THEMES:
        raw     = desc_scores.get(theme, 0)
        boost   = bold_boosts.get(theme, 1.0)
        boosted = min(SCORE_MAX, raw * boost)
        desc_weighted[theme] = round(boosted * WEIGHTS["description"], 2)

    # ── Step 2: Activity scores — time-share normalised ──
    # Each activity contributes proportionally to its share of total hours.
    # This ensures combined activity score stays within 0-100 regardless
    # of how many activities the package has.
    total_hours = sum(a.get("duration_hours", 0) for a in act_scores)
    act_accumulator   = {theme: 0.0 for theme in THEMES}
    activity_weighted = {theme: 0.0 for theme in THEMES}
    activity_breakdown = []

    for act in act_scores:
        hours  = act.get("duration_hours", 0)
        scores = act.get("scores", {})
        name   = act.get("activity_name", "Unknown")

        time_share  = (hours / total_hours) if total_hours > 0 else 0
        boost_mult  = _get_time_boost(time_share)
        boost_label = _get_boost_label(time_share)

        act_contribution = {}
        for theme in THEMES:
            raw     = scores.get(theme, 0)
            boosted = min(SCORE_MAX, raw * boost_mult)
            # Weight contribution by time share — activities sum to ≤ 100
            act_accumulator[theme] += boosted * time_share
            act_contribution[theme] = round(boosted, 1)

        activity_breakdown.append({
            "name":           name,
            "hours":          hours,
            "time_share":     round(time_share * 100, 1),
            "boost_mult":     boost_mult,
            "boost_label":    boost_label,
            "raw_scores":     scores,
            "boosted_scores": act_contribution,
        })

    # Apply activity weight to time-share-normalised accumulator
    for theme in THEMES:
        activity_weighted[theme] = round(
            min(SCORE_MAX, act_accumulator[theme]) * WEIGHTS["activity"], 2
        )

    # ── Step 3: Combine description + activity — cap at 100 ──
    combined = {}
    for theme in THEMES:
        combined[theme] = round(
            min(SCORE_MAX, desc_weighted[theme] + activity_weighted[theme]), 1
        )

    # ── Step 4: Group composition multiplier ──────
    # Applied post-LLM as a soft signal boost on the relevant theme.
    # Does not override scoring — amplifies an existing signal.
    group_boost_applied = None
    if group_type == "couple" and combined.get("romantic", 0) > 0:
        multiplier = GROUP_COMPOSITION_MULTIPLIER["romantic"]
        combined["romantic"] = round(min(SCORE_MAX, combined["romantic"] * multiplier), 1)
        group_boost_applied = f"Romantic boosted x{multiplier} — group is a couple (2 adults, no children)"
    elif group_type == "family" and combined.get("family", 0) > 0:
        multiplier = GROUP_COMPOSITION_MULTIPLIER["family"]
        combined["family"] = round(min(SCORE_MAX, combined["family"] * multiplier), 1)
        group_boost_applied = f"Family boosted x{multiplier} — group includes children"

    # ── Step 5: Overall score with gap bonus ────────
    sorted_themes  = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    top_theme, top_score = sorted_themes[0]
    second_score   = sorted_themes[1][1] if len(sorted_themes) > 1 else 0
    gap            = round(top_score - second_score, 1)
    overall_score  = _compute_overall(top_score, gap)

    return {
        "theme_scores":         combined,
        "top_theme":            top_theme,
        "overall_score":        overall_score,
        "gap":                  gap,
        "description_weighted": desc_weighted,
        "activity_weighted":    {t: round(v, 2) for t, v in activity_weighted.items()},
        "activity_breakdown":   activity_breakdown,
        "bold_boosts":          bold_boosts,
        "bolded_terms":         bolded_terms,
        "reasoning":            llm_output.get("reasoning", ""),
        "total_activity_hours": total_hours,
        "group_type":            group_type,
        "group_boost_applied":   group_boost_applied,
    }


def _get_time_boost(time_share: float) -> float:
    if time_share > 0.40:
        return TIME_BOOST["high"]
    elif time_share >= 0.20:
        return TIME_BOOST["medium"]
    return TIME_BOOST["low"]


def _get_boost_label(time_share: float) -> str:
    if time_share > 0.40:
        return "high (1.3x)"
    elif time_share >= 0.20:
        return "medium (1.15x)"
    return "none (1.0x)"


def _detect_bold_boost(description: str, bolded_terms: list, desc_scores: dict) -> dict:
    """
    If bolded terms are present and they influence a theme,
    apply BOLD_MULTIPLIER to that theme's description score.
    Only applies to themes scoring above 50 — avoids inflating weak signals.
    """
    boosts = {theme: 1.0 for theme in THEMES}
    if not bolded_terms:
        return boosts

    desc_lower = description.lower()
    found = [t for t in bolded_terms if t.lower() in desc_lower]
    if not found:
        return boosts

    for theme in THEMES:
        if desc_scores.get(theme, 0) > 50:
            boosts[theme] = BOLD_MULTIPLIER

    return boosts


def _compute_overall(top_score: float, gap: float) -> float:
    """
    Overall score = top theme score + gap bonus.
    Gap bonus rewards clear winners over ambiguous ones.

      gap > 30  → x1.05 (clear winner — confident separation)
      gap 15-30 → x1.02 (moderate separation)
      gap < 15  → x1.00 (ambiguous — no bonus)
    """
    if gap > 30:
        multiplier = 1.05
    elif gap >= 15:
        multiplier = 1.02
    else:
        multiplier = 1.00

    return round(min(SCORE_MAX, top_score * multiplier), 1)
