"""
Voice Interview Agent — Phase 2: Advanced Interview Intelligence

Architecture-ready agent with STT/TTS integration points.
Manages voice interview sessions with follow-up question generation.
"""
from __future__ import annotations

import uuid
import re
from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class VoiceInterviewAgent(BaseAgent):
    """Voice interview with STT/TTS integration stubs."""

    def __init__(self) -> None:
        super().__init__(name="voice_interview")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "create_session":
            result = self.create_session(payload)
        elif task == "process_audio":
            result = self.process_audio(payload)
        elif task == "generate_followup":
            result = self.generate_followup(payload)
        elif task == "score_confidence":
            result = self.score_confidence(payload)
        else:
            raise ValueError(f"VoiceInterviewAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new voice interview session."""
        return {
            "session_id": str(uuid.uuid4()),
            "status": "ready",
            "stt_engine": "whisper_stub",
            "tts_engine": "edge_tts_stub",
            "job_title": payload.get("job_title", ""),
            "candidate_name": payload.get("candidate_name", ""),
            "mode": "real_time",
        }

    def process_audio(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process audio input. In production, this would invoke STT.
        For now, accepts text transcription directly.
        """
        transcription = payload.get("transcription", "")
        session_id = payload.get("session_id", "")

        if not transcription:
            return {"error": "No transcription provided. STT integration pending."}

        # Analyze transcription
        word_count = len(transcription.split())
        filler_words = len(re.findall(r"\b(um|uh|like|you know|basically|actually)\b", transcription.lower()))

        return {
            "session_id": session_id,
            "transcription": transcription,
            "word_count": word_count,
            "filler_word_count": filler_words,
            "fluency_score": max(0, 100 - filler_words * 10),
        }

    def generate_followup(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate follow-up questions based on the previous answer."""
        previous_answer = payload.get("previous_answer", "")
        topic = payload.get("topic", "general")

        followups = []
        if "project" in previous_answer.lower():
            followups.append("Can you walk me through the technical architecture of that project?")
        if "team" in previous_answer.lower():
            followups.append("What was your specific role and contribution within the team?")
        if "challenge" in previous_answer.lower():
            followups.append("What alternatives did you consider before choosing your approach?")

        if not followups:
            followups = [
                "Can you elaborate on that with a specific example?",
                "What was the most important lesson you learned from that experience?",
            ]

        return {"follow_up_questions": followups}

    def score_confidence(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Score candidate confidence from transcription signals."""
        text = payload.get("transcription", "")
        lower = text.lower()

        # Positive signals
        assertive = len(re.findall(r"\b(i led|i built|i designed|i decided|i created|i managed)\b", lower))
        specific = len(re.findall(r"\d+%|\d+ (users|requests|team|clients)", lower))

        # Negative signals
        hedge = len(re.findall(r"\b(maybe|possibly|sort of|kind of|i think|i guess|not sure)\b", lower))
        filler = len(re.findall(r"\b(um|uh|like|you know)\b", lower))

        score = min(100, max(0, 50 + assertive * 10 + specific * 8 - hedge * 12 - filler * 5))

        return {
            "confidence_score": score,
            "assertive_signals": assertive,
            "specificity_signals": specific,
            "hedge_signals": hedge,
            "filler_signals": filler,
            "level": "High" if score >= 75 else "Medium" if score >= 45 else "Low",
        }


voice_interview_agent = VoiceInterviewAgent()
