import streamlit as st
import requests
from services.report_generator import build_docx_report
from services.scoring import compute_overall_risk

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/analyze"

st.set_page_config(page_title="Contract Intelligence Platform", page_icon="📑", layout="wide")

# ---------------------------------------------------------------------------
# Design system: "redline margin" — cards carry a colored margin bar, the way
# a lawyer annotates a printed contract by hand. Serif for headings (evokes a
# printed legal document), Inter for body/UI, JetBrains Mono for data values.
# ---------------------------------------------------------------------------
RISK_COLORS = {"low": "#4F9B6E", "medium": "#D9A441", "high": "#C1443D", "unknown": "#5B6470"}
STATUS_COLORS = {"green": "#4F9B6E", "yellow": "#D9A441", "red": "#C1443D", "unknown": "#5B6470"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
h1, h2, h3 {{
    font-family: 'Source Serif 4', serif !important;
    letter-spacing: -0.01em;
}}
.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #D9A441;
    margin-bottom: 0.2rem;
}}
.app-title {{
    font-family: 'Source Serif 4', serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: #E9E6DD;
    margin: 0 0 0.15rem 0;
}}
.app-subtitle {{
    color: #9AA1AB;
    font-size: 0.95rem;
    margin-bottom: 1.6rem;
}}
.redline-card {{
    border-left: 4px solid var(--accent, #5B6470);
    background: rgba(255,255,255,0.035);
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.55rem;
}}
.redline-card .tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    font-weight: 500;
    color: var(--accent, #5B6470);
    text-transform: uppercase;
    margin-right: 0.5rem;
}}
.redline-card .body-text {{
    color: #DCDAD3;
    font-size: 0.93rem;
}}
.data-value {{
    font-family: 'JetBrains Mono', monospace;
    color: #E9E6DD;
}}
.pipeline-step {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 1rem 1.1rem;
    height: 100%;
}}
.pipeline-step .step-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #D9A441;
    letter-spacing: 0.1em;
}}
.pipeline-step .step-title {{
    font-family: 'Source Serif 4', serif;
    font-size: 1.05rem;
    color: #E9E6DD;
    margin: 0.3rem 0 0.35rem 0;
}}
.pipeline-step .step-desc {{
    font-size: 0.85rem;
    color: #9AA1AB;
    line-height: 1.4;
}}
.metric-card {{
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-top: 3px solid var(--accent, #D9A441);
    border-radius: 8px;
    padding: 0.9rem 1rem;
    text-align: center;
    height: 100%;
}}
.metric-card .metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.9rem;
    font-weight: 500;
    color: #E9E6DD;
    line-height: 1.1;
}}
.metric-card .metric-label {{
    font-size: 0.78rem;
    color: #9AA1AB;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
</style>
""", unsafe_allow_html=True)


def redline_card(tag: str, tag_color_key: str, body_html: str, color_map=RISK_COLORS):
    accent = color_map.get(tag_color_key.lower(), color_map["unknown"])
    st.markdown(
        f'<div class="redline-card" style="--accent:{accent}">'
        f'<span class="tag">{tag}</span>'
        f'<span class="body-text">{body_html}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def metric_card(value: str, label: str, accent: str = "#D9A441"):
    st.markdown(
        f'<div class="metric-card" style="--accent:{accent}">'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )



# ---------------------------------------------------------------------------
# Sidebar: recent analysis history (from SQLite via the backend)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow">Recent Analyses</div>', unsafe_allow_html=True)
    try:
        history_resp = requests.get(f"{BASE_URL}/history", timeout=5)
        history_resp.raise_for_status()
        recent = history_resp.json().get("analyses", [])
    except requests.exceptions.RequestException:
        recent = []
        st.caption("Backend not reachable — history unavailable.")

    if recent:
        for item in recent:
            grade_color = {"A": "#4F9B6E", "B": "#4F9B6E", "C": "#D9A441", "D": "#C1443D", "F": "#C1443D"}.get(item["grade"], "#5B6470")
            label = f'{item["filename"]}  ·  Grade {item["grade"]}'
            if st.button(label, key=f"history_{item['id']}", use_container_width=True):
                try:
                    detail_resp = requests.get(f"{BASE_URL}/history/{item['id']}", timeout=10)
                    detail_resp.raise_for_status()
                    st.session_state.viewed_history = detail_resp.json()
                    st.session_state.entered_app = True
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Could not load: {e}")
    elif recent == []:
        st.caption("No analyses yet — run one to see it here.")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="eyebrow">Multi-Agent Contract Review</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">Contract Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Upload a contract — five specialized agents classify, segment, '
    'flag risk from your side of the deal, benchmark it against market norms, and summarize it.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Welcome screen — shown once per session, before the uploader
# ---------------------------------------------------------------------------
if "entered_app" not in st.session_state:
    st.session_state.entered_app = False

if not st.session_state.entered_app:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#DCDAD3;font-size:0.98rem;max-width:680px;margin-bottom:1.4rem">'
        'Reading contracts manually is slow, and the risk that matters most is often '
        'what\'s <em>missing</em>, not just what\'s written. This tool runs your contract '
        'through five specialized agents so nothing gets a generic, one-size-fits-all review.'
        '</div>',
        unsafe_allow_html=True,
    )

    steps = [
        ("01", "Classify", "Detects the contract type (NDA, SaaS, Lease, Employment, Vendor) to apply the right checklist."),
        ("02", "Segment", "Splits the raw text into individual clauses for focused analysis."),
        ("03", "Risk Analysis", "Flags risky clauses from your specific side of the deal, and checks for silently missing protections."),
        ("04", "Benchmark", "Compares key terms (notice periods, liability caps) against industry-standard ranges."),
        ("05", "Summarize", "Produces a plain-English executive summary of the whole contract."),
    ]
    cols = st.columns(5)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f'<div class="pipeline-step">'
                f'<div class="step-num">{num}</div>'
                f'<div class="step-title">{title}</div>'
                f'<div class="step-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="margin-top:1.4rem"></div>', unsafe_allow_html=True)
    st.caption("This tool provides AI-assisted first-pass review — it is not a substitute for a qualified attorney.")

    if st.button("Get Started →", type="primary"):
        st.session_state.entered_app = True
        st.rerun()

    st.stop()

# ---------------------------------------------------------------------------
# Upload + position
# ---------------------------------------------------------------------------
def render_results(result: dict, position: str, filename: str, show_download: bool = True):
    if show_download:
        docx_buffer = build_docx_report(result, position, filename=filename)
        st.download_button(
            label="⬇️  Download Report (.docx)",
            data=docx_buffer,
            file_name=f"contract_analysis_{filename.rsplit('.', 1)[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    if result.get("document_type"):
        st.markdown(
            f'<div class="eyebrow" style="margin-top:1.2rem">Detected Type</div>'
            f'<div style="font-size:1.05rem;color:#E9E6DD;margin-bottom:0.8rem">{result["document_type"]}</div>',
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------
    # Dashboard summary row — at-a-glance metrics before the detail
    # -----------------------------------------------------------------
    present_flags = [f for f in result["risk_flags"] if f.get("type", "present") == "present"]
    missing_flags = [f for f in result["risk_flags"] if f.get("type") == "missing"]
    benchmarks = result.get("benchmarks", [])

    overall_score, grade = compute_overall_risk(result["risk_flags"])
    grade_accent = {"A": "#4F9B6E", "B": "#4F9B6E", "C": "#D9A441", "D": "#C1443D", "F": "#C1443D"}.get(grade, "#5B6470")
    red_benchmarks = len([b for b in benchmarks if b["status"] == "red"])
    benchmark_accent = "#C1443D" if red_benchmarks else "#4F9B6E"

    high_present = [f for f in present_flags if f.get("risk_level", "").lower() == "high"]
    high_missing = [f for f in missing_flags if f.get("risk_level", "").lower() == "high"]
    if grade in ("D", "F"):
        alert_bits = []
        if high_present:
            alert_bits.append(f"{len(high_present)} high-risk clause{'s' if len(high_present) != 1 else ''}")
        if high_missing:
            alert_bits.append(f"{len(high_missing)} critical missing protection{'s' if len(high_missing) != 1 else ''}")
        detail = " and ".join(alert_bits) if alert_bits else "significant concerns"
        st.markdown(
            f'<div style="background:rgba(193,68,61,0.12);border:1px solid rgba(193,68,61,0.4);'
            f'border-radius:8px;padding:0.8rem 1.1rem;margin-bottom:1rem;color:#E9E6DD">'
            f'⚠️ <strong>High overall risk (Grade {grade})</strong> — this contract has {detail}. '
            f'Review the flags below closely before signing.'
            f'</div>',
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        metric_card(f"{overall_score}", f"Overall Risk · Grade {grade}", grade_accent)
    with m2:
        metric_card(str(len(result["clauses"])), "Clauses Analyzed", "#5B6470")
    with m3:
        metric_card(str(len(present_flags)), "Risk Flags", "#C1443D" if present_flags else "#4F9B6E")
    with m4:
        metric_card(str(len(missing_flags)), "Missing Protections", "#C1443D" if missing_flags else "#4F9B6E")
    with m5:
        metric_card(str(len(benchmarks)), "Benchmarks Checked", benchmark_accent)

    # Risk distribution chart
    if present_flags:
        level_counts = {"Low": 0, "Medium": 0, "High": 0}
        for f in present_flags:
            lvl = f.get("risk_level", "").capitalize()
            if lvl in level_counts:
                level_counts[lvl] += 1

        st.markdown('<div style="margin-top:1.1rem"></div>', unsafe_allow_html=True)
        chart_cols = st.columns([1, 1, 1])
        bar_colors = {"Low": "#4F9B6E", "Medium": "#D9A441", "High": "#C1443D"}
        for col, (level, count) in zip(chart_cols, level_counts.items()):
            with col:
                max_count = max(level_counts.values()) or 1
                bar_width = int((count / max_count) * 100) if count else 4
                st.markdown(
                    f'<div style="font-size:0.8rem;color:#9AA1AB;margin-bottom:0.25rem">'
                    f'{level} risk · <span class="data-value">{count}</span></div>'
                    f'<div style="background:rgba(255,255,255,0.06);border-radius:4px;height:10px;overflow:hidden">'
                    f'<div style="background:{bar_colors[level]};width:{bar_width}%;height:100%"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    with st.expander("🔍 How this analysis was produced (agent-by-agent)"):
        present_count = len([f for f in result["risk_flags"] if f.get("type", "present") == "present"])
        missing_count = len([f for f in result["risk_flags"] if f.get("type") == "missing"])
        benchmark_count = len(result.get("benchmarks", []))
        clause_count = len(result["clauses"])

        st.markdown(f"""
1. **Document Classifier** → read the contract and identified it as **{result.get('document_type', 'Unknown')}**, which determined which checklist of critical provisions to apply later.
2. **Clause Segmenter** → split the raw contract text into **{clause_count} distinct clauses** for individual analysis.
3. **Risk Analyzer** → assessed each clause from the **"{position}"** perspective, producing **{present_count} present-clause risk flags**, and separately checked the type-specific checklist to find **{missing_count} missing-provision concerns**.
4. **Benchmark Analyzer** → extracted **{benchmark_count} numeric provisions** (e.g. notice periods, liability caps) and compared them against industry-standard ranges.
5. **Summarizer** → combined all of the above into the plain-English executive summary shown below.
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Executive Summary")
    st.write(result["summary"])

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Market Standard Benchmarks")
    if benchmarks:
        for row in benchmarks:
            body = (
                f'<span class="data-value">{row["provision"]}</span> — '
                f'contract: <span class="data-value">{row["contract_value_days"]:.0f} days</span> · '
                f'standard: <span class="data-value">{row["standard_range"]}</span>'
            )
            redline_card(row["status"], row["status"], body, color_map=STATUS_COLORS)
    else:
        st.caption("No benchmarkable provisions (e.g. liability cap, notice periods) were detected in this contract.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Risk Flags — clauses present in the contract")
    if present_flags:
        for flag in sorted(present_flags, key=lambda f: f.get("risk_score", 50), reverse=True):
            score = flag.get("risk_score", "?")
            tag = f'{flag["risk_level"].upper()} · {score}'
            body = flag["reason"]
            if flag.get("legal_reference"):
                body += f'<br><span style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:#9AA1AB">§ {flag["legal_reference"]}</span>'
            redline_card(tag, flag["risk_level"], body)
            with st.expander("View clause"):
                st.write(flag["clause"])
    else:
        st.caption("No risky clauses flagged.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("Missing Protections — not found anywhere in the contract")
    if missing_flags:
        st.caption("A protection that's silently absent can be riskier than one that's stated explicitly.")
        for flag in sorted(missing_flags, key=lambda f: f.get("risk_score", 50), reverse=True):
            score = flag.get("risk_score", "?")
            tag = f'{flag["risk_level"].upper()} · {score}'
            body = f'<strong>{flag["clause"]}</strong> — {flag["reason"]}'
            if flag.get("legal_reference"):
                body += f'<br><span style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:#9AA1AB">§ {flag["legal_reference"]}</span>'
            redline_card(tag, flag["risk_level"], body)
    else:
        st.caption("No missing-provision concerns detected.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.subheader("All Clauses")
    for i, clause in enumerate(result["clauses"], 1):
        with st.expander(f"Clause {i}"):
            st.write(clause)


# ---------------------------------------------------------------------------
# Viewing a past analysis from the sidebar history
# ---------------------------------------------------------------------------
if st.session_state.get("viewed_history"):
    hist = st.session_state.viewed_history
    st.success(f"Viewing saved analysis: {hist['filename']}")
    if st.button("← Back to new analysis"):
        del st.session_state.viewed_history
        st.rerun()
    render_results(hist, hist.get("user_position", ""), hist["filename"], show_download=True)
    st.stop()

# ---------------------------------------------------------------------------
# Upload + position
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload a contract", type=["pdf", "docx"])

position = st.selectbox(
    "Which party are you in this contract?",
    ["Not specified", "Customer / Buyer", "Vendor / Seller", "Employer", "Employee",
     "Disclosing Party (NDA)", "Receiving Party (NDA)", "Landlord", "Tenant", "Other"],
    help="Risk assessment adjusts based on whose side you're on — the same clause "
         "can be favorable for one party and risky for the other.",
)

if uploaded_file is not None:
    if st.button("Analyze Contract", type="primary"):
        with st.spinner("Running agent pipeline (classify → segment → risk → benchmark → summarize)..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {"position": position}
            try:
                response = requests.post(API_URL, files=files, data=data, timeout=300)
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to reach backend: {e}")
                st.stop()

        st.success("Analysis complete")
        render_results(result, position, uploaded_file.name)