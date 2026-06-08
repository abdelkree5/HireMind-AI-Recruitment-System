"""
Recruiter Feedback Agent

Responsibilities:
  - Feedback collection and storage
  - Recruiter decision analytics (FP/FN, agreement rate)
  - Preference model building from historical decisions
  - Rejection pattern detection
  - Hiring success pattern analysis
  - Continuous skill weight learning

Wraps: backend/app/services/feedback_service.py, ai_engine/feedback.py
"""
from __future__ import annotations

from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class RecruiterFeedbackAgent(BaseAgent):
    """Manages the full recruiter feedback loop."""

    def __init__(self) -> None:
        super().__init__(name="recruiter_feedback")

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "collect_feedback":
            result = self.collect_feedback(payload)
        elif task == "compute_analytics":
            result = self.compute_analytics()
        elif task == "generate_preference_model":
            result = self.generate_preference_model(payload.get("job_id", ""))
        elif task == "detect_rejection_patterns":
            result = self.detect_rejection_patterns(payload.get("job_id", ""))
        elif task == "get_skill_heatmap":
            result = self.get_skill_heatmap(payload.get("job_id", ""))
        elif task == "generate_feedback_report":
            result = {"report": self.generate_feedback_report(payload.get("job_id", ""))}
        else:
            raise ValueError(f"RecruiterFeedbackAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def collect_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Store recruiter feedback and trigger learning loop."""
        from backend.app.services.feedback_service import feedback_service
        return feedback_service.submit_feedback(payload)

    def compute_analytics(self) -> dict[str, Any]:
        """Compute comprehensive recruiter analytics."""
        from backend.app.services.feedback_service import feedback_service
        return feedback_service.get_feedback_analytics()

    def generate_preference_model(self, job_id: str) -> dict[str, Any]:
        """
        Build a recruiter preference model for a specific job.
        Returns: preferred_skills, avoided_skills, avg_accepted_score,
                 acceptance_rate, top_rejection_reasons
        """
        from ai_engine.feedback import build_recruiter_preference_model
        return build_recruiter_preference_model(job_id)

    def detect_rejection_patterns(self, job_id: str) -> dict[str, Any]:
        """
        Identify common patterns in rejected candidates for a job.
        Returns: top_rejection_reasons, most_missing_skills, avg_rejected_score
        """
        from ai_engine.feedback import detect_rejection_patterns
        return detect_rejection_patterns(job_id)

    def get_skill_heatmap(self, job_id: str) -> dict[str, Any]:
        """
        Build a skill acceptance/rejection matrix.
        Returns: skill → {accepted_count, rejected_count, acceptance_rate}
        """
        try:
            from database.connection import get_connection
            import json

            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT rf.is_accepted, ja.candidate_skills
                    FROM recruiter_feedback rf
                    JOIN job_applications ja ON rf.application_id = ja.id
                    WHERE rf.job_id = ?
                    """,
                    (job_id,),
                ).fetchall()

            heatmap: dict[str, dict[str, int]] = {}
            for row in rows:
                skills = []
                try:
                    skills = json.loads(row["candidate_skills"] or "[]")
                except Exception:
                    pass
                accepted = int(row["is_accepted"])
                for skill in skills:
                    skill_key = skill.lower().strip()
                    if skill_key not in heatmap:
                        heatmap[skill_key] = {"accepted": 0, "rejected": 0}
                    if accepted:
                        heatmap[skill_key]["accepted"] += 1
                    else:
                        heatmap[skill_key]["rejected"] += 1

            result = {}
            for skill, counts in heatmap.items():
                total = counts["accepted"] + counts["rejected"]
                result[skill] = {
                    "accepted_count": counts["accepted"],
                    "rejected_count": counts["rejected"],
                    "acceptance_rate": round(counts["accepted"] / total, 4) if total else 0.0,
                }

            return {"job_id": job_id, "skill_heatmap": result}
        except Exception as exc:
            return {"job_id": job_id, "skill_heatmap": {}, "error": str(exc)}

    def generate_feedback_report(self, job_id: str) -> str:
        """Generate a human-readable markdown feedback insight report."""
        from ai_engine.feedback import generate_feedback_report
        return generate_feedback_report(job_id)


recruiter_feedback_agent = RecruiterFeedbackAgent()
