# ─────────────────────────────────────────────
# monitoring/seed_data.py
# Simulated historical validation log entries
# for portfolio demo purposes.
# Shows the monitoring dashboard with real data.
# ─────────────────────────────────────────────

import json
import os
from datetime import datetime, timedelta
import random

random.seed(42)

LOG_FILE = "monitoring/validation_log.jsonl"


def seed_historical_data():
    """
    Generate 60 days of simulated classification history.
    Includes realistic distribution of events.
    Only runs if log file doesn't already exist.
    """
    if os.path.exists(LOG_FILE):
        return

    os.makedirs("monitoring", exist_ok=True)
    entries = []
    base_date = datetime.utcnow() - timedelta(days=60)
    themes = ["romantic", "adventure", "spiritual", "family"]
    layers = ["hard_rule", "city_rule", "llm", "llm", "llm", "llm"]

    package_counter = 1000

    for day in range(60):
        day_date = base_date + timedelta(days=day)
        # 15-25 packages per day
        daily_count = random.randint(15, 25)

        for _ in range(daily_count):
            pkg_id = f"PKG_{package_counter}"
            package_counter += 1
            layer = random.choice(layers)
            decision = random.choices(
                ["auto_assign", "human_review"],
                weights=[75, 25]
            )[0]
            theme = random.choice(themes) if decision == "auto_assign" else None
            score = round(random.uniform(78, 96), 1) if decision == "auto_assign" else round(random.uniform(55, 77), 1)

            entries.append({
                "type":           "classification",
                "package_id":     pkg_id,
                "decision":       decision,
                "assigned_theme": theme,
                "overall_score":  score,
                "themes_crossed": [theme] if theme else [],
                "layer":          layer,
                "timestamp":      (day_date + timedelta(
                    hours=random.randint(8, 20),
                    minutes=random.randint(0, 59)
                )).isoformat(),
            })

            # 4% missing field rate
            if random.random() < 0.04:
                field = random.choice(["reasoning", "bolded_terms", "activity_scores"])
                resolved_on_retry = random.random() < 0.82
                ts = (day_date + timedelta(hours=random.randint(8, 20))).isoformat()
                # Attempt 1 — initial failure, triggers rerun
                entries.append({
                    "package_id":      pkg_id,
                    "event":           "missing_fields",
                    "fields_affected": [field],
                    "action_taken":    "rerun",
                    "resolved":        False,
                    "attempt":         1,
                    "timestamp":       ts,
                })
                # Attempt 2 — the retry result
                entries.append({
                    "package_id":      pkg_id,
                    "event":           "missing_fields",
                    "fields_affected": [] if resolved_on_retry else [field],
                    "action_taken":    "resolved" if resolved_on_retry else "human_review",
                    "resolved":        resolved_on_retry,
                    "attempt":         2,
                    "timestamp":       ts,
                })

            # 1.5% extra field rate
            if random.random() < 0.015:
                entries.append({
                    "package_id":      pkg_id,
                    "event":           "extra_fields",
                    "fields_affected": [random.choice(["confidence", "overall_recommendation", "summary"])],
                    "action_taken":    "strip",
                    "resolved":        True,
                    "attempt":         1,
                    "timestamp":       (day_date + timedelta(
                        hours=random.randint(8, 20)
                    )).isoformat(),
                })

    # Sort by timestamp
    entries.sort(key=lambda x: x["timestamp"])

    with open(LOG_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
