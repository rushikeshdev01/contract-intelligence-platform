import streamlit as st
import requests
import threading
import time
from datetime import datetime
import plotly.graph_objects as go
from services.report_generator import build_docx_report
from services.scoring import compute_overall_risk

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/analyze"
ASK_URL = f"{BASE_URL}/ask"

st.set_page_config(page_title="Contract Intelligence Platform", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Design system: dark indigo, glassmorphism cards, radial gradient background.
# ---------------------------------------------------------------------------
PALETTE = {
    "bg": "#0F172A",
    "card": "#1E293B",
    "primary": "#6366F1",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
}
RISK_COLORS = {"low": PALETTE["success"], "medium": PALETTE["warning"], "high": PALETTE["danger"], "unknown": "#64748B"}
STATUS_COLORS = {"green": PALETTE["success"], "yellow": PALETTE["warning"], "red": PALETTE["danger"], "unknown": "#64748B"}
DOC_TYPE_ICONS = {
    "NDA": "🤝",
    "SaaS / Software Agreement": "💻",
    "Employment Agreement": "💼",
    "Vendor / Service Agreement": "🧾",
    "Lease / Rental Agreement": "🏠",
    "Other / General Commercial Agreement": "📄",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

.stApp {{
    background:
        radial-gradient(circle at top right, #312e81 0%, transparent 40%),
        radial-gradient(circle at bottom left, #1e1b4b 0%, transparent 45%),
        {PALETTE["bg"]};
}}
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {PALETTE["text"]};
}}
h1, h2, h3 {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700;
    letter-spacing: -0.01em;
}}
.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {PALETTE["primary"]};
    margin-bottom: 0.2rem;
}}
.app-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: {PALETTE["text"]};
    margin: 0 0 0.15rem 0;
}}
.app-subtitle {{
    color: {PALETTE["muted"]};
    font-size: 0.95rem;
    margin-bottom: 1.6rem;
}}
.glass-card {{
    background: rgba(30,41,59,0.55);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid var(--accent, {PALETTE["primary"]});
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.glass-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.4);
}}
.glass-card .body-text {{
    color: #E2E8F0;
    font-size: 0.93rem;
}}
.data-value {{
    font-family: 'JetBrains Mono', monospace;
    color: {PALETTE["text"]};
}}
.pipeline-step {{
    background: rgba(30,41,59,0.55);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    height: 100%;
    transition: transform 0.15s ease;
}}
.pipeline-step:hover {{ transform: translateY(-2px); }}
.pipeline-step .step-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: {PALETTE["primary"]};
    letter-spacing: 0.1em;
}}
.pipeline-step .step-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: {PALETTE["text"]};
    margin: 0.3rem 0 0.35rem 0;
}}
.pipeline-step .step-desc {{
    font-size: 0.85rem;
    color: {PALETTE["muted"]};
    line-height: 1.4;
}}
.metric-card {{
    background: linear-gradient(160deg, rgba(99,102,241,0.12), rgba(30,41,59,0.4));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid var(--accent, {PALETTE["primary"]});
    border-radius: 12px;
    padding: 1rem 1rem 0.9rem 1.1rem;
    height: 100%;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.4);
}}
.metric-card .metric-icon {{ font-size: 1.3rem; margin-bottom: 0.35rem; display: block; }}
.metric-card .metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.1rem;
    font-weight: 500;
    color: {PALETTE["text"]};
    line-height: 1.1;
}}
.metric-card .metric-label {{
    font-size: 0.78rem;
    color: {PALETTE["muted"]};
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.risk-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    text-transform: uppercase;
}}
.risk-badge.badge-high {{ background: rgba(239,68,68,0.16); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.4); }}
.risk-badge.badge-medium {{ background: rgba(245,158,11,0.16); color: #FCD34D; border: 1px solid rgba(245,158,11,0.4); }}
.risk-badge.badge-low {{ background: rgba(34,197,94,0.16); color: #86EFAC; border: 1px solid rgba(34,197,94,0.4); }}
.upload-container {{
    background: linear-gradient(160deg, rgba(99,102,241,0.10), rgba(30,41,59,0.35));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 14px;
    padding: 1.2rem 1.3rem 0.4rem 1.3rem;
    margin-bottom: 1rem;
}}
.upload-container .upload-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: {PALETTE["text"]};
    margin-bottom: 0.6rem;
}}
.section-divider {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1.6rem 0 1.1rem 0;
}}
.verdict-card {{
    background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(30,41,59,0.5));
    backdrop-filter: blur(14px);
    border: 1px solid rgba(99,102,241,0.35);
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
}}
.verdict-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    color: {PALETTE["text"]};
    margin-bottom: 0.5rem;
}}
.verdict-body {{
    font-size: 1rem;
    color: #E2E8F0;
    line-height: 1.5;
    margin-bottom: 0.9rem;
}}
.verdict-stats {{ display: flex; gap: 1.8rem; }}
.verdict-stat-label {{ font-size: 0.72rem; color: {PALETTE["muted"]}; text-transform: uppercase; letter-spacing: 0.06em; }}
.verdict-stat-value {{ font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: {PALETTE["text"]}; }}
.sidebar-item {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    padding: 0.15rem 0;
}}
.sidebar-timestamp {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: {PALETTE["muted"]};
}}
.toc-item {{
    font-size: 0.85rem;
    color: #CBD5E1;
    padding: 0.3rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.chat-bubble-user {{
    background: rgba(99,102,241,0.18);
    border: 1px solid rgba(99,102,241,0.35);
    border-radius: 12px 12px 2px 12px;
    padding: 0.6rem 0.9rem;
    margin: 0.4rem 0;
    color: {PALETTE["text"]};
    font-size: 0.9rem;
}}
.chat-bubble-ai {{
    background: rgba(30,41,59,0.6);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px 12px 12px 2px;
    padding: 0.6rem 0.9rem;
    margin: 0.4rem 0;
    color: #E2E8F0;
    font-size: 0.9rem;
}}
</style>
""", unsafe_allow_html=True)


def style_fig(fig, height=280):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#E2E8F0", size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)")
    return fig


def risk_badge_html(level: str) -> str:
    level_key = (level or "").lower()
    icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level_key, "⚪")
    return f'<span class="risk-badge badge-{level_key}">{icon} {level_key.capitalize() or "Unknown"}</span>'


def glass_card(tag_color_key: str, body_html: str, color_map=RISK_COLORS):
    accent = color_map.get(tag_color_key.lower(), color_map["unknown"])
    st.markdown(
        f'<div class="glass-card" style="--accent:{accent}"><span class="body-text">{body_html}</span></div>',
        unsafe_allow_html=True,
    )


def metric_card(value: str, label: str, accent: str = None, icon: str = ""):
    accent = accent or PALETTE["primary"]
    icon_html = f'<span class="metric-icon">{icon}</span>' if icon else ""
    st.markdown(
        f'<div class="metric-card" style="--accent:{accent}">{icon_html}'
        f'<div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def format_timestamp(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %H:%M")
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# Session flags
# ---------------------------------------------------------------------------
if "entered_app" not in st.session_state:
    st.session_state.entered_app = False
if "jump_to_clause" not in st.session_state:
    st.session_state.jump_to_clause = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------------------------
# Sidebar: recent analysis history — icons per document type + timestamps
# ---------------------------------------------------------------------------
if st.session_state.entered_app:
    with st.sidebar:
        st.markdown('<div class="eyebrow">📄 Recent Contracts</div>', unsafe_allow_html=True)
        try:
            history_resp = requests.get(f"{BASE_URL}/history", timeout=5)
            history_resp.raise_for_status()
            recent = history_resp.json().get("analyses", [])
        except requests.exceptions.RequestException:
            recent = []
            st.caption("Backend not reachable — history unavailable.")

        if recent:
            for item in recent:
                icon = DOC_TYPE_ICONS.get(item.get("document_type", ""), "📄")
                ts = format_timestamp(item.get("uploaded_at", ""))
                st.markdown(
                    f'<div class="sidebar-item">{icon} <strong style="color:{PALETTE["text"]}">{item["filename"][:22]}</strong></div>'
                    f'<div class="sidebar-timestamp">{ts} · Grade {item["grade"]}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open", key=f"history_{item['id']}", use_container_width=True):
                    try:
                        detail_resp = requests.get(f"{BASE_URL}/history/{item['id']}", timeout=10)
                        detail_resp.raise_for_status()
                        st.session_state.viewed_history = detail_resp.json()
                        st.session_state.entered_app = True
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Could not load: {e}")
                st.markdown('<div style="margin-bottom:0.6rem"></div>', unsafe_allow_html=True)
        elif recent == []:
            st.caption("No analyses yet — run one to see it here.")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="eyebrow">🤖 Multi-Agent Contract Review</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">Contract Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Upload a contract — five specialized agents classify, segment, '
    'flag risk from your side of the deal, benchmark it against market norms, and summarize it.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Welcome screen — shown once per session, before the uploader
# ---------------------------------------------------------------------------
if not st.session_state.entered_app:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#E2E8F0;font-size:0.98rem;max-width:680px;margin-bottom:1.4rem">'
        'Reading contracts manually is slow, and the risk that matters most is often '
        'what\'s <em>missing</em>, not just what\'s written. This tool runs your contract '
        'through five specialized agents so nothing gets a generic, one-size-fits-all review.'
        '</div>',
        unsafe_allow_html=True,
    )

    steps = [
        ("01", "🏷️ Classify", "Detects the contract type (NDA, SaaS, Lease, Employment, Vendor) to apply the right checklist."),
        ("02", "✂️ Segment", "Splits the raw text into individual clauses for focused analysis."),
        ("03", "⚠️ Risk Analysis", "Flags risky clauses from your specific side of the deal, and checks for silently missing protections."),
        ("04", "📊 Benchmark", "Compares key terms (notice periods, liability caps) against industry-standard ranges."),
        ("05", "📝 Summarize", "Produces a plain-English executive summary of the whole contract."),
    ]
    cols = st.columns(5)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f'<div class="pipeline-step"><div class="step-num">{num}</div>'
                f'<div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="margin-top:1.4rem"></div>', unsafe_allow_html=True)
    st.caption("This tool provides AI-assisted first-pass review — it is not a substitute for a qualified attorney.")

    if st.button("Get Started →", type="primary"):
        st.session_state.entered_app = True
        st.rerun()

    st.stop()


def estimate_reading_time(clauses: list) -> int:
    word_count = sum(len(c.split()) for c in clauses)
    return max(1, round(word_count / 200))


def estimate_confidence(result: dict) -> int:
    """
    Heuristic, not a calibrated model probability: reflects how much grounding
    data the pipeline actually found (legal citations, benchmarks matched,
    clauses segmented) rather than the LLM's own certainty, which isn't a
    real number these models expose.
    """
    score = 70
    flags = result.get("risk_flags", [])
    if flags:
        cited = len([f for f in flags if f.get("legal_reference")])
        score += min(15, round((cited / len(flags)) * 15))
    if result.get("benchmarks"):
        score += 6
    if len(result.get("clauses", [])) >= 5:
        score += 5
    return min(96, score)


def render_results(result: dict, position: str, filename: str, show_download: bool = True):
    present_flags = [f for f in result["risk_flags"] if f.get("type", "present") == "present"]
    missing_flags = [f for f in result["risk_flags"] if f.get("type") == "missing"]
    benchmarks = result.get("benchmarks", [])
    overall_score, grade = compute_overall_risk(result["risk_flags"])

    if show_download:
        docx_buffer = build_docx_report(result, position, filename=filename)
        st.download_button(
            label="⬇️  Download Report (.docx)",
            data=docx_buffer,
            file_name=f"contract_analysis_{filename.rsplit('.', 1)[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    if result.get("document_type"):
        icon = DOC_TYPE_ICONS.get(result["document_type"], "📄")
        st.markdown(
            f'<div class="eyebrow" style="margin-top:1.2rem">Detected Type</div>'
            f'<div style="font-size:1.05rem;color:{PALETTE["text"]};margin-bottom:0.8rem">{icon} {result["document_type"]}</div>',
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------
    # AI Verdict — the headline card, replacing a plain "Executive Summary"
    # -----------------------------------------------------------------
    verdict_map = {
        "A": ("🟢 Low Risk", PALETTE["success"]),
        "B": ("🟢 Low Risk", PALETTE["success"]),
        "C": ("🟡 Moderate Risk", PALETTE["warning"]),
        "D": ("🔴 High Risk", PALETTE["danger"]),
        "F": ("🔴 High Risk", PALETTE["danger"]),
    }
    verdict_label, verdict_color = verdict_map.get(grade, ("⚪ Unrated", "#64748B"))
    high_present_count = len([f for f in present_flags if f.get("risk_level", "").lower() == "high"])

    if high_present_count == 0 and not missing_flags:
        verdict_line = "This contract looks solid overall, with no high-risk clauses or missing protections flagged."
    elif high_present_count == 0:
        verdict_line = f"This contract is largely acceptable, but {len(missing_flags)} protection{'s' if len(missing_flags) != 1 else ''} you'd normally expect are missing — worth raising before signing."
    else:
        verdict_line = f"This contract is acceptable overall, but {high_present_count} clause{'s' if high_present_count != 1 else ''} should be negotiated before signing."

    reading_time = estimate_reading_time(result["clauses"])
    confidence = estimate_confidence(result)

    st.markdown(
        f'<div class="verdict-card" style="--accent:{verdict_color}">'
        f'<div class="eyebrow">🤖 AI Verdict</div>'
        f'<div class="verdict-title">{verdict_label}</div>'
        f'<div class="verdict-body">{verdict_line}</div>'
        f'<div class="verdict-stats">'
        f'<div><div class="verdict-stat-label">Estimated Reading Time</div><div class="verdict-stat-value">{reading_time} min</div></div>'
        f'<div><div class="verdict-stat-label">Analysis Confidence</div><div class="verdict-stat-value">{confidence}%</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Confidence reflects how much of the contract could be grounded in benchmarks and legal citations — not a certified accuracy score.")

    # -----------------------------------------------------------------
    # Dashboard summary row
    # -----------------------------------------------------------------
    grade_accent = {"A": PALETTE["success"], "B": PALETTE["success"], "C": PALETTE["warning"], "D": PALETTE["danger"], "F": PALETTE["danger"]}.get(grade, "#64748B")
    red_benchmarks = len([b for b in benchmarks if b["status"] == "red"])
    benchmark_accent = PALETTE["danger"] if red_benchmarks else PALETTE["success"]

    high_missing = [f for f in missing_flags if f.get("risk_level", "").lower() == "high"]
    if grade in ("D", "F"):
        alert_bits = []
        if high_present_count:
            alert_bits.append(f"{high_present_count} high-risk clause{'s' if high_present_count != 1 else ''}")
        if high_missing:
            alert_bits.append(f"{len(high_missing)} critical missing protection{'s' if len(high_missing) != 1 else ''}")
        detail = " and ".join(alert_bits) if alert_bits else "significant concerns"
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.4);'
            f'border-radius:10px;padding:0.8rem 1.1rem;margin-bottom:1rem;color:{PALETTE["text"]}">'
            f'⚠️ <strong>High overall risk (Grade {grade})</strong> — this contract has {detail}. '
            f'Review the flags below closely before signing.'
            f'</div>',
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        metric_card(f"{overall_score}", f"Overall Risk · Grade {grade}", grade_accent, icon="📊")
    with m2:
        metric_card(str(len(result["clauses"])), "Clauses Analyzed", "#64748B", icon="📄")
    with m3:
        metric_card(str(len(present_flags)), "Risk Flags", PALETTE["danger"] if present_flags else PALETTE["success"], icon="⚠️")
    with m4:
        metric_card(str(len(missing_flags)), "Missing Protections", PALETTE["danger"] if missing_flags else PALETTE["success"], icon="🛡️")
    with m5:
        metric_card(str(len(benchmarks)), "Benchmarks Checked", benchmark_accent, icon="📈")

    # -----------------------------------------------------------------
    # Charts
    # -----------------------------------------------------------------
    st.markdown('<div style="margin-top:1.1rem"></div>', unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown('<div class="eyebrow">Risk Distribution</div>', unsafe_allow_html=True)
        if present_flags:
            level_counts = {"Low": 0, "Medium": 0, "High": 0}
            for f in present_flags:
                lvl = f.get("risk_level", "").capitalize()
                if lvl in level_counts:
                    level_counts[lvl] += 1
            fig = go.Figure(data=[go.Pie(
                labels=list(level_counts.keys()),
                values=list(level_counts.values()),
                hole=0.55,
                marker=dict(colors=[PALETTE["success"], PALETTE["warning"], PALETTE["danger"]]),
                textfont=dict(color="#0F172A", size=13),
            )])
            st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No present-clause risk flags to chart.")

    with chart_col2:
        st.markdown('<div class="eyebrow">Benchmark Comparison</div>', unsafe_allow_html=True)
        if benchmarks:
            status_color = {"green": PALETTE["success"], "yellow": PALETTE["warning"], "red": PALETTE["danger"]}
            fig = go.Figure(data=[go.Bar(
                y=[b["provision"] for b in benchmarks],
                x=[b["contract_value_days"] for b in benchmarks],
                orientation="h",
                marker=dict(color=[status_color.get(b["status"], "#64748B") for b in benchmarks]),
                text=[f'{b["contract_value_days"]:.0f}d vs {b["standard_range"]}' for b in benchmarks],
                textposition="auto",
            )])
            fig.update_xaxes(title="Days")
            st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("No benchmarkable provisions detected in this contract.")

    if missing_flags:
        st.markdown('<div style="margin-top:0.6rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Missing Protections by Severity</div>', unsafe_allow_html=True)
        missing_level_counts = {"Low": 0, "Medium": 0, "High": 0}
        for f in missing_flags:
            lvl = f.get("risk_level", "").capitalize()
            if lvl in missing_level_counts:
                missing_level_counts[lvl] += 1
        fig = go.Figure(data=[go.Bar(
            x=list(missing_level_counts.keys()),
            y=list(missing_level_counts.values()),
            marker=dict(color=[PALETTE["success"], PALETTE["warning"], PALETTE["danger"]]),
        )])
        st.plotly_chart(style_fig(fig, height=220), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    with st.expander("🔍 How this analysis was produced (agent-by-agent)"):
        present_count = len(present_flags)
        missing_count = len(missing_flags)
        benchmark_count = len(benchmarks)
        clause_count = len(result["clauses"])
        st.markdown(f"""
1. **Document Classifier** → read the contract and identified it as **{result.get('document_type', 'Unknown')}**, which determined which checklist of critical provisions to apply later.
2. **Clause Segmenter** → split the raw contract text into **{clause_count} distinct clauses** for individual analysis.
3. **Risk Analyzer** → assessed each clause from the **"{position}"** perspective, producing **{present_count} present-clause risk flags**, and separately checked the type-specific checklist to find **{missing_count} missing-provision concerns**.
4. **Benchmark Analyzer** → extracted **{benchmark_count} numeric provisions** (e.g. notice periods, liability caps) and compared them against industry-standard ranges.
5. **Summarizer** → combined all of the above into the plain-English executive summary shown below.
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("📝 Executive Summary")
    st.write(result["summary"])

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("📈 Market Standard Benchmarks")
    if benchmarks:
        for row in benchmarks:
            body = (
                f'<span class="data-value">{row["provision"]}</span> — '
                f'contract: <span class="data-value">{row["contract_value_days"]:.0f} days</span> · '
                f'standard: <span class="data-value">{row["standard_range"]}</span>'
            )
            glass_card(row["status"], body, color_map=STATUS_COLORS)
    else:
        st.caption("No benchmarkable provisions (e.g. liability cap, notice periods) were detected in this contract.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("⚠️ Risk Flags — clauses present in the contract")

    fcol1, fcol2 = st.columns([2, 1])
    with fcol1:
        risk_search = st.text_input("🔍 Search risk flags", placeholder="Search by keyword in reason or clause...", key="risk_search")
    with fcol2:
        risk_level_filter = st.selectbox("Filter by level", ["All", "High", "Medium", "Low"], key="risk_level_filter")

    filtered_present = present_flags
    if risk_level_filter != "All":
        filtered_present = [f for f in filtered_present if f.get("risk_level", "").lower() == risk_level_filter.lower()]
    if risk_search:
        q = risk_search.lower()
        filtered_present = [f for f in filtered_present if q in f.get("reason", "").lower() or q in f.get("clause", "").lower()]

    if filtered_present:
        for flag in sorted(filtered_present, key=lambda f: f.get("risk_score", 50), reverse=True):
            score = flag.get("risk_score", "?")
            badge = risk_badge_html(flag["risk_level"])
            body = f'{badge} <span class="data-value" style="margin-left:0.4rem">{score}</span><br>{flag["reason"]}'
            if flag.get("legal_reference"):
                body += f'<br><span style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:{PALETTE["muted"]}">§ {flag["legal_reference"]}</span>'
            glass_card(flag["risk_level"], body)
            with st.expander("View clause"):
                st.write(flag["clause"])
    elif present_flags:
        st.caption("No risk flags match your search/filter.")
    else:
        st.caption("No risky clauses flagged.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("🛡️ Missing Protections — not found anywhere in the contract")
    if missing_flags:
        st.caption("A protection that's silently absent can be riskier than one that's stated explicitly.")
        for flag in sorted(missing_flags, key=lambda f: f.get("risk_score", 50), reverse=True):
            score = flag.get("risk_score", "?")
            badge = risk_badge_html(flag["risk_level"])
            body = f'{badge} <span class="data-value" style="margin-left:0.4rem">{score}</span><br><strong>{flag["clause"]}</strong> — {flag["reason"]}'
            if flag.get("legal_reference"):
                body += f'<br><span style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:{PALETTE["muted"]}">§ {flag["legal_reference"]}</span>'
            glass_card(flag["risk_level"], body)
    else:
        st.caption("No missing-provision concerns detected.")

    # -----------------------------------------------------------------
    # Clause Navigator — table of contents; clicking brings that clause
    # to the top of the list below, expanded (Streamlit can't do true
    # smooth-scroll to an anchor, so this is the practical equivalent:
    # instant, no manual scrolling needed).
    # -----------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("📑 Table of Contents")
    nav_cols = st.columns(3)
    for i, clause in enumerate(result["clauses"]):
        label = clause.strip().split("\n")[0][:38]
        if len(clause) > 38:
            label += "…"
        with nav_cols[i % 3]:
            if st.button(f"{i+1}. {label}", key=f"toc_{i}", use_container_width=True):
                st.session_state.jump_to_clause = i
                st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("📄 All Clauses")
    clause_search = st.text_input("🔍 Search clauses", placeholder="Search clause text...", key="clause_search")

    ordered_indices = list(range(len(result["clauses"])))
    if st.session_state.jump_to_clause is not None and st.session_state.jump_to_clause in ordered_indices:
        jump_idx = st.session_state.jump_to_clause
        ordered_indices.remove(jump_idx)
        ordered_indices.insert(0, jump_idx)

    any_shown = False
    for idx in ordered_indices:
        clause = result["clauses"][idx]
        if clause_search and clause_search.lower() not in clause.lower():
            continue
        any_shown = True
        is_jumped = idx == st.session_state.jump_to_clause
        label = f"📍 Clause {idx+1} (jumped here)" if is_jumped else f"Clause {idx+1}"
        with st.expander(label, expanded=is_jumped):
            st.write(clause)
    if not any_shown:
        st.caption("No clauses match your search.")

    if st.session_state.jump_to_clause is not None:
        if st.button("Clear jump"):
            st.session_state.jump_to_clause = None
            st.rerun()

    # -----------------------------------------------------------------
    # AI Chat — ask questions grounded in this contract's actual clauses
    # -----------------------------------------------------------------
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("🤖 Ask AI")
    st.caption("Ask a question about this contract — answers are grounded in the actual clauses above, not general knowledge.")

    for turn in st.session_state.chat_history:
        st.markdown(f'<div class="chat-bubble-user">🙋 {turn["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble-ai">🤖 {turn["answer"]}</div>', unsafe_allow_html=True)

    chat_col1, chat_col2 = st.columns([4, 1])
    with chat_col1:
        chat_question = st.text_input("Ask a question", placeholder="e.g. Can the landlord increase rent?", key="chat_input", label_visibility="collapsed")
    with chat_col2:
        ask_clicked = st.button("Ask", type="primary", use_container_width=True)

    if ask_clicked and chat_question.strip():
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    ASK_URL,
                    json={
                        "clauses": result["clauses"],
                        "question": chat_question,
                        "document_type": result.get("document_type", ""),
                        "user_position": position,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                answer = resp.json().get("answer", "No answer returned.")
            except requests.exceptions.RequestException as e:
                answer = f"Could not reach the AI: {e}"
        st.session_state.chat_history.append({"question": chat_question, "answer": answer})
        st.rerun()


# ---------------------------------------------------------------------------
# Viewing a past analysis from the sidebar history
# ---------------------------------------------------------------------------
if st.session_state.get("viewed_history"):
    hist = st.session_state.viewed_history
    st.success(f"Viewing saved analysis: {hist['filename']}")
    if st.button("← Back to new analysis"):
        del st.session_state.viewed_history
        st.session_state.jump_to_clause = None
        st.session_state.chat_history = []
        st.rerun()
    render_results(hist, hist.get("user_position", ""), hist["filename"], show_download=True)
    st.stop()

# ---------------------------------------------------------------------------
# Upload + position
# ---------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="upload-title">📄 Upload Contract</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drag & drop or browse files",
        type=["pdf", "docx"],
        label_visibility="collapsed",
    )
    st.caption("PDF • DOCX • Max 200MB")

position = st.selectbox(
    "Which party are you in this contract?",
    ["Not specified", "Customer / Buyer", "Vendor / Seller", "Employer", "Employee",
     "Disclosing Party (NDA)", "Receiving Party (NDA)", "Landlord", "Tenant", "Other"],
    help="Risk assessment adjusts based on whose side you're on — the same clause "
         "can be favorable for one party and risky for the other.",
)

if uploaded_file is not None:
    if st.button("Analyze Contract", type="primary"):
        st.session_state.jump_to_clause = None
        st.session_state.chat_history = []

        AGENT_STEPS = [
            ("🏷️", "Document Classifier", "Identifying contract type..."),
            ("✂️", "Clause Segmenter", "Splitting into individual clauses..."),
            ("⚠️", "Risk Analyzer", "Assessing risk from your position..."),
            ("📊", "Benchmark Analyzer", "Comparing against market standards..."),
            ("📝", "Summarizer", "Writing the executive summary..."),
        ]

        request_result = {}

        def _do_request():
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"position": position}
                resp = requests.post(API_URL, files=files, data=data, timeout=300)
                resp.raise_for_status()
                request_result["data"] = resp.json()
            except requests.exceptions.RequestException as e:
                request_result["error"] = str(e)

        thread = threading.Thread(target=_do_request)
        thread.start()

        with st.status("Running agent pipeline...", expanded=True) as status:
            step_placeholder = st.empty()
            step_index = 0
            while thread.is_alive():
                icon, name, desc = AGENT_STEPS[step_index % len(AGENT_STEPS)]
                step_placeholder.markdown(f"{icon} **{name}** — {desc}")
                time.sleep(1.4)
                step_index += 1
            thread.join()

            if "error" in request_result:
                status.update(label="Analysis failed", state="error", expanded=True)
                st.error(f"Failed to reach backend: {request_result['error']}")
                st.stop()

            step_placeholder.markdown("✅ **All agents complete**")
            status.update(label="Analysis complete", state="complete", expanded=False)

        result = request_result["data"]
        st.success("Analysis complete")
        render_results(result, position, uploaded_file.name)