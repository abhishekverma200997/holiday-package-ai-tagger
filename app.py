"""
Holiday Package AI Tagger
Streamlit app — two tabs:
  1. Classifier — run a package through the full pipeline
  2. Monitoring — prompt health dashboard
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sample_packages import SAMPLE_PACKAGES
from classifier.pipeline import classify_package
from classifier.config import THEMES, THRESHOLDS
from monitoring.logger import load_logs, compute_health_metrics
from monitoring.seed_data import seed_historical_data

# ── Page config ───────────────────────────────
st.set_page_config(
    page_title="Holiday Package AI Tagger",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Seed simulated monitoring data ────────────
seed_historical_data()

# ── Custom CSS ────────────────────────────────
st.markdown("""
<style>
.main { padding-top: 1rem; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 20px;
    border-radius: 8px;
    font-size: 14px;
}
.verdict-auto {
    background: #d6efe0; color: #1e6b3c;
    padding: 8px 16px; border-radius: 8px;
    font-weight: 600; display: inline-block;
    margin-bottom: 12px;
}
.verdict-review {
    background: #fde8d0; color: #7b3f00;
    padding: 8px 16px; border-radius: 8px;
    font-weight: 600; display: inline-block;
    margin-bottom: 12px;
}
.verdict-hard {
    background: #d6e4f0; color: #1f4e79;
    padding: 8px 16px; border-radius: 8px;
    font-weight: 600; display: inline-block;
    margin-bottom: 12px;
}
.metric-card {
    background: #f8f9fa; border-radius: 8px;
    padding: 16px; text-align: center;
    border: 1px solid #e9ecef;
}
.step-tag {
    font-size: 11px; padding: 3px 10px;
    border-radius: 6px; font-weight: 600;
    letter-spacing: 0.5px; margin-bottom: 8px;
    display: inline-block;
}
.tag-hard { background: #d6e4f0; color: #1f4e79; }
.tag-llm  { background: #f1efff; color: #3c3489; }
.tag-score { background: #eaf3de; color: #3b6d11; }
.tag-route { background: #faeeda; color: #633806; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────
st.title("🏷️ Holiday Package AI Tagger")
st.caption("Automated theme classification using LLM signal extraction + weighted scoring")

# ── Tabs ─────────────────────────────────────
tab1, tab2 = st.tabs(["🔍  Classifier", "📊  Monitoring Dashboard"])



def _render_result(result: dict):
    routing  = result.get("routing", {})
    scores   = result.get("scores")
    error    = result.get("error")
    layer    = result.get("layer_fired")

    if error and not routing:
        st.error(f"Pipeline error: {error}")
        return

    # ── Verdict badge ─────────────────────────
    decision = routing.get("decision", "")
    assigned = routing.get("assigned_theme")
    if decision == "auto_assign" and layer == "hard_rule":
        badge_class = "verdict-hard"
        badge_text  = f"⚡ Hard rule → {assigned.title()}"
    elif decision == "auto_assign" and layer == "city_rule":
        badge_class = "verdict-hard"
        badge_text  = f"🏙️ City rule → {assigned.title()}"
    elif decision == "auto_assign":
        badge_class = "verdict-auto"
        badge_text  = f"✓ Auto-assigned → {assigned.title()}"
    else:
        badge_class = "verdict-review"
        badge_text  = "⚠ Flagged for human review"

    st.markdown(f'<div class="{badge_class}">{badge_text}</div>', unsafe_allow_html=True)

    # ── Reason ────────────────────────────────
    st.markdown(f"_{routing.get('reason', '')}_")

    # Show group composition boost if applied
    if scores and scores.get("group_boost_applied"):
        st.info(f"👥 Group signal: {scores['group_boost_applied']}")

    st.divider()

    # ── Layer 1: Hard/city rule ───────────────
    st.markdown('<span class="step-tag tag-hard">Step 1 — Hard rules</span>', unsafe_allow_html=True)
    hard = result.get("hard_rule")
    city = result.get("city_rule")
    if hard:
        st.success(f"Keyword **'{hard['trigger']}'** matched in `{hard['source']}` → {hard['theme'].title()} at 100% confidence")
        return
    elif city and city.get("matched"):
        st.success(f"City **'{city['trigger'].title()}'** matched in city map → {city['theme'].title()} at 90% confidence")
        return
    else:
        st.caption("No hard rule or city match. Proceeding to LLM scoring.")

    if result.get("validation_warnings"):
        with st.expander("⚠ Validation warnings"):
            for w in result["validation_warnings"]:
                st.caption(f"• {w}")

    # ── Layer 2: LLM output ───────────────────
    st.markdown('<span class="step-tag tag-llm">Step 2 — LLM signal extraction</span>', unsafe_allow_html=True)
    llm = result.get("llm_output")
    if llm:
        with st.expander("LLM raw signals", expanded=False):
            st.markdown("**Description scores (raw, before weighting):**")
            desc_s = llm.get("description_scores", {})
            dcols = st.columns(4)
            for i, theme in enumerate(THEMES):
                dcols[i].metric(theme.title(), desc_s.get(theme, 0))

            if llm.get("bolded_terms"):
                st.markdown(f"**Bolded terms detected:** {', '.join(llm['bolded_terms'])}")

            if llm.get("activity_scores"):
                st.markdown("**Activity scores (raw):**")
                for act in llm["activity_scores"]:
                    s = act.get("scores", {})
                    st.caption(
                        f"**{act['activity_name']}** ({act['duration_hours']}h) — "
                        + " | ".join(f"{t.title()}: {s.get(t,0)}" for t in THEMES)
                    )

            st.markdown(f"**Reasoning:** _{llm.get('reasoning', '')}_")

    # ── Layer 3: Scoring ──────────────────────
    if scores:
        st.markdown('<span class="step-tag tag-score">Step 3 — Weighted scoring</span>', unsafe_allow_html=True)

        with st.expander("Scoring breakdown", expanded=False):
            ab = scores.get("activity_breakdown", [])
            if ab:
                st.caption("**Activity time boosts applied:**")
                for act in ab:
                    st.caption(
                        f"• {act['name']}: {act['time_share']}% of itinerary → "
                        f"boost {act['boost_label']}"
                    )

            dw = scores.get("description_weighted", {})
            aw = scores.get("activity_weighted", {})
            st.caption("**Weighted contributions per theme:**")
            for theme in THEMES:
                st.caption(
                    f"• {theme.title()}: description {dw.get(theme,0):.1f} "
                    f"+ activity {aw.get(theme,0):.1f}"
                )

        # ── Theme score bars ──────────────────
        st.markdown('<span class="step-tag tag-route">Step 4 — Threshold check</span>', unsafe_allow_html=True)
        theme_scores = scores.get("theme_scores", {})
        td = routing.get("threshold_detail", {})

        for theme in THEMES:
            score     = theme_scores.get(theme, 0)
            threshold = THRESHOLDS[theme]
            crossed   = td.get(theme, {}).get("crossed", False)
            pct       = min(score, 100)

            bar_color = "#1D9E75" if crossed else "#378ADD"
            label     = f"✓ crosses threshold" if crossed else f"threshold: {threshold}"

            col_a, col_b, col_c = st.columns([2, 5, 2])
            col_a.markdown(f"**{theme.title()}**")
            col_b.markdown(
                f'<div style="background:#eee;border-radius:4px;height:18px;margin-top:6px">'
                f'<div style="width:{pct}%;background:{bar_color};height:18px;border-radius:4px"></div>'
                f'</div>', unsafe_allow_html=True
            )
            col_c.markdown(f"`{score:.0f}` / {threshold} {label}")

        st.divider()
        oc1, oc2, oc3 = st.columns(3)
        oc1.metric("Overall score", f"{scores.get('overall_score', 0):.1f}")
        oc2.metric("Top theme", scores.get("top_theme", "—").title())
        oc3.metric("Gap", f"{scores.get('gap', 0):.1f} pts")




# ═══════════════════════════════════════════════
# TAB 1 — CLASSIFIER
# ═══════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Package input")

        input_mode = st.radio(
            "Input mode",
            ["Select a pre-loaded package", "Write your own"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if input_mode == "Select a pre-loaded package":
            pkg_labels = {v["label"]: k for k, v in SAMPLE_PACKAGES.items()}
            selected_label = st.selectbox(
                "Choose a package",
                options=list(pkg_labels.keys()),
            )
            selected_key = pkg_labels[selected_label]
            package = SAMPLE_PACKAGES[selected_key].copy()

            scenario_colors = {
                "Hard rule trigger": "🔵",
                "Single theme auto-assign": "🟢",
                "Multi-theme conflict → human review": "🟠",
                "No theme crosses threshold → human review": "🔴",
            }
            scenario = package.get("scenario", "")
            icon = scenario_colors.get(scenario, "⚪")
            st.info(f"{icon} **Scenario:** {scenario}")

            with st.expander("View package details", expanded=True):
                st.markdown(f"**Name:** {package['name']}")
                st.markdown(f"**Destination:** {package['destination']}")
                st.markdown(f"**Price tier:** {package['price_tier']}")
                st.markdown(f"**Hotel type:** {package['hotel_type']}")
                group_label = {
                    "couple":      "👫 2 adults, no children",
                    "family":      "👨‍👩‍👧 2+ adults with children",
                    "solo":        "🧍 Solo traveller",
                    "friends":     "👥 Group of adults",
                    "unspecified": "— Not specified",
                }.get(package.get("group_type", "unspecified"), "— Not specified")
                st.markdown(f"**Group composition:** {group_label}")
                st.markdown(f"**Description:**\n\n{package['description']}")
                if package.get("activities"):
                    st.markdown("**Activities:**")
                    for act in package["activities"]:
                        st.markdown(
                            f"- **{act['name']}** ({act['duration_hours']}h): {act['description']}"
                        )
        else:
            st.markdown("**Build a custom package:**")
            pkg_name = st.text_input("Package name", placeholder="e.g. Bali Honeymoon Retreat — 5 Nights")
            destination = st.text_input("Destination(s)", placeholder="e.g. Bali  or  Manali, Leh")
            price_tier = st.selectbox("Price tier", ["Budget", "Standard", "Premium", "Luxury"])
            hotel_type = st.text_input("Hotel type", placeholder="e.g. Overwater villa, Safari lodge")
            group_type = st.selectbox(
                "Group composition",
                options=["unspecified", "couple", "family", "solo", "friends"],
                format_func=lambda x: {
                    "couple":      "👫 2 adults, no children",
                    "family":      "👨‍👩‍👧 2+ adults with children",
                    "solo":        "🧍 Solo traveller",
                    "friends":     "👥 Group of adults",
                    "unspecified": "— Not specified",
                }[x],
                key="group_type"
            )
            description = st.text_area(
                "Description",
                placeholder="Write the package description. Use **double asterisks** around terms you want emphasised...",
                height=120,
            )

            st.markdown("**Activities** (add up to 5)")
            activities = []
            for i in range(3):
                with st.expander(f"Activity {i+1}", expanded=(i == 0)):
                    a_name = st.text_input(f"Name", key=f"aname_{i}", placeholder="e.g. Scuba diving")
                    a_desc = st.text_input(f"Description", key=f"adesc_{i}", placeholder="What does this involve?")
                    a_hours = st.number_input(f"Duration (hours)", key=f"ahours_{i}", min_value=0.0, max_value=48.0, value=0.0, step=0.5)
                    if a_name and a_hours > 0:
                        activities.append({"name": a_name, "description": a_desc, "duration_hours": a_hours})

            package = {
                "id": "CUSTOM_001",
                "name": pkg_name or "Custom Package",
                "destination": destination or "Unknown",
                "price_tier": price_tier,
                "hotel_type": hotel_type or "Standard",
                "description": description or "",
                "activities": activities,
                "group_type": group_type,
            }

        # ── API key check ─────────────────────
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            st.warning("⚠️ GROQ_API_KEY not set. Add it to your .env file.")
            st.code("GROQ_API_KEY=your_key_here", language="bash")

        run = st.button("▶  Run classifier", type="primary", use_container_width=True)

    # ── Results column ────────────────────────
    with col_right:
        st.subheader("Classification result")

        if run:
            with st.spinner("Running pipeline..."):
                result = classify_package(package)

            _render_result(result)
        else:
            st.markdown(
                "<div style='color:#888;margin-top:60px;text-align:center;'>"
                "Select a package and click <strong>Run classifier</strong>"
                "</div>",
                unsafe_allow_html=True
            )



# ═══════════════════════════════════════════════
# TAB 2 — MONITORING DASHBOARD
# ═══════════════════════════════════════════════
with tab2:
    st.subheader("Prompt health dashboard")
    st.caption("Aggregated from validation event log. Covers last 60 days of simulated history + live runs.")

    logs    = load_logs()
    metrics = compute_health_metrics(logs)

    if not logs:
        st.info("No classification runs yet. Run some packages in the Classifier tab.")
    else:
        # ── Top-line metrics ───────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total classified", metrics["total_classifications"])
        m2.metric("Auto-assigned",    metrics["auto_assign_count"])
        m3.metric("Human review",     metrics["human_review_count"])
        m4.metric("Hard rule fires",  metrics["hard_rule_count"])
        m5.metric(
            "Auto-assign rate",
            f"{round(metrics['auto_assign_count'] / metrics['total_classifications'] * 100, 1) if metrics['total_classifications'] > 0 else 0}%"
        )

        st.divider()

        # ── Health metrics ─────────────────────
        st.markdown("#### Validation health metrics")
        h1, h2, h3, h4 = st.columns(4)

        mfr = metrics["missing_field_rate"]
        h1.metric(
            "Missing field rate",
            f"{mfr}%",
            delta="⚠ Above alert threshold" if mfr > 5 else "✓ Healthy",
            delta_color="inverse" if mfr > 5 else "normal",
        )

        efr = metrics["extra_field_rate"]
        h2.metric(
            "Extra field rate",
            f"{efr}%",
            delta="⚠ Monitor" if efr > 5 else "✓ Normal",
            delta_color="inverse" if efr > 5 else "normal",
        )

        rr = metrics["retry_resolution_rate"]
        h3.metric(
            "Retry resolution rate",
            f"{rr}%" if rr is not None else "N/A",
            delta="⚠ Below threshold" if rr is not None and rr < 60 else "✓ Healthy",
            delta_color="inverse" if rr is not None and rr < 60 else "normal",
        )

        vhr = metrics["validation_hr_rate"]
        h4.metric(
            "Validation-triggered review",
            f"{vhr}%",
            delta="⚠ High" if vhr > 1 else "✓ Low",
            delta_color="inverse" if vhr > 1 else "normal",
        )

        st.divider()

        # ── Field-level frequency ──────────────
        st.markdown("#### Field-level missing frequency")
        st.caption("Which fields go missing most often — identifies weakest parts of the prompt.")

        field_counts = metrics.get("field_level_frequency", {})
        if field_counts:
            import pandas as pd
            df = pd.DataFrame(
                list(field_counts.items()),
                columns=["Field", "Missing count"]
            ).sort_values("Missing count", ascending=False)
            st.bar_chart(df.set_index("Field"))
        else:
            st.caption("No missing field events recorded yet.")

        st.divider()

        # ── Recent events ──────────────────────
        st.markdown("#### Recent validation events")
        validation_logs = [
            e for e in logs
            if e.get("event") in ["missing_fields", "extra_fields", "parse_failure"]
        ][-20:]

        if validation_logs:
            import pandas as pd
            rows = []
            for e in reversed(validation_logs):
                rows.append({
                    "Package":  e.get("package_id", ""),
                    "Event":    e.get("event", ""),
                    "Fields":   ", ".join(e.get("fields_affected", [])),
                    "Action":   e.get("action_taken", ""),
                    "Resolved": "✓" if e.get("resolved") else "✗",
                    "Attempt":  e.get("attempt", 1),
                    "Time":     e.get("timestamp", "")[:19],
                })
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No validation events in log yet.")

        # ── Alert status ───────────────────────
        st.divider()
        st.markdown("#### Alert status")
        alerts = []
        if mfr > 5:
            alerts.append(f"🔴 Missing field rate ({mfr}%) exceeds 5% alert threshold — investigate prompt")
        if rr is not None and rr < 60:
            alerts.append(f"🔴 Retry resolution rate ({rr}%) below 60% — retrying may be wasting tokens")
        if vhr > 1:
            alerts.append(f"🟠 Validation-triggered human review ({vhr}%) above 1% — check edge cases")
        if efr > 5:
            alerts.append(f"🟡 Extra field rate ({efr}%) above 5% — model may be going off-schema")

        if alerts:
            for a in alerts:
                st.warning(a)
        else:
            st.success("✓ All metrics within healthy thresholds")
