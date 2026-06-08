import json
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.schemas import (
    CandidateProfile,
    CandidateComparisonRequest,
    CandidateComparisonResponse,
    CandidateMatchResponse,
    CompanyDashboardResponse,
    JobApplication,
    JobInput,
    JobMatchRequest,
    PostedJob,
    PostedJobDetails,
    PostedJobsResponse,
    TopMatchesRequest,
    TopMatchesResponse,
)
from backend.app.services.analysis_service import (
    compare_candidates_for_job,
    match_candidate_to_job,
    rank_jobs_for_candidate,
    rank_jobs_for_resume,
)
from backend.app.services.auth_service import require_current_user, require_role
from backend.app.services.recruitment_service import recruitment_service

router = APIRouter(dependencies=[Depends(require_current_user)])
MAX_UPLOAD_BYTES = int(os.getenv("HIREMIND_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))


def _enforce_upload_limit(file_bytes: bytes) -> None:
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the maximum allowed size.")


@router.post("/match", response_model=CandidateMatchResponse)
def match_job(payload: JobMatchRequest) -> CandidateMatchResponse:
    return match_candidate_to_job(payload.job, payload.candidate)


@router.post("/top-matches", response_model=TopMatchesResponse)
def top_matches(payload: TopMatchesRequest) -> TopMatchesResponse:
    return rank_jobs_for_candidate(payload.candidate, payload.jobs)


@router.post("/top-matches/from-cv", response_model=TopMatchesResponse)
async def top_matches_from_cv(
    file: UploadFile = File(...),
    jobs: str = Form("[]"),
) -> TopMatchesResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="الملف ناقص")

    try:
        parsed_jobs = json.loads(jobs)
        if not isinstance(parsed_jobs, list):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="jobs لازم تكون JSON list") from exc

    file_bytes = await file.read()
    _enforce_upload_limit(file_bytes)
    jobs_payload = [job if isinstance(job, JobInput) else JobInput(**job) for job in parsed_jobs]
    return rank_jobs_for_resume(file_bytes, file.filename, jobs_payload or None)


@router.post("/top-matches/general-from-cv", response_model=TopMatchesResponse)
async def top_matches_general_from_cv(
    file: UploadFile = File(...),
) -> TopMatchesResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="الملف ناقص")

    file_bytes = await file.read()
    _enforce_upload_limit(file_bytes)
    # Always rank against the global job-title library, never posted company jobs.
    return rank_jobs_for_resume(file_bytes, file.filename, None)


@router.post("/compare-candidates", response_model=CandidateComparisonResponse)
def compare_candidates(payload: CandidateComparisonRequest) -> CandidateComparisonResponse:
    return compare_candidates_for_job(payload.job, payload.candidates)


@router.post("/posted", response_model=PostedJob, dependencies=[Depends(require_role("recruiter", "admin"))])
def create_posted_job(payload: JobInput) -> PostedJob:
    return recruitment_service.create_job(payload)


@router.post("/posted/seed-realistic", dependencies=[Depends(require_role("admin"))])
def seed_realistic_jobs() -> dict:
    outcome = recruitment_service.seed_realistic_jobs()
    created = outcome.get("created", [])
    updated = outcome.get("updated", [])
    return {
        "created_count": len(created),
        "updated_count": len(updated),
        "jobs": [job.model_dump() for job in created],
        "updated_jobs": [job.model_dump() for job in updated],
    }


@router.get("/posted", response_model=PostedJobsResponse)
def list_posted_jobs() -> PostedJobsResponse:
    return PostedJobsResponse(jobs=recruitment_service.list_jobs())


@router.get("/posted/{job_id}", response_model=PostedJobDetails)
def posted_job_details(job_id: str) -> PostedJobDetails:
    try:
        return recruitment_service.get_job_details(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/posted/{job_id}/apply", response_model=JobApplication)
async def apply_to_posted_job(
    job_id: str,
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    candidate_headline: str = Form("Candidate"),
    candidate_skills: str = Form("[]"),
    candidate_summary: str = Form(""),
) -> JobApplication:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    try:
        parsed_skills = json.loads(candidate_skills)
        if not isinstance(parsed_skills, list):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="candidate_skills must be JSON list") from exc

    try:
        file_bytes = await file.read()
        _enforce_upload_limit(file_bytes)
        profile = CandidateProfile(
            name=candidate_name,
            headline=candidate_headline,
            skills=parsed_skills,
            summary=candidate_summary,
        )
        return recruitment_service.apply_to_job(job_id, file_bytes, file.filename, profile)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/apply")
async def apply_cv_only(
    job_id: str = Form(...),
    file: UploadFile = File(...),
    confirmed_skills: str | None = Form(None),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    try:
        file_bytes = await file.read()
        _enforce_upload_limit(file_bytes)
        confirmed_list = json.loads(confirmed_skills) if confirmed_skills else None
        return recruitment_service.apply_to_job_cv_only(
            job_id, file_bytes, file.filename, confirmed_skills=confirmed_list
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive API fallback
        raise HTTPException(status_code=500, detail=f"Apply pipeline failed: {exc}") from exc


@router.post("/pre-match")
async def pre_match_cv(
    job_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    try:
        file_bytes = await file.read()
        _enforce_upload_limit(file_bytes)
        return recruitment_service.pre_match_report(job_id, file_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/posted/{job_id}", response_model=PostedJob, dependencies=[Depends(require_role("recruiter", "admin"))])
def update_posted_job(job_id: str, payload: JobInput) -> PostedJob:
    try:
        return recruitment_service.update_job(job_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/posted/{job_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def delete_posted_job(job_id: str) -> dict:
    try:
        recruitment_service.delete_job(job_id)
        return {"status": "deleted", "job_id": job_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/company/dashboard", response_model=CompanyDashboardResponse, dependencies=[Depends(require_role("recruiter", "admin"))])
def company_dashboard(
    sort_by: str = "score",
    order: str = "desc",
    min_score: float | None = None,
    since_date: str | None = None,
) -> CompanyDashboardResponse:
    return recruitment_service.company_dashboard(
        sort_by=sort_by,
        order=order,
        min_score=min_score,
        since_date=since_date,
    )
