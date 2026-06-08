from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Any
from backend.app.services.feedback_service import feedback_service
from ai_engine.training.ltr_pipeline import ltr_pipeline
from backend.app.services.auth_service import require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])

@router.post("", dependencies=[Depends(require_role("recruiter", "admin"))])
def submit_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    if "application_id" not in payload or "job_id" not in payload or "ai_score" not in payload:
        raise HTTPException(status_code=400, detail="Missing required fields: application_id, job_id, ai_score")
    try:
        return feedback_service.submit_feedback(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.put("/{feedback_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def update_feedback(feedback_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return feedback_service.update_feedback(feedback_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/analytics", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_feedback_analytics() -> dict[str, Any]:
    try:
        return feedback_service.get_feedback_analytics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/{application_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_feedback(application_id: str) -> dict[str, Any]:
    res = feedback_service.get_feedback(application_id)
    if not res:
        raise HTTPException(status_code=404, detail="Feedback not found for this application")
    return res

@router.get("/job/{job_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_feedback_by_job(job_id: str) -> list[dict[str, Any]]:
    try:
        return feedback_service.get_feedback_by_job(job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/ltr/train", dependencies=[Depends(require_role("admin"))])
def train_ltr(background_tasks: BackgroundTasks) -> dict[str, Any]:
    try:
        # Run training in background or synchronously since it is fast
        res = ltr_pipeline.train()
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/ltr/info", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_ltr_info() -> dict[str, Any]:
    metadata = ltr_pipeline.get_metadata()
    if not metadata:
        return {
            "status": "not_trained",
            "message": "No LTR model trained yet. Submit feedback to begin training."
        }
    return {
        "status": "trained",
        "metadata": metadata
    }
