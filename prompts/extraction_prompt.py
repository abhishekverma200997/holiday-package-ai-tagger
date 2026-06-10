# ─────────────────────────────────────────────
# prompts/extraction_prompt.py
# Versioned prompt — v1.0
# LLM reads text, returns raw scores only.
# All computation (weights, boost, thresholds)
# happens in scorer.py and router.py — not here.
# ─────────────────────────────────────────────

PROMPT_VERSION = "v1.0"

SYSTEM_PROMPT = """You are a holiday package theme classifier. Your only job is to read package metadata and return structured JSON scores.

You score each package against four themes: romantic, adventure, spiritual, family.

CRITICAL RULES:
- Return ONLY valid JSON. No preamble, no explanation, no markdown fences.
- All scores must be integers between 0 and 100.
- Do not calculate weighted scores — return raw signal scores only.
- Do not make routing decisions — only score.
- If a field has no signal, return an empty list or 0 scores — do not invent data."""


def build_user_prompt(package: dict, city_priors: dict = None) -> str:
    """
    Build the user prompt from package metadata.
    Injects city priors if multi-city lookup found hardcoded cities.
    """
    activities_text = _format_activities(package.get("activities", []))
    city_prior_text = _format_city_priors(city_priors) if city_priors else ""

    prompt = f"""Score this holiday package against the four themes.

PACKAGE METADATA:
Name: {package.get('name', 'Not provided')}
Destination: {package.get('destination', 'Not provided')}
Price tier: {package.get('price_tier', 'Not provided')}
Hotel type: {package.get('hotel_type', 'Not provided')}

DESCRIPTION:
{package.get('description', 'Not provided')}
Note: Any term wrapped in **double asterisks** is an intentionally emphasised signal. Treat it as 2x the weight of the same term without asterisks.

ACTIVITIES:
{activities_text}
{city_prior_text}

THEME DEFINITIONS:
- romantic: Couples-oriented. Signals: honeymoon, anniversary, couples spa, intimate dining, private villa, sunset experiences, adults-only, partner activities.
- adventure: Physical challenge, outdoor activity. Signals: trekking, hiking, camping, river rafting, bungee, rock climbing, mountain biking, scuba diving, skydiving, high-altitude, expedition.
- spiritual: Devotional, religious, mindfulness. Signals: temple visits, pilgrimage, aarti, shrine, meditation, yoga retreat, sacred sites, monastery, religious festivals.
- family: Multi-generational, child-inclusive. Signals: kids club, family rooms, child-friendly, theme parks, group games, age-appropriate, school holiday.

SCORE CALIBRATION — use this scale precisely:
90-100: Dominant. Almost every signal points to this theme.
70-89:  Strong. Majority of signals align with this theme.
50-69:  Moderate. Clear signals present but not dominant.
30-49:  Weak. Incidental mentions only.
0-29:   Negligible. No meaningful signal for this theme.

IMPORTANT: Score themes independently. A package can score high on multiple themes. Do not normalise scores to sum to 100.

REQUIRED OUTPUT FORMAT — return this exact JSON structure, nothing else:
{{
  "description_scores": {{
    "romantic": <integer 0-100>,
    "adventure": <integer 0-100>,
    "spiritual": <integer 0-100>,
    "family": <integer 0-100>
  }},
  "activity_scores": [
    {{
      "activity_name": "<name>",
      "duration_hours": <number>,
      "scores": {{
        "romantic": <integer 0-100>,
        "adventure": <integer 0-100>,
        "spiritual": <integer 0-100>,
        "family": <integer 0-100>
      }}
    }}
  ],
  "bolded_terms": ["<term1>", "<term2>"],
  "reasoning": "<2-3 sentences on key signals detected and any ambiguity>"
}}"""

    return prompt


def _format_activities(activities: list) -> str:
    if not activities:
        return "No activities provided."

    lines = []
    for i, act in enumerate(activities, 1):
        name = act.get("name", f"Activity {i}")
        desc = act.get("description", "No description")
        hours = act.get("duration_hours", "Unknown")
        lines.append(f"{i}. {name} ({hours} hours)\n   {desc}")

    return "\n".join(lines)


def _format_city_priors(city_priors: dict) -> str:
    if not city_priors:
        return ""

    lines = ["\nCITY CONTEXT (use as supporting signal, not override):"]
    for city, theme in city_priors.items():
        lines.append(f"  - {city.title()} is typically associated with {theme} packages")

    return "\n".join(lines)
