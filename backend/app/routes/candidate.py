"""Phase 1 — Candidate AI Ecosystem routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.auth_service import require_current_user

router = APIRouter(dependencies=[Depends(require_current_user)])


class SkillGapRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    target_role: str = ""

class CareerRoadmapRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    target_role: str = ""

class CertificationRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    target_role: str = ""

class PromotionRequest(BaseModel):
    candidate_text: str
    target_seniority: str = "Senior"

class CandidateCopilotRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class CVBuilderRequest(BaseModel):
    candidate_text: str
    format_type: str = "ats_friendly"
    candidate_id: str = ""
    linkedin_data: dict = Field(default_factory=dict)
    github_data: dict = Field(default_factory=dict)
    target_job: dict = Field(default_factory=dict)


@router.post("/coach/skill-gap")
def skill_gap_analysis(req: SkillGapRequest) -> dict:
    from ai_engine.agents.career_coach_agent import career_coach_agent
    return career_coach_agent.skill_gap_analysis(req.model_dump())


@router.post("/coach/roadmap")
def career_roadmap(req: CareerRoadmapRequest) -> dict:
    from ai_engine.agents.career_coach_agent import career_coach_agent
    return career_coach_agent.career_roadmap(req.model_dump())


@router.post("/coach/learning-plan")
def learning_plan(req: SkillGapRequest) -> dict:
    from ai_engine.agents.career_coach_agent import career_coach_agent
    return career_coach_agent.learning_plan(req.model_dump())


@router.post("/coach/certifications")
def certifications(req: CertificationRequest) -> dict:
    from ai_engine.agents.career_coach_agent import career_coach_agent
    return career_coach_agent.certification_recommendations(req.model_dump())


@router.post("/coach/promotion-readiness")
def promotion_readiness(req: PromotionRequest) -> dict:
    from ai_engine.agents.career_coach_agent import career_coach_agent
    return career_coach_agent.promotion_readiness(req.model_dump())


@router.post("/copilot/chat")
def candidate_copilot_chat(req: CandidateCopilotRequest) -> dict:
    from ai_engine.agents.candidate_copilot_agent import candidate_copilot_agent
    return candidate_copilot_agent.chat(req.message)


@router.post("/cv-builder/generate")
def generate_cv(req: CVBuilderRequest) -> dict:
    from ai_engine.services.cv_builder_service import cv_builder_service
    return cv_builder_service.generate_cv(req.model_dump())
