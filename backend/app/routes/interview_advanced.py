"""Phase 2 — Advanced Interview Intelligence routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.auth_service import require_current_user

router = APIRouter(dependencies=[Depends(require_current_user)])


class CodingChallengeRequest(BaseModel):
    difficulty: str = "medium"
    tags: list[str] = Field(default_factory=list)

class CodeSubmissionRequest(BaseModel):
    code: str
    problem_id: str = ""

class BehavioralQuestionRequest(BaseModel):
    dimensions: list[str] = Field(default_factory=lambda: ["leadership", "communication", "problem_solving", "culture_fit"])
    count_per_dimension: int = 1

class BehavioralAnswerRequest(BaseModel):
    answer: str
    dimension: str = "leadership"

class BehavioralFullRequest(BaseModel):
    answers: dict = Field(default_factory=dict)

class VoiceSessionRequest(BaseModel):
    job_title: str = ""
    candidate_name: str = ""

class VoiceAudioRequest(BaseModel):
    session_id: str
    transcription: str

class InterviewCopilotQuestionsRequest(BaseModel):
    job_title: str = ""
    candidate_skills: list[str] = Field(default_factory=list)
    seniority: str = "Mid"

class InterviewCopilotFollowupRequest(BaseModel):
    answer: str
    original_question: str = ""

class InterviewSummaryRequest(BaseModel):
    turns: list[dict] = Field(default_factory=list)

class HiringRecRequest(BaseModel):
    interview_score: float = 0
    match_score: float = 0


# --- Coding Interview ---

@router.post("/coding/generate")
def generate_coding_challenge(req: CodingChallengeRequest) -> dict:
    from ai_engine.agents.coding_interview_agent import coding_interview_agent
    return coding_interview_agent.generate_challenge(req.model_dump())

@router.post("/coding/evaluate")
def evaluate_code(req: CodeSubmissionRequest) -> dict:
    from ai_engine.agents.coding_interview_agent import coding_interview_agent
    return coding_interview_agent.evaluate_submission(req.model_dump())


# --- Behavioral Interview ---

@router.post("/behavioral/questions")
def behavioral_questions(req: BehavioralQuestionRequest) -> dict:
    from ai_engine.agents.behavioral_interview_agent import behavioral_interview_agent
    return behavioral_interview_agent.generate_questions(req.model_dump())

@router.post("/behavioral/evaluate")
def behavioral_evaluate(req: BehavioralAnswerRequest) -> dict:
    from ai_engine.agents.behavioral_interview_agent import behavioral_interview_agent
    return behavioral_interview_agent.evaluate_answer(req.model_dump())

@router.post("/behavioral/full-assessment")
def behavioral_full(req: BehavioralFullRequest) -> dict:
    from ai_engine.agents.behavioral_interview_agent import behavioral_interview_agent
    return behavioral_interview_agent.full_assessment(req.model_dump())


# --- Voice Interview ---

@router.post("/voice/session")
def voice_create_session(req: VoiceSessionRequest) -> dict:
    from ai_engine.agents.voice_interview_agent import voice_interview_agent
    return voice_interview_agent.create_session(req.model_dump())

@router.post("/voice/process")
def voice_process(req: VoiceAudioRequest) -> dict:
    from ai_engine.agents.voice_interview_agent import voice_interview_agent
    return voice_interview_agent.process_audio(req.model_dump())

@router.post("/voice/confidence")
def voice_confidence(req: VoiceAudioRequest) -> dict:
    from ai_engine.agents.voice_interview_agent import voice_interview_agent
    return voice_interview_agent.score_confidence(req.model_dump())


# --- Interview Copilot ---

@router.post("/copilot/questions")
def copilot_questions(req: InterviewCopilotQuestionsRequest) -> dict:
    from ai_engine.agents.interview_copilot_agent import interview_copilot_agent
    return interview_copilot_agent.generate_questions(req.model_dump())

@router.post("/copilot/followups")
def copilot_followups(req: InterviewCopilotFollowupRequest) -> dict:
    from ai_engine.agents.interview_copilot_agent import interview_copilot_agent
    return interview_copilot_agent.generate_followups(req.model_dump())

@router.post("/copilot/summarize")
def copilot_summarize(req: InterviewSummaryRequest) -> dict:
    from ai_engine.agents.interview_copilot_agent import interview_copilot_agent
    return interview_copilot_agent.summarize_interview(req.model_dump())

@router.post("/copilot/recommendation")
def copilot_recommendation(req: HiringRecRequest) -> dict:
    from ai_engine.agents.interview_copilot_agent import interview_copilot_agent
    return interview_copilot_agent.hiring_recommendation(req.model_dump())
