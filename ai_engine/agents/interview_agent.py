"""
Interview Agent

Responsibilities:
  - Interview session generation (personalized per job/candidate)
  - Adaptive question generation (difficulty adjusts to scores)
  - Technical depth, clarity, impact scoring per answer
  - Session finalization with strengths/weaknesses report
  - Hire recommendation

Wraps: backend/app/services/interview_service.py
"""
from __future__ import annotations

from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class InterviewAgent(BaseAgent):
    """Generates and scores adaptive technical interviews."""

    def __init__(self) -> None:
        super().__init__(name="interview")

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "start_interview":
            result = self.start_interview(payload["application_id"])
        elif task == "submit_answer":
            result = self.submit_answer(payload["session_id"], payload["answer"])
        elif task == "finalize_interview":
            result = self.finalize_interview(payload["session_id"])
        elif task == "get_report":
            result = self.get_report(payload["session_id"])
        else:
            raise ValueError(f"InterviewAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def start_interview(self, application_id: str) -> dict[str, Any]:
        """Start a new interview session for a candidate application."""
        from backend.app.services.interview_service import start_job_linked_interview
        response = start_job_linked_interview(application_id)
        return response.model_dump()

    def submit_answer(self, session_id: str, answer: str) -> dict[str, Any]:
        """Submit an answer for the current interview question."""
        from backend.app.services.interview_service import submit_interview_answer
        response = submit_interview_answer(session_id, answer)
        return response.model_dump()

    def finalize_interview(self, session_id: str) -> dict[str, Any]:
        """Force-finalize a session and compute final scores."""
        from backend.app.services.interview_service import _finalize_session
        report = _finalize_session(session_id)
        return report.model_dump()

    def get_report(self, session_id: str) -> dict[str, Any]:
        """Retrieve the complete interview report for a session."""
        from backend.app.services.interview_service import get_interview_report
        report = get_interview_report(session_id)
        return report.model_dump()


interview_agent = InterviewAgent()
