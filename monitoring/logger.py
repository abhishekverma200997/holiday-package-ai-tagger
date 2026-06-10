# ─────────────────────────────────────────────
# monitoring/logger.py
# Validation event logging
# Every strip, retry, and failure is recorded.
# Over time this log is your prompt health signal.
# ─────────────────────────────────────────────

import json
import os
from datetime import datetime

LOG_FILE = "monitoring/validation_log.jsonl"


def log_event(
    package_id: str,
    event_type: str,
    fields_affected: list,
    action_taken: str,
    resolved: bool,
    attempt: int,
):
    """
    Log a single validation event.

    event_type: missing_fields | extra_fields | parse_failure | invalid_type
    action_taken: strip | rerun | human_review
    resolved: True if fixed after retry
    """
    entry = {
        "package_id":      package_id,
        "event":           event_type,
        "fields_affected": fields_affected,
        "action_taken":    action_taken,
        "resolved":        resolved,
        "attempt":         attempt,
        "timestamp":       datetime.utcnow().isoformat(),
    }

    os.makedirs("monitoring", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_classification(
    package_id: str,
    decision: str,
    assigned_theme: str | None,
    overall_score: float,
    themes_crossed: list,
    layer: str,
):
    """Log every classification decision for audit trail."""
    entry = {
        "type":            "classification",
        "package_id":      package_id,
        "decision":        decision,
        "assigned_theme":  assigned_theme,
        "overall_score":   overall_score,
        "themes_crossed":  themes_crossed,
        "layer":           layer,
        "timestamp":       datetime.utcnow().isoformat(),
    }

    os.makedirs("monitoring", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_logs() -> list:
    """Load all log entries for the monitoring dashboard."""
    if not os.path.exists(LOG_FILE):
        return []
    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def compute_health_metrics(logs: list) -> dict:
    """
    Compute the five prompt health metrics from logs.
    """
    validation_events = [e for e in logs if e.get("event") in
                         ["missing_fields", "extra_fields", "parse_failure", "invalid_type"]]

    classification_events = [e for e in logs if e.get("type") == "classification"]
    total_classifications = len(classification_events)

    missing_events  = [e for e in validation_events if e.get("event") == "missing_fields"]
    extra_events    = [e for e in validation_events if e.get("event") == "extra_fields"]
    retry_events    = [e for e in missing_events if e.get("attempt") == 1]
    resolved_events = [e for e in missing_events if e.get("attempt") == 2 and e.get("resolved")]
    human_review_from_validation = [
        e for e in missing_events
        if e.get("action_taken") == "human_review"
    ]

    missing_rate = (
        len(set(e["package_id"] for e in missing_events)) / total_classifications
        if total_classifications > 0 else 0
    )
    extra_rate = (
        len(set(e["package_id"] for e in extra_events)) / total_classifications
        if total_classifications > 0 else 0
    )
    retry_resolution = (
        len(resolved_events) / len(retry_events)
        if retry_events else None
    )
    validation_hr_rate = (
        len(human_review_from_validation) / total_classifications
        if total_classifications > 0 else 0
    )

    # Field-level frequency
    field_counts = {}
    for e in missing_events:
        for field in e.get("fields_affected", []):
            field_counts[field] = field_counts.get(field, 0) + 1

    return {
        "total_classifications":    total_classifications,
        "missing_field_rate":       round(missing_rate * 100, 2),
        "extra_field_rate":         round(extra_rate * 100, 2),
        "retry_resolution_rate":    round(retry_resolution * 100, 2) if retry_resolution is not None else None,
        "validation_hr_rate":       round(validation_hr_rate * 100, 2),
        "field_level_frequency":    field_counts,
        "auto_assign_count":        sum(1 for e in classification_events if e.get("decision") == "auto_assign"),
        "human_review_count":       sum(1 for e in classification_events if e.get("decision") == "human_review"),
        "hard_rule_count":          sum(1 for e in classification_events if e.get("layer") == "hard_rule"),
    }
