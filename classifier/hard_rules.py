# ─────────────────────────────────────────────
# hard_rules.py — Layer 1 of the classification pipeline
# Keyword trigger engine + city lookup
# Bypasses all scoring when a match is found
# ─────────────────────────────────────────────

from classifier.config import HARD_RULES, CITY_THEME_MAP


def check_hard_rules(package: dict) -> dict | None:
    """
    Check package text against hard rule keywords.
    Returns a result dict if matched, None if no match.

    Hard rules fire on:
      - Package name
      - Package description
      - Activity descriptions

    Returns:
        {
            "matched": True,
            "theme": "spiritual",
            "trigger": "yatra",
            "source": "description",
            "confidence": 100,
            "layer": "hard_rule"
        }
    """
    text_fields = _extract_text_fields(package)

    for field_name, text in text_fields.items():
        text_lower = text.lower()
        for theme, keywords in HARD_RULES.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return {
                        "matched": True,
                        "theme": theme,
                        "trigger": keyword,
                        "source": field_name,
                        "confidence": 100,
                        "layer": "hard_rule",
                    }
    return None


def check_city_rule(package: dict) -> dict | None:
    """
    Single-city packages: look up city in hardcoded theme map.
    Multi-city packages: return None — LLM handles these.

    Looks at package["destination"] which can be a string or list.

    Returns:
        {
            "matched": True,
            "theme": "romantic",
            "trigger": "maldives",
            "source": "city_lookup",
            "confidence": 90,
            "layer": "city_rule"
        }
    """
    destination = package.get("destination", "")

    # Normalise to list
    if isinstance(destination, str):
        cities = [c.strip().lower() for c in destination.split(",") if c.strip()]
    else:
        cities = [c.strip().lower() for c in destination]

    if len(cities) == 0:
        return None

    if len(cities) == 1:
        city = cities[0]
        theme = CITY_THEME_MAP.get(city)
        if theme:
            return {
                "matched": True,
                "theme": theme,
                "trigger": city,
                "source": "city_lookup",
                "confidence": 90,
                "layer": "city_rule",
            }
        return None

    # Multiple cities — check if any hardcoded city exists and pass as prior to LLM
    city_priors = {}
    for city in cities:
        theme = CITY_THEME_MAP.get(city)
        if theme:
            city_priors[city] = theme

    if city_priors:
        return {
            "matched": False,
            "multi_city": True,
            "city_priors": city_priors,
            "layer": "city_prior",
        }

    return None


def _extract_text_fields(package: dict) -> dict:
    """Extract all text fields from package for keyword scanning."""
    fields = {}

    if package.get("name"):
        fields["package_name"] = package["name"]

    if package.get("description"):
        fields["description"] = package["description"]

    activities = package.get("activities", [])
    if activities:
        activity_text = " ".join(
            f"{a.get('name', '')} {a.get('description', '')}"
            for a in activities
        )
        fields["activities"] = activity_text

    return fields
