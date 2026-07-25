import streamlit as st
import requests

API_URL = "http://localhost:8000/analyze"

st.set_page_config(page_title="Contract Intelligence Platform", layout="wide")
st.title("📄 Multi-Agent Contract Intelligence Platform")
st.caption("Upload a contract → agents extract, segment, flag risk, and summarize it.")

uploaded_file = st.file_uploader("Upload a contract", type=["pdf", "docx"])

if uploaded_file is not None:
    if st.button("Analyze Contract", type="primary"):
        with st.spinner("Running agent pipeline (extraction → segmentation → risk → summary)..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                response = requests.post(API_URL, files=files, timeout=120)
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to reach backend: {e}")
                st.stop()

        st.success("Analysis complete")

        st.subheader("📝 Executive Summary")
        st.write(result["summary"])

        risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        present_flags = [f for f in result["risk_flags"] if f.get("type", "present") == "present"]
        missing_flags = [f for f in result["risk_flags"] if f.get("type") == "missing"]

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
