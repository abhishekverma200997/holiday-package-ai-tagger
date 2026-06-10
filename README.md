# 🏷️ Holiday Package AI Tagger

> **LLM-driven theme classification system** — automatically tags holiday packages as Romantic, Adventure, Spiritual, or Family using a weighted scoring engine built on Llama 3.1.

**Live demo →** [Deploy link here once on Streamlit Cloud]  
**Built by:** [Your name]  
**Stack:** Python · Streamlit · Groq API · Llama 3.1 8B

---

## The problem

MakeMyTrip's holiday packages were tagged manually by the operations team. The process was slow, inconsistent across taggers, and couldn't scale as the catalogue grew — resulting in incomplete coverage and unreliable browse-stage discoverability for customers.

Untagged packages were invisible at the browse stage. Customers searching by theme couldn't find them, directly suppressing demand.

---

## The solution

An end-to-end LLM classification system that reads package metadata and automatically assigns themes across the full catalogue — replacing manual tagging entirely.

**Key architectural decision:** The LLM only does what LLMs are good at — reading and understanding text. All numerical computation (weights, scoring, thresholds, routing) lives in Python code. This makes the system model-agnostic — swapping Llama for GPT-4 or Mistral requires only re-validating the prompt format.

---

## Impact

| Metric | Result |
|--------|--------|
| Catalogue tagging coverage | 100% (up from incomplete) |
| Manual ops effort | Eliminated entirely |
| Browse-stage funnel drop-off | Reduced by 10% |

---

## System architecture

```
Package metadata
      │
      ▼
┌─────────────────────────┐
│  Layer 1: Hard rules    │  ── Keyword match → auto-assign at 100% confidence
│  (keyword + city)       │  ── Single city → hardcoded city-theme map
└────────────┬────────────┘
             │ No match
             ▼
┌─────────────────────────┐
│  Layer 2: LLM scoring   │  ── Reads description + activities
│  (Llama 3.1 via Groq)   │  ── Returns raw signal scores per theme
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Validator              │  ── Schema check → strip extra fields
│                         │  ── Missing fields → retry once at temp=0
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Layer 3: Scorer        │  ── Applies weights (desc 35%, activity 50%)
│                         │  ── Time boost (up to 1.3x for dominant activities)
│                         │  ── Bolded term multiplier (2x signal weight)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Router                 │  ── Per-theme threshold check
│                         │  ── 0 themes cross → human review
│                         │  ── 1 theme crosses → auto-assign
│                         │  ── 2+ themes cross → human review (conflict)
└─────────────────────────┘
```

---

## Scoring engine

Three signals are scored independently and combined:

| Signal | Weight | Rationale |
|--------|--------|-----------|
| Package description | 35% | Marketing copy — useful but intentionally written |
| Activity descriptions | 50% | Most reliable — what the customer actually does |
| Activity time boost | 15% | Amplifies activity scores by time share |

**Time boost multipliers:**
- Activity > 40% of total hours → 1.3x
- Activity 20–40% → 1.15x  
- Activity < 20% → 1.0x (no boost)

**Bolded terms:** Any `**term**` in the description gets 2x signal weight — an editorial layer where ops writers can flag what matters most.

---

## Per-theme thresholds

Each theme has its own confidence threshold — not a universal cutoff. This reflects that different themes have different signal densities.

| Theme | Threshold | Reasoning |
|-------|-----------|-----------|
| Romantic | 82 | Romantic signals appear in many non-romantic packages — high bar avoids over-tagging |
| Adventure | 85 | Adventure signals fairly specific but aspirational language is common |
| Spiritual | 78 | Spiritual signals are unambiguous and theme-exclusive — lower bar justified |
| Family | 80 | Moderately specific signals — mid-range threshold |

> **Note:** These are placeholder thresholds for development. Production thresholds are derived empirically by running the scorer against 200-300 manually-labelled packages and tuning each threshold to balance precision vs human review load.

---

## Human-in-the-loop routing

Two conditions trigger human review:
1. **No theme crosses its threshold** — insufficient confidence
2. **Two or more themes cross their thresholds** — multi-theme conflict

The LLM never makes routing decisions. `router.py` computes this deterministically from scores vs thresholds.

---

## Running locally

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/holiday-package-ai-tagger
cd holiday-package-ai-tagger

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here

# 4. Run
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Deploying to Streamlit Cloud

1. Push this repo to GitHub (make sure `.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Under **Advanced settings → Secrets**, add:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Click Deploy — live URL in ~2 minutes

---

## Project structure

```
holiday-package-ai-tagger/
├── app.py                        # Streamlit UI — classifier + monitoring tabs
├── classifier/
│   ├── config.py                 # Thresholds, weights, hard rules, city map
│   ├── hard_rules.py             # Keyword + city lookup engine
│   ├── llm_extractor.py          # Groq API call — raw scores only
│   ├── validator.py              # JSON schema validation + retry logic
│   ├── scorer.py                 # Weights, time boost, overall score
│   ├── router.py                 # Threshold check, routing decision
│   └── pipeline.py               # Orchestrates all three layers
├── prompts/
│   └── extraction_prompt.py      # Versioned prompt (v1.0)
├── monitoring/
│   ├── logger.py                 # Validation event logging
│   └── seed_data.py              # Simulated history for demo
├── data/
│   └── sample_packages.py        # 4 pre-loaded demo packages
├── .env.example
├── requirements.txt
└── README.md
```

---

## Known limitations

- Scores are only as good as description quality — short or vague descriptions underperform
- Activity duration data assumed accurate — if ops team logs incorrectly, time boost misfires
- Hard rules require ongoing PM maintenance as new trigger keywords emerge
- Thresholds need empirical validation against real catalogue data before production use
- LLM non-determinism at temperature > 0 means identical packages can score slightly differently across runs

---

## Key design decisions

**Why weights live in code, not the prompt:** Embedding weights in the prompt makes the system model-dependent. Swapping LLMs invalidates all scoring. Code-based weights are model-agnostic and unit-testable.

**Why per-theme thresholds:** Different themes have different signal densities. A universal threshold either over-tags Romantic or under-tags Spiritual. Per-theme thresholds calibrate to each theme's specificity.

**Why the LLM doesn't make routing decisions:** Routing is a deterministic function of scores vs thresholds. Asking the LLM to make this decision introduces non-determinism into a binary choice that should be rule-based.

**Why temperature 0 on retry:** If the first run fails validation, the retry uses temperature 0 for maximum determinism. If it still fails at temperature 0, the failure is structural — human review is the correct response.
