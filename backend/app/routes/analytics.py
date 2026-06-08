"""Phase 6 — Analytics & Decision Intelligence routes."""
from fastapi import APIRouter, Depends
from typing import Optional
from backend.app.services.auth_service import require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])


@router.get("/recruiter", dependencies=[Depends(require_role("recruiter", "admin"))])
def recruiter_dashboard(job_id: Optional[str] = None) -> dict:
    from ai_engine.services.analytics_service import analytics_service
    return analytics_service.recruiter_dashboard(job_id)

@router.get("/ai-performance", dependencies=[Depends(require_role("admin"))])
def ai_performance() -> dict:
    from ai_engine.services.analytics_service import analytics_service
    return analytics_service.ai_performance_dashboard()

@router.get("/executive", dependencies=[Depends(require_role("admin"))])
def executive_dashboard() -> dict:
    from ai_engine.services.analytics_service import analytics_service
    return analytics_service.executive_dashboard()

@router.get("/funnel/{job_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def candidate_funnel(job_id: str) -> dict:
    from ai_engine.services.analytics_service import analytics_service
    return analytics_service.candidate_funnel(job_id)
