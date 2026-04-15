import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.app.schemas import CandidateMatchResponse, FullCvAnalysisResponse, JobInput
from backend.app.services.analysis_service import analyze_resume_to_jobs, start_resume_analysis_job
from backend.app.services.cv_full_analysis_service import analyze_full_cv_report

router = APIRouter()


@router.post("/full-analysis", response_model=FullCvAnalysisResponse)
async def full_cv_analysis(
    file: UploadFile = File(...),
) -> FullCvAnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="الملف ناقص")

    file_bytes = await file.read()
    try:
        return analyze_full_cv_report(file_bytes=file_bytes, filename=file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze", response_model=CandidateMatchResponse)
async def analyze_cv(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("[]"),
) -> CandidateMatchResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="الملف ناقص")

    try:
        parsed_skills = json.loads(required_skills)
        if not isinstance(parsed_skills, list):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="required_skills لازم تكون JSON list") from exc

    job = JobInput(title=job_title, description=job_description, required_skills=parsed_skills)
    file_bytes = await file.read()
    return analyze_resume_to_jobs(file_bytes=file_bytes, filename=file.filename, job=job)


@router.post("/analyze/stream")
async def analyze_cv_stream(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("[]"),
):
    try:
        parsed_skills = json.loads(required_skills)
        if not isinstance(parsed_skills, list):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="required_skills لازم تكون JSON list") from exc

    job_id = uuid.uuid4().hex
    file_bytes = await file.read()
    job = JobInput(title=job_title, description=job_description, required_skills=parsed_skills)
    queue = start_resume_analysis_job(job_id=job_id, file_bytes=file_bytes, filename=file.filename or "resume", job=job)

    async def event_stream() -> AsyncGenerator[str, None]:
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("type") == "done":
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")
