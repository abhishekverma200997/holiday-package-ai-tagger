# ─────────────────────────────────────────────
# config.py — Single source of truth
# All thresholds, weights, rules, city mappings
# Only PM + Engineering should modify this file
# ─────────────────────────────────────────────

# ── Themes ────────────────────────────────────
THEMES = ["romantic", "adventure", "spiritual", "family"]

# ── Scoring weights ───────────────────────────
# These live in code, NOT the prompt — making the
# system model-agnostic. Swap LLMs without rebuilding.
WEIGHTS = {
    "description": 0.35,   # Package description (marketing copy — useful but biased)
    "activity":    0.50,   # Activity descriptions (most reliable — what customer actually does)
    "time_boost":  0.15,   # Time share amplifier (applied on top of activity scores)
}

# ── Activity time boost multipliers ───────────
# Applied per-activity based on its share of total hours
TIME_BOOST = {
    "high":   1.30,   # Activity > 40% of total hours
    "medium": 1.15,   # Activity 20–40% of total hours
    "low":    1.00,   # Activity < 20% — no boost
}

# ── Bolded term multiplier ────────────────────
# **term** in description = 2x signal weight
BOLD_MULTIPLIER = 2.0

# ── Group composition multipliers ────────────
# Applied as a post-LLM multiplier on the relevant theme's
# combined score (description + activity weighted).
# Placeholder values — tune empirically against labelled data.
#
# Logic:
#   2 adults, 0 children   → Romantic signal → boost Romantic score
#   2+ adults, 1+ children → Family signal   → boost Family score
#   All other combinations → neutral          → no boost applied
GROUP_COMPOSITION_MULTIPLIER = {
    "romantic": 1.25,   # Applied when group is 2 adults, 0 children
    "family":   1.25,   # Applied when group has 1+ children
}

# Group type labels used in UI and scoring logic
GROUP_TYPES = {
    "couple":      "2 adults, no children",
    "family":      "2+ adults with children",
    "solo":        "Solo traveller",
    "friends":     "Group of adults",
    "unspecified": "Not specified",
}

# ── Per-theme assignment thresholds ──────────
# IMPORTANT: These are placeholder values for development.
# Production thresholds must be derived empirically by running
# the scorer against 200-300 manually-labelled packages and
# tuning each threshold to balance precision vs human review load.
#
# Threshold reasoning:
#   romantic  82 — romantic signals appear in many non-romantic packages; high bar avoids over-tagging
#   adventure 85 — adventure signals fairly specific but aspirational language is common
#   spiritual 78 — spiritual signals unambiguous and theme-exclusive; lower bar justified
#   family    80 — moderately specific signals; mid-range threshold
THRESHOLDS = {
    "romantic":   82,
    "adventure":  80,
    "spiritual":  78,
    "family":     80,
}

# ── Hard rule keywords ────────────────────────
# Instantly assigns theme at 100% confidence — bypasses all scoring
# Only PM + Engineering can add or modify these
HARD_RULES = {
    "romantic": [
        "honeymoon", "honeymoon package", "honeymoon special",
        "anniversary special", "couples only", "romantic getaway",
    ],
    "spiritual": [
        "yatra", "kashi vishwanath", "char dham", "jyotirlinga",
        "pilgrimage", "amarnath", "kedarnath", "vaishno devi",
        "tirupati darshan", "shirdi", "puri jagannath",
    ],
    "family": [
        "school holiday special", "kids special package",
    ]
}

# ── City → theme mapping ──────────────────────
# Single city packages → hard-coded theme lookup
# Multiple cities → LLM takes over
# Only PM + Engineering can modify this mapping
CITY_THEME_MAP = {
    # Spiritual cities
    "varanasi": "spiritual",
    "rishikesh": "spiritual",
    "haridwar": "spiritual",
    "tirupati": "spiritual",
    "shirdi": "spiritual",
    "amritsar": "spiritual",
    "puri": "spiritual",
    "dwarka": "spiritual",
    "mathura": "spiritual",
    "vrindavan": "spiritual",
    "bodh gaya": "spiritual"
}

# ── LLM configuration ─────────────────────────
LLM_MODEL         = "llama-3.1-8b-instant"
LLM_TEMPERATURE   = 0.3
LLM_RETRY_TEMP    = 0.0    # Temperature 0 on retry — maximum determinism
LLM_MAX_TOKENS    = 1500

# ── Validation thresholds ─────────────────────
SCORE_MIN = 0
SCORE_MAX = 100

# ── Required JSON schema from LLM ────────────
REQUIRED_LLM_FIELDS = [
    "description_scores",
    "activity_scores",
    "bolded_terms",
    "reasoning",
]

# ── Monitoring alert thresholds ───────────────
ALERT_MISSING_FIELD_RATE   = 0.05   # Alert if > 5% packages have missing fields
ALERT_RETRY_RESOLUTION_MIN = 0.60   # Alert if retry resolves < 60% of failures
ALERT_THRESHOLD_FLIPS      = 3      # Alert if golden set shows 3+ routing flips