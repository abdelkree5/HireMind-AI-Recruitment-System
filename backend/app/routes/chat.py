from fastapi import APIRouter, HTTPException

from backend.app.schemas import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewMessage,
    InterviewReportResponse,
    InterviewStartRequest,
    InterviewStartResponse,
)
from backend.app.services.interview_service import (
    continue_interview,
    get_interview_report,
    get_latest_interview_for_application,
    start_job_linked_interview,
    submit_interview_answer,
)

router = APIRouter()


@router.post("/interview/start", response_model=InterviewStartResponse)
def start_interview(payload: InterviewStartRequest) -> InterviewStartResponse:
    try:
        return start_job_linked_interview(payload.application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/interview/answer", response_model=InterviewAnswerResponse)
def answer_interview(payload: InterviewAnswerRequest) -> InterviewAnswerResponse:
    try:
        return submit_interview_answer(payload.session_id, payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/interview/report/{session_id}", response_model=InterviewReportResponse)
def interview_report(session_id: str) -> InterviewReportResponse:
    try:
        return get_interview_report(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/interview/latest/{application_id}", response_model=InterviewReportResponse | None)
def latest_interview(application_id: str) -> InterviewReportResponse | None:
    return get_latest_interview_for_application(application_id)


@router.post("/interview")
def interview(message: InterviewMessage) -> dict:
    if not message.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return continue_interview(message.session_id, message.message)
