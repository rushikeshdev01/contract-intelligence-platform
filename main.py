import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from services.extraction_service import extract_text
from agents.graph import run_pipeline

app = FastAPI(title="Contract Intelligence API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Contract Intelligence API is running"}


@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...), position: str = Form("")):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = extract_text(file_path)
        if not raw_text:
            raise HTTPException(status_code=422, detail="Could not extract text from file")

        result = run_pipeline(raw_text, user_position=position)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "clauses": result["clauses"],
            "risk_flags": result["risk_flags"],
            "summary": result["summary"],
        }
    finally:
        os.remove(file_path)  # clean up uploaded file after processing
