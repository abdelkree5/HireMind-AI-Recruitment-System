"""Phase 3 — Recruiting Automation routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.auth_service import require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])


class OutreachEmailRequest(BaseModel):
    candidate_name: str
    job_title: str
    company_name: str = "HireMind"
    matched_skills: list[str] = Field(default_factory=list)
    match_score: float = 0
    candidate_id: str = ""
    job_id: str = ""

class OutreachSequenceRequest(BaseModel):
    candidate_name: str
    job_title: str

class WorkflowCreateRequest(BaseModel):
    name: str
    description: str = ""
    trigger_event: str
    steps: list[dict] = Field(default_factory=list)
    created_by: str = "system"

class HiringWorkflowRequest(BaseModel):
    candidate_text: str
    job_id: str = ""
    auto_advance: bool = True
    confidence_threshold: float = 60


@router.post("/outreach/email", dependencies=[Depends(require_role("recruiter", "admin"))])
def generate_outreach_email(req: OutreachEmailRequest) -> dict:
    from ai_engine.agents.outreach_agent import outreach_agent
    return outreach_agent.generate_email(req.model_dump())

@router.post("/outreach/linkedin", dependencies=[Depends(require_role("recruiter", "admin"))])
def generate_linkedin_message(req: OutreachEmailRequest) -> dict:
    from ai_engine.agents.outreach_agent import outreach_agent
    return outreach_agent.generate_linkedin(req.model_dump())

@router.post("/outreach/sequence", dependencies=[Depends(require_role("recruiter", "admin"))])
def generate_outreach_sequence(req: OutreachSequenceRequest) -> dict:
    from ai_engine.agents.outreach_agent import outreach_agent
    return outreach_agent.generate_sequence(req.model_dump())

@router.post("/workflow/create", dependencies=[Depends(require_role("recruiter", "admin"))])
def create_workflow(req: WorkflowCreateRequest) -> dict:
    from ai_engine.automation.workflow_builder import workflow_builder
    return workflow_builder.create_workflow(req.model_dump())

@router.get("/workflow/list", dependencies=[Depends(require_role("recruiter", "admin"))])
def list_workflows() -> dict:
    from ai_engine.automation.workflow_builder import workflow_builder
    return workflow_builder.list_workflows()

@router.get("/workflow/components")
def workflow_components() -> dict:
    from ai_engine.automation.workflow_builder import workflow_builder
    return workflow_builder.get_available_components()

@router.post("/workflow/hire", dependencies=[Depends(require_role("recruiter", "admin"))])
def run_hiring_workflow(req: HiringWorkflowRequest) -> dict:
    from ai_engine.automation.hiring_workflow import hiring_workflow_engine
    return hiring_workflow_engine.execute_workflow(req.model_dump())
