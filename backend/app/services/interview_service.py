from __future__ import annotations

from datetime import datetime
import json
import uuid

from backend.app.schemas import (
    InterviewAnswerResponse,
    InterviewReportResponse,
    InterviewStartResponse,
    InterviewTurn,
)
from database.connection import get_connection
from ai_engine.interview import InterviewEngine

class InterviewService:
    def __init__(self) -> None:
        self.engine = InterviewEngine()

    def start_interview(self, application_id: str) -> InterviewStartResponse:
        # Simplified logic for demonstration
        session_id = uuid.uuid4().hex
        first_question = "كلمنا عن أهم مشروع اشتغلت عليه."
        
        return InterviewStartResponse(
            session_id=session_id,
            application_id=application_id,
            job_title="Software Engineer",
            candidate_name="Candidate",
            status="in_progress",
            total_questions=1,
            current_question_index=0,
            current_question=first_question,
        )

    def submit_answer(self, session_id: str, answer: str) -> InterviewAnswerResponse:
        analysis = self.engine.score_answer("", answer)
        return InterviewAnswerResponse(
            session_id=session_id,
            status="in_progress",
            current_question_index=1,
            next_question="إيه أكبر تحدي واجهته؟",
            answer_score=analysis["total_score"],
            answer_feedback=analysis["feedback"],
            is_completed=False,
        )
