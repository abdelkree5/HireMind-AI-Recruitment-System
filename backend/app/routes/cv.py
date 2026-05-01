import json
import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks

from backend.app.schemas import JobInput
from backend.app.services.task_service import task_store
from backend.app.services.analysis_service import analyze_resume_to_jobs
from backend.app.services.cv_full_analysis_service import analyze_full_cv_report

router = APIRouter()

def process_full_cv_task(task_id: str, file_bytes: bytes, filename: str):
    task_store.update_status(task_id, "processing")
    try:
        result = analyze_full_cv_report(file_bytes=file_bytes, filename=filename)
        task_store.set_result(task_id, result.model_dump())
    except Exception as e:
        task_store.set_error(task_id, str(e))

def process_analyze_cv_task(task_id: str, file_bytes: bytes, filename: str, job: JobInput):
    task_store.update_status(task_id, "processing")
    try:
        result = analyze_resume_to_jobs(file_bytes=file_bytes, filename=filename, job=job)
        task_store.set_result(task_id, result.model_dump())
    except Exception as e:
        task_store.set_error(task_id, str(e))

@router.post("/full-analysis")
async def full_cv_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="الملف ناقص")
    file_bytes = await file.read()
    task_id = uuid.uuid4().hex
    task_store.create_task(task_id)
    background_tasks.add_task(process_full_cv_task, task_id, file_bytes, file.filename)
    return {"task_id": task_id, "status": "processing"}

@router.post("/analyze")
async def analyze_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("[]"),
):
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
    task_id = uuid.uuid4().hex
    task_store.create_task(task_id)
    background_tasks.add_task(process_analyze_cv_task, task_id, file_bytes, file.filename, job)
    return {"task_id": task_id, "status": "processing"}
