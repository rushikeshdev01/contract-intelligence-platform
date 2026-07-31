import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.extraction_service import extract_text
from services.scoring import compute_overall_risk
from services.database import init_db, save_analysis, get_recent_analyses, get_analysis_by_id
from agents.graph import run_pipeline
from agents.chat_agent import answer_question

app = FastAPI(title="Contract Intelligence API")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

init_db()


class AskRequest(BaseModel):
    clauses: list[str]
    question: str
    document_type: str = ""
    user_position: str = ""


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

        overall_score, grade = compute_overall_risk(result["risk_flags"])

        response = {
            "document_type": result.get("document_type", ""),
            "clauses": result["clauses"],
            "risk_flags": result["risk_flags"],
            "benchmarks": result.get("benchmarks", []),
            "summary": result["summary"],
            "overall_score": overall_score,
            "grade": grade,
        }

        analysis_id = save_analysis(file.filename, position, result, overall_score, grade)
        response["analysis_id"] = analysis_id

        return response
    finally:
        os.remove(file_path)  # clean up uploaded file after processing


@app.get("/history")
def history(limit: int = 20):
    return {"analyses": get_recent_analyses(limit)}


@app.get("/history/{analysis_id}")
def history_detail(analysis_id: int):
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@app.post("/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = answer_question(req.clauses, req.question, req.document_type, req.user_position)
    return {"answer": answer}