import streamlit as st
import os
from services.pdf_service import extract_pdf_text
from services.groq_service import test_groq


st.title("Multi-Agent Contract Intelligence Platform")
if st.button("Test Groq"):
    result = test_groq()
    st.success(result)
    
uploaded_file = st.file_uploader(
    "Upload a contract",
    type=["pdf", "docx"]
)

if uploaded_file is not None:

    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File saved: {uploaded_file.name}")
    
    if uploaded_file.name.endswith(".pdf"):
        text = extract_pdf_text(file_path)

        st.subheader("Extracted Text")
        st.text_area(
            "Contract Content",
            text,
            height=300
        )
    