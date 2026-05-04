import json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.schemas import JobInput
from backend.app.services.analysis_service import analyze_resume_to_jobs
from backend.app.services.cv_full_analysis_service import analyze_full_cv_report

router = APIRouter()

@router.post("/full-analysis")
async def full_cv_analysis(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is missing")
    file_bytes = await file.read()
    result = analyze_full_cv_report(file_bytes=file_bytes, filename=file.filename)
    return result.model_dump()

@router.post("/analyze")
async def analyze_cv(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("[]"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is missing")
    try:
        parsed_skills = json.loads(required_skills)
        if not isinstance(parsed_skills, list):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="required_skills must be a JSON list") from exc

    job = JobInput(title=job_title, description=job_description, required_skills=parsed_skills)
    file_bytes = await file.read()
    result = analyze_resume_to_jobs(file_bytes=file_bytes, filename=file.filename, job=job)
    return result.model_dump()
