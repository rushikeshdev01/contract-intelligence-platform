import streamlit as st
import os
from pypdf import PdfReader


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text


st.title("Multi-Agent Contract Intelligence Platform")

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