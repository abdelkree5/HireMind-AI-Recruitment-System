import json
import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.schemas import JobInput
from backend.app.services.auth_service import require_current_user
from backend.app.services.analysis_service import analyze_resume_to_jobs
from backend.app.services.cv_full_analysis_service import analyze_full_cv_report

router = APIRouter(dependencies=[Depends(require_current_user)])
MAX_UPLOAD_BYTES = int(os.getenv("HIREMIND_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))


def _enforce_upload_limit(file_bytes: bytes) -> None:
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the maximum allowed size.")

@router.post("/full-analysis")
async def full_cv_analysis(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is missing")
    file_bytes = await file.read()
    _enforce_upload_limit(file_bytes)
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
    _enforce_upload_limit(file_bytes)
    result = analyze_resume_to_jobs(file_bytes=file_bytes, filename=file.filename, job=job)
    return result.model_dump()
