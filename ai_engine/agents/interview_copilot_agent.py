"""
Interview Copilot Agent — Phase 2: Advanced Interview Intelligence

Assists recruiters during live interviews with question generation,
follow-ups, summaries, and hiring recommendations.
"""
from __future__ import annotations

from typing import Any
from ai_engine.agents.base import AgentMessage, BaseAgent


class InterviewCopilotAgent(BaseAgent):
    """Real-time interview assistant for recruiters."""

    def __init__(self) -> None:
        super().__init__(name="interview_copilot")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        handlers = {
            "generate_questions": self.generate_questions,
            "generate_followups": self.generate_followups,
            "summarize_interview": self.summarize_interview,
            "hiring_recommendation": self.hiring_recommendation,
        }

        handler = handlers.get(task)
        if not handler:
            raise ValueError(f"InterviewCopilotAgent: unknown task_type '{task}'")

        return self.reply(message, handler(payload))

    def generate_questions(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate targeted interview questions from job + candidate context."""
        job_title = payload.get("job_title", "")
        skills = payload.get("candidate_skills", [])
        seniority = payload.get("seniority", "Mid")

        questions = []
        for skill in skills[:5]:
            if seniority in ("Senior", "Lead"):
                questions.append(f"Describe a complex system you designed using {skill}. What trade-offs did you make?")
            else:
                questions.append(f"Tell me about your experience with {skill}. What projects have you used it in?")

        questions.append(f"Why are you interested in the {job_title} role?")
        questions.append("Where do you see yourself professionally in three years?")

        return {"questions": questions, "total": len(questions), "seniority_adjusted": True}

    def generate_followups(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate follow-up questions based on candidate's answer."""
        answer = payload.get("answer", "")
        original_question = payload.get("original_question", "")

        followups = []
        lower = answer.lower()

        if "team" in lower:
            followups.append("How many people were on the team, and what was your specific role?")
        if any(w in lower for w in ["built", "created", "designed"]):
            followups.append("What was the scale of that system? How many users/requests?")
        if "challenge" in lower or "problem" in lower:
            followups.append("What alternatives did you consider, and why did you choose this approach?")
        if not followups:
            followups.append("Can you provide a more specific example of that?")
            followups.append("What was the measurable impact of your contribution?")

        return {"follow_ups": followups}

    def summarize_interview(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Summarize interview turns into a structured report."""
        turns = payload.get("turns", [])
        if not turns:
            return {"summary": "No interview data to summarize."}

        scores = [t.get("score", 0) for t in turns]
        avg_score = sum(scores) / max(1, len(scores))

        strengths = [t["question"] for t in turns if t.get("score", 0) >= 70]
        weaknesses = [t["question"] for t in turns if t.get("score", 0) < 50]

        return {
            "total_questions": len(turns),
            "average_score": round(avg_score, 1),
            "strong_areas": strengths[:3],
            "weak_areas": weaknesses[:3],
            "summary": f"Candidate answered {len(turns)} questions with an average score of {round(avg_score, 1)}%.",
        }

    def hiring_recommendation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Combine interview + match scores for final recommendation."""
        interview_score = payload.get("interview_score", 0)
        match_score = payload.get("match_score", 0)

        composite = interview_score * 0.6 + match_score * 0.4

        if composite >= 75:
            rec = "Strong Hire"
        elif composite >= 60:
            rec = "Hire"
        elif composite >= 45:
            rec = "Lean Hire — Additional Assessment Recommended"
        else:
            rec = "Pass"

        return {
            "recommendation": rec,
            "composite_score": round(composite, 1),
            "interview_weight": 0.6,
            "match_weight": 0.4,
        }


interview_copilot_agent = InterviewCopilotAgent()
