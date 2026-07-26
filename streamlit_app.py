import streamlit as st
import requests
from services.report_generator import build_docx_report

API_URL = "http://localhost:8000/analyze"

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
.section-divider {{
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1.6rem 0 1.1rem 0;
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

        docx_buffer = build_docx_report(result, position, filename=uploaded_file.name)
        st.download_button(
            label="⬇️  Download Report (.docx)",
            data=docx_buffer,
            file_name=f"contract_analysis_{uploaded_file.name.rsplit('.', 1)[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        if result.get("document_type"):
            st.markdown(
                f'<div class="eyebrow" style="margin-top:1.2rem">Detected Type</div>'
                f'<div style="font-size:1.05rem;color:#E9E6DD;margin-bottom:0.8rem">{result["document_type"]}</div>',
                unsafe_allow_html=True,
            )

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

        present_flags = [f for f in result["risk_flags"] if f.get("type", "present") == "present"]
        missing_flags = [f for f in result["risk_flags"] if f.get("type") == "missing"]
        benchmarks = result.get("benchmarks", [])

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
            for flag in present_flags:
                redline_card(flag["risk_level"], flag["risk_level"], flag["reason"])
                with st.expander("View clause"):
                    st.write(flag["clause"])
        else:
            st.caption("No risky clauses flagged.")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("Missing Protections — not found anywhere in the contract")
        if missing_flags:
            st.caption("A protection that's silently absent can be riskier than one that's stated explicitly.")
            for flag in missing_flags:
                body = f'<strong>{flag["clause"]}</strong> — {flag["reason"]}'
                redline_card(flag["risk_level"], flag["risk_level"], body)
        else:
            st.caption("No missing-provision concerns detected.")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("All Clauses")
        for i, clause in enumerate(result["clauses"], 1):
            with st.expander(f"Clause {i}"):
                st.write(clause)