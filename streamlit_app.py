import streamlit as st
import requests

API_URL = "http://localhost:8000/analyze"

st.set_page_config(page_title="Contract Intelligence Platform", layout="wide")
st.title("📄 Multi-Agent Contract Intelligence Platform")
st.caption("Upload a contract → agents extract, segment, flag risk, and summarize it.")

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
        with st.spinner("Running agent pipeline (extraction → segmentation → risk → summary)..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {"position": position}
            try:
                response = requests.post(API_URL, files=files, data=data, timeout=120)
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to reach backend: {e}")
                st.stop()

        st.success("Analysis complete")

        if result.get("document_type"):
            st.info(f"📄 Detected contract type: **{result['document_type']}**")

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

        st.subheader("📝 Executive Summary")
        st.write(result["summary"])

        risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        present_flags = [f for f in result["risk_flags"] if f.get("type", "present") == "present"]
        missing_flags = [f for f in result["risk_flags"] if f.get("type") == "missing"]

        st.subheader("📊 Market Standard Benchmarks")
        benchmarks = result.get("benchmarks", [])
        status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        if benchmarks:
            for row in benchmarks:
                icon = status_icon.get(row["status"], "⚪")
                st.markdown(
                    f"{icon} **{row['provision']}** — contract: "
                    f"{row['contract_value_days']:.0f} days · standard: {row['standard_range']}"
                )
        else:
            st.caption("No benchmarkable provisions (e.g. liability cap, notice periods) were detected in this contract.")

        st.subheader("⚠️ Risk Flags (clauses present in the contract)")
        if present_flags:
            for flag in present_flags:
                icon = risk_color.get(flag["risk_level"].lower(), "⚪")
                st.markdown(f"{icon} **{flag['risk_level'].upper()}** — {flag['reason']}")
                with st.expander("View clause"):
                    st.write(flag["clause"])
        else:
            st.caption("No risky clauses flagged.")

        st.subheader("🚫 Missing Protections (not found anywhere in the contract)")
        if missing_flags:
            st.caption("A protection that's silently absent can be riskier than one that's stated explicitly.")
            for flag in missing_flags:
                icon = risk_color.get(flag["risk_level"].lower(), "⚪")
                st.markdown(f"{icon} **{flag['clause']}** — {flag['reason']}")
        else:
            st.caption("No missing-provision concerns detected.")

        st.subheader("📋 All Clauses")
        for i, clause in enumerate(result["clauses"], 1):
            with st.expander(f"Clause {i}"):
                st.write(clause)