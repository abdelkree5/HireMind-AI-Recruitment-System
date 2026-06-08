"""
AI Outreach Agent — Phase 3: Recruiting Automation

Generates personalized recruitment communications across multiple channels.
"""
from __future__ import annotations

import uuid
import json
import logging
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class OutreachAgent(BaseAgent):
    """Generates personalized outreach messages for candidate engagement."""

    def __init__(self) -> None:
        super().__init__(name="outreach")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        handlers = {
            "generate_email": self.generate_email,
            "generate_linkedin": self.generate_linkedin,
            "generate_sequence": self.generate_sequence,
        }
        handler = handlers.get(task)
        if not handler:
            raise ValueError(f"OutreachAgent: unknown task_type '{task}'")

        return self.reply(message, handler(payload))

    def generate_email(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate a personalized recruitment email."""
        candidate_name = payload.get("candidate_name", "Candidate")
        job_title = payload.get("job_title", "an exciting role")
        company = payload.get("company_name", "our company")
        skills = payload.get("matched_skills", [])
        match_score = payload.get("match_score", 0)

        skill_highlight = ", ".join(skills[:3]) if skills else "your technical expertise"

        subject = f"Exciting {job_title} Opportunity — Your Profile Stood Out"
        body = f"""Hi {candidate_name},

I came across your profile and was impressed by your background in {skill_highlight}. We have an opening for {job_title} at {company} that aligns closely with your experience.

Based on our analysis, your profile matches {round(match_score, 1)}% of the role requirements, which puts you among our top candidates.

Would you be open to a brief conversation about this opportunity?

Best regards,
Recruiting Team at {company}"""

        msg_id = str(uuid.uuid4())
        self._save_outreach(msg_id, payload.get("candidate_id", ""), payload.get("job_id", ""), "email", body)

        return {"message_id": msg_id, "channel": "email", "subject": subject, "body": body}

    def generate_linkedin(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate a LinkedIn-optimized message (shorter format)."""
        candidate_name = payload.get("candidate_name", "there")
        job_title = payload.get("job_title", "a great role")
        skills = payload.get("matched_skills", [])

        skill_text = " and ".join(skills[:2]) if skills else "your skills"

        body = f"""Hi {candidate_name}! Your {skill_text} background caught our attention. We're hiring for {job_title} and think you'd be a strong fit. Open to chatting?"""

        msg_id = str(uuid.uuid4())
        self._save_outreach(msg_id, payload.get("candidate_id", ""), payload.get("job_id", ""), "linkedin", body)

        return {"message_id": msg_id, "channel": "linkedin", "body": body, "char_count": len(body)}

    def generate_sequence(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate a 3-touch follow-up sequence."""
        candidate_name = payload.get("candidate_name", "there")
        job_title = payload.get("job_title", "the role")

        sequence = [
            {"position": 1, "delay_days": 0, "subject": f"{job_title} Opportunity",
             "body": f"Hi {candidate_name}, your profile is a strong match for {job_title}. Would you be open to discussing this?"},
            {"position": 2, "delay_days": 3, "subject": f"Following Up — {job_title}",
             "body": f"Hi {candidate_name}, just wanted to follow up on my previous message. This {job_title} role is still open and your profile remains a top match."},
            {"position": 3, "delay_days": 7, "subject": f"Final Check — {job_title}",
             "body": f"Hi {candidate_name}, last follow-up on the {job_title} position. If the timing isn't right, I completely understand. Feel free to reach out in the future!"},
        ]

        return {"sequence": sequence, "total_touches": len(sequence)}

    def _save_outreach(self, msg_id, candidate_id, job_id, channel, content):
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO outreach_messages (id, candidate_id, job_id, channel, message_content, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (msg_id, candidate_id, job_id, channel, content, "draft",
                     datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            logger.warning("Failed to save outreach message: %s", e)


outreach_agent = OutreachAgent()
