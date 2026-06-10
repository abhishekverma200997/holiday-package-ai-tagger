"""
Holiday Package AI Tagger
A polished, recruiter-facing Streamlit app demonstrating product + technical depth.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.sample_packages import SAMPLE_PACKAGES
from classifier.pipeline import classify_package
from classifier.config import THEMES, THRESHOLDS, WEIGHTS
from monitoring.logger import load_logs, compute_health_metrics
from monitoring.seed_data import seed_historical_data

st.set_page_config(
    page_title="Holiday Package AI Tagger",
    page_icon="\U0001F9ED",
    layout="wide",
    initial_sidebar_state="collapsed",
)

seed_historical_data()

THEME_COLORS = {
    "romantic":  "#E11D6B",
    "adventure": "#D97706",
    "spiritual": "#7C3AED",
    "family":    "#0D9488",
}

# ════════════════════════════════════════════════
# DESIGN SYSTEM
# ════════════════════════════════════════════════
st.markdown("""
<style>
.stApp { background: #FAFAF8; }
.main .block-container { padding-top: 2rem; max-width: 1180px; }
h1,h2,h3,h4 { font-family:'Inter',-apple-system,sans-serif; letter-spacing:-0.02em; }
.eyebrow { font-size:11px; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#2563EB; margin-bottom:8px; }
.big-hook { font-size:38px; font-weight:800; line-height:1.1; color:#1A2332; margin:0 0 14px 0; }
.sub-hook { font-size:18px; color:#51606F; line-height:1.5; font-weight:400; max-width:760px; }
.stTabs [data-baseweb="tab-list"] { gap:4px; background:#EFEEE9; padding:5px; border-radius:12px; border:1px solid #E2E0D8; }
.stTabs [data-baseweb="tab"] { padding:9px 22px; border-radius:8px; font-size:14px; font-weight:600; color:#51606F; background:transparent; }
.stTabs [aria-selected="true"] { background:#FFFFFF !important; color:#1A2332 !important; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
.stat-band { display:flex; gap:0; background:#1A2332; border-radius:14px; overflow:hidden; margin:24px 0 8px 0; }
.stat-cell { flex:1; padding:22px 26px; border-right:1px solid #2A3645; }
.stat-cell:last-child { border-right:none; }
.stat-num { font-size:30px; font-weight:800; color:#FFFFFF; line-height:1; }
.stat-lbl { font-size:12px; color:#8B98A8; margin-top:7px; font-weight:500; }
.stat-accent { color:#5B9BFF; }
.decision-card { background:#FFFFFF; border:1px solid #E8E6DE; border-radius:12px; padding:18px 20px; height:100%; border-top:3px solid #2563EB; }
.dc-title { font-size:15px; font-weight:700; color:#1A2332; margin-bottom:6px; }
.dc-decision { font-size:12.5px; color:#2563EB; font-weight:600; margin-bottom:10px; }
.dc-body { font-size:12.5px; color:#5C6B7A; line-height:1.55; }
.pipe-stage { background:#FFFFFF; border:1.5px solid #E2E0D8; border-radius:11px; padding:14px 18px; margin-bottom:10px; transition:all 0.3s ease; }
.pipe-stage.active { border-color:#2563EB; background:#F5F9FF; box-shadow:0 2px 10px rgba(37,99,235,0.12); }
.pipe-stage.dimmed { opacity:0.4; }
.pipe-num { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:6px; background:#EEF2F7; color:#51606F; font-size:12px; font-weight:700; margin-right:10px; }
.pipe-stage.active .pipe-num { background:#2563EB; color:#FFFFFF; }
.pipe-title { font-size:14px; font-weight:700; color:#1A2332; display:inline; }
.pipe-desc { font-size:12px; color:#6B7888; margin-top:6px; margin-left:32px; }
.verdict { padding:16px 20px; border-radius:12px; margin-bottom:6px; font-weight:700; font-size:17px; }
.v-auto { background:#E7F6EE; color:#0E7A43; border:1px solid #B6E2C8; }
.v-review { background:#FEF3E2; color:#9A5B00; border:1px solid #F3D9AE; }
.v-hard { background:#EAF1FB; color:#1E5BB8; border:1px solid #C4D8F5; }
.section-intro { font-size:15px; color:#51606F; line-height:1.6; max-width:820px; margin-bottom:6px; }
.tradeoff { background:#F5F9FF; border-left:3px solid #2563EB; padding:13px 17px; border-radius:0 8px 8px 0; font-size:13px; color:#3A4756; line-height:1.55; margin:10px 0; }
.tradeoff strong { color:#1E5BB8; }
.theme-chip { display:inline-block; padding:3px 11px; border-radius:20px; font-size:12px; font-weight:700; color:#FFFFFF; }
.layer-box { background:#FFFFFF; border:1px solid #E8E6DE; border-radius:12px; padding:18px 22px; margin-bottom:14px; }
.layer-label { font-size:11px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#8B98A8; margin-bottom:4px; }
.layer-h { font-size:17px; font-weight:700; color:#1A2332; margin-bottom:8px; }
.layer-p { font-size:13.5px; color:#51606F; line-height:1.6; }
#MainMenu { visibility:hidden; }
.stDeployButton { display:none; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════
def render_pipeline(result):
    layer_fired = result.get("layer_fired")
    hard_active = layer_fired in ["hard_rule", "city_rule"]
    llm_active  = layer_fired == "llm"
    s1 = "active" if hard_active else ("dimmed" if llm_active else "")
    s2 = "active" if llm_active else ("dimmed" if hard_active else "")
    s3 = "active" if llm_active else ("dimmed" if hard_active else "")
    st.markdown(f"""
    <div class="pipe-stage {s1}"><span class="pipe-num">1</span><span class="pipe-title">Hard rules</span>
    <div class="pipe-desc">Keyword & single-city lookup. Instant assign, bypasses scoring.</div></div>
    <div class="pipe-stage {s2}"><span class="pipe-num">2</span><span class="pipe-title">LLM signal extraction</span>
    <div class="pipe-desc">Llama 3.1 reads text, returns raw theme scores. No weights here.</div></div>
    <div class="pipe-stage {s3}"><span class="pipe-num">3</span><span class="pipe-title">Weighted scoring & routing</span>
    <div class="pipe-desc">Code applies weights, time boost, group signal, then checks per-theme thresholds.</div></div>
    """, unsafe_allow_html=True)


def render_result(result):
    routing = result.get("routing", {})
    scores  = result.get("scores")
    error   = result.get("error")
    layer   = result.get("layer_fired")

    if error and not routing:
        st.error(f"Pipeline error: {error}")
        return

    decision = routing.get("decision", "")
    assigned = routing.get("assigned_theme")

    if decision == "auto_assign" and layer == "hard_rule":
        st.markdown(f'<div class="verdict v-hard">\u26A1 Hard rule \u2192 {assigned.title()}</div>', unsafe_allow_html=True)
    elif decision == "auto_assign" and layer == "city_rule":
        st.markdown(f'<div class="verdict v-hard">\U0001F3D9\uFE0F City rule \u2192 {assigned.title()}</div>', unsafe_allow_html=True)
    elif decision == "auto_assign":
        st.markdown(f'<div class="verdict v-auto">\u2713 Auto-assigned \u2192 {assigned.title()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="verdict v-review">\u26A0 Flagged for human review</div>', unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:13.5px;color:#51606F;line-height:1.5;margin-bottom:8px'>{routing.get('reason','')}</div>", unsafe_allow_html=True)

    if scores and scores.get("group_boost_applied"):
        st.markdown(f"<div class='tradeoff'>\U0001F465 <strong>Group signal:</strong> {scores['group_boost_applied']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    render_pipeline(result)

    if layer in ["hard_rule", "city_rule"]:
        return

    if scores:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='eyebrow'>Theme scores vs thresholds</div>", unsafe_allow_html=True)
        theme_scores = scores.get("theme_scores", {})
        td = routing.get("threshold_detail", {})
        for theme in THEMES:
            score     = theme_scores.get(theme, 0)
            threshold = THRESHOLDS[theme]
            crossed   = td.get(theme, {}).get("crossed", False)
            color     = THEME_COLORS[theme]
            pct       = min(score, 100)
            check     = "\u2713" if crossed else ""
            opacity   = "1" if crossed else "0.55"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:9px">
                <div style="width:78px;font-size:13px;font-weight:600;color:#1A2332">{theme.title()}</div>
                <div style="flex:1;position:relative;height:22px;background:#EDEBE4;border-radius:6px;overflow:hidden">
                    <div style="position:absolute;left:{threshold}%;top:0;height:22px;width:2px;background:#1A2332;opacity:0.5;z-index:2"></div>
                    <div style="width:{pct}%;height:22px;background:{color};border-radius:6px;opacity:{opacity}"></div>
                </div>
                <div style="width:120px;font-size:12px;color:#51606F;text-align:right">
                    <strong style="color:#1A2332">{score:.0f}</strong> / {threshold} {check}
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;color:#8B98A8;margin-top:2px'>The vertical line marks each theme's assignment threshold.</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='eyebrow'>Overall score</div><div style='font-size:26px;font-weight:800;color:#1A2332'>{scores.get('overall_score',0):.1f}</div>", unsafe_allow_html=True)
        with c2:
            tt = scores.get("top_theme","-")
            st.markdown(f"<div class='eyebrow'>Top theme</div><div style='font-size:20px;font-weight:700;color:{THEME_COLORS.get(tt,'#1A2332')}'>{tt.title()}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='eyebrow'>Gap to 2nd</div><div style='font-size:26px;font-weight:800;color:#1A2332'>{scores.get('gap',0):.0f}<span style='font-size:14px;color:#8B98A8'> pts</span></div>", unsafe_allow_html=True)

        gap = scores.get("gap", 0)
        if gap < 15:
            st.markdown("<div class='tradeoff' style='margin-top:14px'><strong>Low gap:</strong> the top two themes are close \u2014 the system treats this as genuine ambiguity, not a confident win.</div>", unsafe_allow_html=True)

        llm = result.get("llm_output")
        if llm:
            with st.expander("See the LLM's raw signals (before any weighting)"):
                desc_s = llm.get("description_scores", {})
                st.markdown("**Description scores** \u2014 what the LLM read from the package text:")
                cols = st.columns(4)
                for i, t in enumerate(THEMES):
                    cols[i].markdown(f"<div style='text-align:center'><div class='theme-chip' style='background:{THEME_COLORS[t]}'>{t.title()}</div><div style='font-size:22px;font-weight:800;margin-top:6px;color:#1A2332'>{desc_s.get(t,0)}</div></div>", unsafe_allow_html=True)
                if llm.get("bolded_terms"):
                    st.markdown(f"<div style='margin-top:14px;font-size:13px'><strong>Bolded terms detected:</strong> {', '.join(llm['bolded_terms'])}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:10px;font-size:13px;color:#51606F'><strong>LLM reasoning:</strong> <em>{llm.get('reasoning','')}</em></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
    <span style="font-size:26px">\U0001F9ED</span>
    <span style="font-size:20px;font-weight:800;color:#1A2332">Holiday Package AI Tagger</span>
</div>
""", unsafe_allow_html=True)

tab_overview, tab_classify, tab_how, tab_monitor = st.tabs([
    "Overview", "Try the classifier", "How it works", "Monitoring"
])

# ════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════
with tab_overview:
    st.markdown('<div class="eyebrow">LLM classification system · case study</div>', unsafe_allow_html=True)
    st.markdown('<div class="big-hook">Manual tagging didn\'t scale.<br>So I replaced it with an LLM that explains itself.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-hook">Holiday packages were tagged by hand \u2014 slow, inconsistent, and incomplete as the catalogue grew. This system reads each package and assigns a theme automatically, but only when it\'s confident. When it isn\'t, it says so and routes to a human.</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="stat-band">
        <div class="stat-cell"><div class="stat-num stat-accent">100%</div><div class="stat-lbl">Catalogue coverage<br>(was incomplete)</div></div>
        <div class="stat-cell"><div class="stat-num">0</div><div class="stat-lbl">Manual tagging hours<br>(fully eliminated)</div></div>
        <div class="stat-cell"><div class="stat-num">\u201310%</div><div class="stat-lbl">Browse-stage<br>funnel drop-off</div></div>
        <div class="stat-cell"><div class="stat-num">4</div><div class="stat-lbl">Themes, each with its<br>own confidence bar</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">The architecture</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-intro">Every package flows through three layers. It exits at the first one that produces a confident answer \u2014 so the cheap, unambiguous cases never hit the LLM at all.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #1E5BB8">
        <div class="layer-label">Layer 1</div><div class="layer-h">Hard rules</div>
        <div class="layer-p">A curated keyword list (<em>yatra</em>, <em>honeymoon</em>) and a single-city map assign a theme instantly at high confidence. No LLM call. Governed only by PM + Engineering.</div></div>""", unsafe_allow_html=True)
    with a2:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #7C3AED">
        <div class="layer-label">Layer 2</div><div class="layer-h">LLM signal extraction</div>
        <div class="layer-p">Llama 3.1 reads the description and activities and returns a raw score per theme. It only reads and scores \u2014 it never decides the final theme or the routing.</div></div>""", unsafe_allow_html=True)
    with a3:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #0D9488">
        <div class="layer-label">Layer 3</div><div class="layer-h">Scoring & routing</div>
        <div class="layer-p">Code applies the weights, time boost and group signal, then checks each theme's own threshold. One theme crosses \u2192 assign. Zero or two+ \u2192 human review.</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Decisions worth defending</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-intro">The interesting part of this project isn\'t that it calls an LLM \u2014 it\'s the choices around the LLM. A few I\'d talk through in an interview:</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("""<div class="decision-card">
        <div class="dc-title">Weights live in code, not the prompt</div>
        <div class="dc-decision">Model-agnostic by design</div>
        <div class="dc-body">If the weights are baked into the prompt, swapping the LLM breaks the scoring. By keeping all math in Python, I can change Llama for GPT-4 and only re-validate the prompt format \u2014 the scoring logic is unit-testable without any model.</div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown("""<div class="decision-card" style="border-top-color:#0D9488">
        <div class="dc-title">Each theme has its own threshold</div>
        <div class="dc-decision">Calibrated to signal density</div>
        <div class="dc-body">Spiritual signals (temple, yatra) are unambiguous, so a lower bar is safe. Romantic signals (beach, dinner, spa) show up in lots of non-romantic packages, so the bar is higher to avoid over-tagging.</div></div>""", unsafe_allow_html=True)
    with d2:
        st.markdown("""<div class="decision-card" style="border-top-color:#7C3AED">
        <div class="dc-title">The LLM never decides routing</div>
        <div class="dc-decision">Separation of concerns</div>
        <div class="dc-body">Routing is a deterministic function of scores vs thresholds. Letting the LLM make that call would inject non-determinism into a binary decision that should be a rule. The model scores; the code decides.</div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown("""<div class="decision-card" style="border-top-color:#D97706">
        <div class="dc-title">Human review is a feature, not a failure</div>
        <div class="dc-decision">Confidence-aware by default</div>
        <div class="dc-body">When two themes both clear their thresholds, or none do, the system flags it instead of guessing. A wrong confident tag hurts the customer more than an honest "needs review."</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.info("Head to **Try the classifier** to run a package through all three layers \u2014 or **How it works** for the full scoring breakdown.")

# ════════════════════════════════════════════════
# TAB 2 — CLASSIFIER
# ════════════════════════════════════════════════
with tab_classify:
    st.markdown('<div class="eyebrow">Live demo</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:22px;font-weight:800;color:#1A2332;margin-bottom:4px'>Run a package through the pipeline</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>Pick a pre-loaded example \u2014 each is built to trigger a different path \u2014 or write your own. Watch which layer fires and why.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        mode = st.radio("Input mode", ["Pre-loaded example", "Write your own"], horizontal=True, label_visibility="collapsed")

        if mode == "Pre-loaded example":
            labels = {v["label"]: k for k, v in SAMPLE_PACKAGES.items()}
            sel_label = st.selectbox("Choose a package", list(labels.keys()))
            sel_key = labels[sel_label]
            package = SAMPLE_PACKAGES[sel_key].copy()

            scen = package.get("scenario", "")
            scen_color = {
                "Hard rule trigger": "#1E5BB8",
                "Single theme auto-assign": "#0E7A43",
                "Multi-theme conflict \u2192 human review": "#9A5B00",
                "No theme crosses threshold \u2192 human review": "#B23A48",
            }.get(scen, "#51606F")
            st.markdown(f"<div style='background:#FFF;border:1px solid #E8E6DE;border-left:3px solid {scen_color};border-radius:8px;padding:10px 14px;margin:10px 0;font-size:13px;color:#3A4756'><strong style='color:{scen_color}'>Designed to show:</strong> {scen}</div>", unsafe_allow_html=True)

            with st.expander("Package details", expanded=True):
                st.markdown(f"**{package['name']}**")
                st.caption(f"\U0001F4CD {package['destination']}  ·  \U0001F4B0 {package['price_tier']}  ·  \U0001F3E8 {package['hotel_type']}")
                grp = {"couple":"\U0001F46B Couple","family":"\U0001F468\u200D\U0001F469\u200D\U0001F467 Family with children","solo":"\U0001F9CD Solo","friends":"\U0001F465 Friends","unspecified":"Not specified"}.get(package.get("group_type","unspecified"))
                st.caption(f"Group: {grp}")
                st.markdown(f"<div style='font-size:13px;color:#3A4756;line-height:1.5;margin-top:6px'>{package['description']}</div>", unsafe_allow_html=True)
                if package.get("activities"):
                    st.markdown("<div style='font-size:12px;font-weight:700;color:#51606F;margin-top:10px'>ACTIVITIES</div>", unsafe_allow_html=True)
                    for a in package["activities"]:
                        st.caption(f"\u2022 {a['name']} ({a['duration_hours']}h)")
        else:
            pkg_name = st.text_input("Package name", placeholder="Bali Honeymoon Retreat")
            destination = st.text_input("Destination(s)", placeholder="Bali   or   Manali, Leh")
            colp1, colp2 = st.columns(2)
            price_tier = colp1.selectbox("Price tier", ["Budget","Standard","Premium","Luxury"])
            group_type = colp2.selectbox("Group", ["unspecified","couple","family","solo","friends"],
                format_func=lambda x: {"couple":"Couple","family":"Family w/ kids","solo":"Solo","friends":"Friends","unspecified":"Not specified"}[x])
            hotel_type = st.text_input("Hotel type", placeholder="Overwater villa")
            description = st.text_area("Description", placeholder="Use **double asterisks** to emphasise key terms...", height=110)
            st.caption("Add up to 3 activities")
            activities = []
            for i in range(3):
                with st.expander(f"Activity {i+1}", expanded=(i==0)):
                    an = st.text_input("Name", key=f"an{i}")
                    ad = st.text_input("Description", key=f"ad{i}")
                    ah = st.number_input("Hours", key=f"ah{i}", min_value=0.0, max_value=48.0, value=0.0, step=0.5)
                    if an and ah > 0:
                        activities.append({"name":an,"description":ad,"duration_hours":ah})
            package = {"id":"CUSTOM_001","name":pkg_name or "Custom Package","destination":destination or "Unknown",
                       "price_tier":price_tier,"hotel_type":hotel_type or "Standard","description":description or "",
                       "activities":activities,"group_type":group_type}

        if not os.environ.get("GROQ_API_KEY",""):
            st.warning("GROQ_API_KEY not set \u2014 LLM scoring won't run. Hard-rule examples still work.")

        run = st.button("Run classifier", type="primary", use_container_width=True)

    with col_out:
        if run:
            with st.spinner("Flowing through the pipeline..."):
                result = classify_package(package)
            render_result(result)
        else:
            st.markdown("<div style='border:1.5px dashed #D8D5CC;border-radius:12px;padding:50px 20px;text-align:center;color:#9AA5B1;font-size:14px;margin-top:8px'>Pick a package and hit <strong>Run classifier</strong><br>to watch the pipeline resolve.</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 3 — HOW IT WORKS
# ════════════════════════════════════════════════
with tab_how:
    st.markdown('<div class="eyebrow">The depth layer</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:22px;font-weight:800;color:#1A2332;margin-bottom:4px'>How a score becomes a decision</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>The LLM produces raw signals. Everything that turns those signals into a confident, auditable decision happens in code \u2014 which is what makes it testable and model-agnostic.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">1 · The scoring engine</div>', unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>Three signals are combined per theme. The weights reflect how trustworthy each signal is.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    w1, w2, w3 = st.columns(3)
    with w1:
        st.markdown(f"""<div class="layer-box">
        <div style="font-size:30px;font-weight:800;color:#2563EB">{int(WEIGHTS['description']*100)}%</div>
        <div class="layer-h" style="font-size:15px">Package description</div>
        <div class="layer-p">Marketing copy \u2014 useful, but written to sell. Weighted lower because it's intentional, not objective.</div></div>""", unsafe_allow_html=True)
    with w2:
        st.markdown(f"""<div class="layer-box" style="border-top:3px solid #0D9488">
        <div style="font-size:30px;font-weight:800;color:#0D9488">{int(WEIGHTS['activity']*100)}%</div>
        <div class="layer-h" style="font-size:15px">Activity descriptions</div>
        <div class="layer-p">The most reliable signal \u2014 what the traveller actually does on the trip. Carries the most weight.</div></div>""", unsafe_allow_html=True)
    with w3:
        st.markdown(f"""<div class="layer-box" style="border-top:3px solid #D97706">
        <div style="font-size:30px;font-weight:800;color:#D97706">{int(WEIGHTS['time_boost']*100)}%</div>
        <div class="layer-h" style="font-size:15px">Activity time boost</div>
        <div class="layer-p">An activity that eats most of the itinerary gets amplified \u2014 a 10-hour trek matters more than a 1-hour walk.</div></div>""", unsafe_allow_html=True)

    st.markdown("<div class='tradeoff'><strong>Why 35 / 50 / 15?</strong> These are a starting hypothesis, not a law. In production they're tuned with a grid search against a manually-labelled sample \u2014 the split that maximises routing accuracy wins. They can even differ per theme, since some themes rely more on activity data than description.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    cb1, cb2 = st.columns(2)
    with cb1:
        st.markdown("""<div class="layer-box">
        <div class="layer-label">Editorial signal</div><div class="layer-h" style="font-size:16px">Bolded terms count double</div>
        <div class="layer-p">When an ops writer wraps a phrase in <strong>**asterisks**</strong>, that's an intentional flag of what matters. The scorer gives bolded terms 2\u00D7 the signal weight \u2014 a lightweight way to let humans steer the model.</div></div>""", unsafe_allow_html=True)
    with cb2:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #E11D6B">
        <div class="layer-label">Soft signal</div><div class="layer-h" style="font-size:16px">Who's travelling</div>
        <div class="layer-p">Two adults, no kids nudges <span style="color:#E11D6B;font-weight:700">Romantic</span>. Adults with children nudges <span style="color:#0D9488;font-weight:700">Family</span>. It's a multiplier on an existing signal \u2014 it amplifies, it never overrides.</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">2 · Per-theme thresholds</div>', unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>A score only becomes a tag if it clears that theme's own bar. The bars differ on purpose.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    for theme in THEMES:
        thr = THRESHOLDS[theme]
        color = THEME_COLORS[theme]
        reason = {
            "romantic": "Romantic cues (beach, villa, dinner) appear in many non-romantic packages \u2014 high bar prevents over-tagging.",
            "adventure": "Adventure cues are fairly specific, but aspirational copy inflates them \u2014 a high bar keeps it honest.",
            "spiritual": "Temple, yatra, shrine rarely appear outside spiritual trips \u2014 a lower bar is safe.",
            "family": "Family cues are moderately specific \u2014 a mid-range bar fits.",
        }[theme]
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px">
            <div style="width:90px"><span class="theme-chip" style="background:{color}">{theme.title()}</span></div>
            <div style="width:46px;font-size:20px;font-weight:800;color:#1A2332">{thr}</div>
            <div style="flex:1;font-size:13px;color:#51606F;line-height:1.5">{reason}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='tradeoff'><strong>How are these set?</strong> By trial and error against labelled data, then a product call: for each theme, is a false tag or a missed tag more costly to the customer? Romantic leans strict (false tags hurt), Spiritual leans permissive (misses hurt discoverability).</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">3 · When a human steps in</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #0E7A43"><div class="layer-h" style="font-size:15px">1 theme crosses</div><div class="layer-p">Clear winner \u2192 <strong>auto-assign</strong>.</div></div>""", unsafe_allow_html=True)
    with r2:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #9A5B00"><div class="layer-h" style="font-size:15px">0 themes cross</div><div class="layer-p">Not enough signal \u2192 <strong>human review</strong>.</div></div>""", unsafe_allow_html=True)
    with r3:
        st.markdown("""<div class="layer-box" style="border-top:3px solid #9A5B00"><div class="layer-h" style="font-size:15px">2+ themes cross</div><div class="layer-p">Genuine conflict \u2192 <strong>human review</strong>.</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">4 · Prompt engineering</div>', unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>The prompt is treated like code \u2014 versioned, validated, and defended against the fact that LLMs don't reliably follow format instructions.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("""<div class="layer-box"><div class="layer-h" style="font-size:15px">Anchored scoring</div><div class="layer-p">The 0\u2013100 scale is anchored with concrete examples (90+ = dominant, 30\u201349 = incidental) so scores stay consistent across packages \u2014 otherwise thresholds are meaningless.</div></div>""", unsafe_allow_html=True)
    with p2:
        st.markdown("""<div class="layer-box"><div class="layer-h" style="font-size:15px">Defensive validation</div><div class="layer-p">Every response is schema-checked. Extra fields are stripped, missing fields trigger one retry at temperature 0, and a second failure routes to human review \u2014 never a crash.</div></div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 4 — MONITORING
# ════════════════════════════════════════════════
with tab_monitor:
    st.markdown('<div class="eyebrow">Production health</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:22px;font-weight:800;color:#1A2332;margin-bottom:4px'>Catching drift before customers do</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-intro'>Deployment isn't the finish line. Hosted models update silently, and input data shifts as the catalogue grows. This dashboard treats the validation log as a health signal \u2014 each metric guards against a specific failure mode.</div>", unsafe_allow_html=True)

    logs = load_logs()
    metrics = compute_health_metrics(logs)

    if not logs:
        st.info("No runs logged yet.")
    else:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        total = metrics["total_classifications"]
        aa = metrics["auto_assign_count"]
        hr = metrics["human_review_count"]
        hard = metrics["hard_rule_count"]
        aa_rate = round(aa/total*100,1) if total else 0
        st.markdown(f"""
        <div class="stat-band">
            <div class="stat-cell"><div class="stat-num">{total:,}</div><div class="stat-lbl">Packages classified</div></div>
            <div class="stat-cell"><div class="stat-num stat-accent">{aa_rate}%</div><div class="stat-lbl">Auto-assigned</div></div>
            <div class="stat-cell"><div class="stat-num">{hr:,}</div><div class="stat-lbl">Sent to human review</div></div>
            <div class="stat-cell"><div class="stat-num">{hard:,}</div><div class="stat-lbl">Resolved by hard rules</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Validation health \u2014 each metric protects against something</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        mfr = metrics["missing_field_rate"]
        efr = metrics["extra_field_rate"]
        rr = metrics["retry_resolution_rate"]
        vhr = metrics["validation_hr_rate"]

        def metric_card(col, label, value, protects, ok):
            badge = "#0E7A43" if ok else "#B23A48"
            badge_txt = "Healthy" if ok else "Investigate"
            col.markdown(f"""<div class="layer-box" style="border-top:3px solid {badge}">
            <div class="layer-label">{label}</div>
            <div style="font-size:28px;font-weight:800;color:#1A2332;margin:2px 0">{value}</div>
            <div style="display:inline-block;font-size:11px;font-weight:700;color:{badge};background:{badge}18;padding:2px 8px;border-radius:10px">{badge_txt}</div>
            <div style="font-size:11.5px;color:#8B98A8;margin-top:8px;line-height:1.4">{protects}</div></div>""", unsafe_allow_html=True)

        mc1, mc2, mc3, mc4 = st.columns(4)
        metric_card(mc1, "Missing field rate", f"{mfr}%", "Guards against prompt drift \u2014 the LLM silently dropping required fields.", mfr <= 5)
        metric_card(mc2, "Extra field rate", f"{efr}%", "Leading indicator \u2014 the model going off-schema before missing fields climb.", efr <= 5)
        rr_disp = f"{rr}%" if rr is not None else "N/A"
        metric_card(mc3, "Retry resolution", rr_disp, "Tells you if retrying actually helps \u2014 or just burns tokens on a broken prompt.", rr is None or rr >= 60)
        metric_card(mc4, "Validation \u2192 review", f"{vhr}%", "Packages a human had to take because the LLM output failed twice.", vhr <= 1)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Which fields fail most</div>', unsafe_allow_html=True)
        st.markdown("<div class='section-intro'>Pinpoints the weakest part of the prompt \u2014 fix instructions where the evidence says they're failing, not on a hunch.</div>", unsafe_allow_html=True)
        fc = metrics.get("field_level_frequency", {})
        if fc:
            import pandas as pd
            df = pd.DataFrame(list(fc.items()), columns=["Field","Missing count"]).sort_values("Missing count", ascending=False)
            st.bar_chart(df.set_index("Field"), color="#2563EB")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Alert status</div>', unsafe_allow_html=True)
        alerts = []
        if mfr > 5: alerts.append(f"Missing field rate ({mfr}%) over the 5% threshold \u2014 review the prompt.")
        if rr is not None and rr < 60: alerts.append(f"Retry resolution ({rr}%) under 60% \u2014 retrying is wasting tokens, the prompt needs a structural fix.")
        if vhr > 1: alerts.append(f"Validation-triggered review ({vhr}%) over 1% \u2014 check edge cases.")
        if efr > 5: alerts.append(f"Extra field rate ({efr}%) over 5% \u2014 the model may be going off-schema.")
        if alerts:
            for a in alerts:
                st.markdown(f"<div style='background:#FEF3E2;border-left:3px solid #9A5B00;padding:12px 16px;border-radius:0 8px 8px 0;font-size:13px;color:#7A4A00;margin-bottom:8px'>\u26A0 {a}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#E7F6EE;border-left:3px solid #0E7A43;padding:12px 16px;border-radius:0 8px 8px 0;font-size:13px;color:#0E7A43'>\u2713 All metrics within healthy thresholds.</div>", unsafe_allow_html=True)

        with st.expander("Recent validation events"):
            import pandas as pd
            vlogs = [e for e in logs if e.get("event") in ["missing_fields","extra_fields","parse_failure"]][-15:]
            if vlogs:
                rows = [{"Package":e.get("package_id",""),"Event":e.get("event",""),
                         "Fields":", ".join(e.get("fields_affected",[])),"Action":e.get("action_taken",""),
                         "Resolved":"\u2713" if e.get("resolved") else "\u2717","Time":e.get("timestamp","")[:19]} for e in reversed(vlogs)]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
