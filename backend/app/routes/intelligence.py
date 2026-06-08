"""Phase 4 — Agentic Intelligence routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.auth_service import require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])


class DebateRequest(BaseModel):
    candidate_data: dict = Field(default_factory=dict)
    job_data: dict = Field(default_factory=dict)

class ReflectionRequest(BaseModel):
    match_score: float = 0
    rule_status: str = "PASSED"
    interview_score: Optional[float] = None
    recommendation: str = ""
    workflow_id: str = ""

class PipelineReviewRequest(BaseModel):
    stages: dict = Field(default_factory=dict)

class HallucinationRequest(BaseModel):
    claims: list[str] = Field(default_factory=list)
    evidence: str = ""


@router.post("/debate/run", dependencies=[Depends(require_role("recruiter", "admin"))])
def run_debate(req: DebateRequest) -> dict:
    from ai_engine.agents.debate_agent import debate_agent
    return debate_agent.run_debate(req.model_dump())

@router.post("/reflection/review", dependencies=[Depends(require_role("recruiter", "admin"))])
def review_decision(req: ReflectionRequest) -> dict:
    from ai_engine.agents.reflection_agent import reflection_agent
    return reflection_agent.review_decision(req.model_dump())

@router.post("/reflection/pipeline", dependencies=[Depends(require_role("recruiter", "admin"))])
def review_pipeline(req: PipelineReviewRequest) -> dict:
    from ai_engine.agents.reflection_agent import reflection_agent
    return reflection_agent.review_pipeline(req.model_dump())

@router.post("/evaluation/hallucination")
def detect_hallucination(req: HallucinationRequest) -> dict:
    from ai_engine.agents.evaluation_agent import evaluation_agent
    return evaluation_agent.detect_hallucination(req.model_dump())

@router.get("/evaluation/quality")
def evaluate_quality() -> dict:
    from ai_engine.agents.evaluation_agent import evaluation_agent
    return evaluation_agent.evaluate_quality({})

@router.get("/evaluation/agents")
def agent_performance() -> dict:
    from ai_engine.agents.evaluation_agent import evaluation_agent
    return evaluation_agent.agent_performance_report()
