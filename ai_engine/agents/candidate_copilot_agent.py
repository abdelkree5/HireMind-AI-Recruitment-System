"""
Candidate Copilot Agent — Phase 1: Candidate AI Ecosystem

Candidate-facing conversational AI that uses ReAct pattern to help candidates
with CV review, interview prep, job search, and career advice.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from ai_engine.agents.base import AgentMessage, BaseAgent
from ai_engine.tools.registry import tool_registry


class CandidateCopilotAgent(BaseAgent):
    """Conversational copilot for candidates using ReAct tool routing."""

    def __init__(self) -> None:
        super().__init__(name="candidate_copilot")

    def run(self, message: AgentMessage) -> AgentMessage:
        payload = message.payload
        user_msg = payload.get("message", "")
        result = self.chat(user_msg)
        return self.reply(message, result)

    def chat(self, message: str) -> Dict[str, Any]:
        """Route candidate queries to appropriate tools."""
        query = message.lower()
        tools_used = []
        reasoning = []

        # CV Review
        if any(k in query for k in ["review my cv", "review my resume", "cv feedback", "resume feedback"]):
            reasoning.append("Candidate wants CV review")
            cv_text = message.split(":", 1)[-1].strip() if ":" in message else message
            result = self._review_cv(cv_text)
            tools_used.append("cv_review")
            return self._format_response(result, tools_used, reasoning)

        # CV Improvement
        if any(k in query for k in ["improve", "suggestion", "better cv", "fix my resume"]):
            reasoning.append("Candidate wants CV improvement suggestions")
            cv_text = message.split(":", 1)[-1].strip() if ":" in message else message
            result = self._improve_cv(cv_text)
            tools_used.append("cv_improvement")
            return self._format_response(result, tools_used, reasoning)

        # Interview Prep
        if any(k in query for k in ["interview", "prepare", "practice"]):
            reasoning.append("Candidate wants interview preparation")
            result = self._interview_prep(message)
            tools_used.append("interview_prep")
            return self._format_response(result, tools_used, reasoning)

        # Job Search
        if any(k in query for k in ["find job", "job search", "matching job", "recommend job"]):
            reasoning.append("Candidate wants job recommendations")
            result = self._job_search(message)
            tools_used.append("job_search")
            return self._format_response(result, tools_used, reasoning)

        # Career Advice
        if any(k in query for k in ["career", "grow", "next step", "advice", "path"]):
            reasoning.append("Candidate wants career advice")
            result = self._career_advice(message)
            tools_used.append("career_advice")
            return self._format_response(result, tools_used, reasoning)

        # Skill Analysis
        if any(k in query for k in ["skill", "gap", "learn", "missing"]):
            reasoning.append("Candidate wants skill analysis")
            result = self._skill_analysis(message)
            tools_used.append("skill_analysis")
            return self._format_response(result, tools_used, reasoning)

        reasoning.append("General candidate query")
        return {
            "answer": "I can help you with: CV Review, CV Improvement, Interview Preparation, Job Search, Career Advice, and Skill Analysis. Please tell me what you need!",
            "reasoning_summary": " -> ".join(reasoning),
            "tools_used": [],
            "citations": [],
        }

    def _review_cv(self, cv_text: str) -> dict:
        from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
        agent = CVAnalysisAgent()
        try:
            result = agent.analyze_cv(text=cv_text)
            return {
                "headline": result.get("inferred_headline", ""),
                "level": result.get("level", ""),
                "skills_found": len(result.get("skills", [])),
                "primary_domain": result.get("primary_domain", ""),
                "years_experience": result.get("years_of_experience", 0),
                "leadership_score": round(result.get("leadership_score", 0) * 100, 1),
                "depth_score": round(result.get("project_depth_score", 0) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}

    def _improve_cv(self, cv_text: str) -> dict:
        from ai_engine.reasoning import build_candidate_insight
        try:
            insight = build_candidate_insight(cv_text)
            suggestions = []
            if insight.years_of_experience == 0:
                suggestions.append("Add specific years of experience to strengthen your profile.")
            if insight.leadership_score < 0.3:
                suggestions.append("Include leadership examples (led, managed, mentored) to show growth potential.")
            if insight.project_depth_score < 0.4:
                suggestions.append("Add more project details with metrics (deployed, built, optimized).")
            if len(insight.skills) < 5:
                suggestions.append("List more technical skills explicitly to improve ATS matching.")
            if not suggestions:
                suggestions.append("Your CV looks strong! Consider tailoring it for specific roles.")
            return {"suggestions": suggestions, "current_strengths": insight.skills[:10]}
        except Exception as e:
            return {"error": str(e)}

    def _interview_prep(self, message: str) -> dict:
        from ai_engine.interview import InterviewEngine, TECHNICAL_TARGETS
        engine = InterviewEngine()
        questions = []
        for skill, qs in list(TECHNICAL_TARGETS.items())[:3]:
            questions.extend([{"skill": skill, "question": q} for q in qs[:1]])
        return {"practice_questions": questions, "tip": "Use the STAR method for behavioral questions."}

    def _job_search(self, message: str) -> dict:
        from database.connection import get_connection
        try:
            with get_connection() as conn:
                jobs = conn.execute(
                    "SELECT id, title, required_skills FROM posted_jobs ORDER BY created_at DESC LIMIT 5"
                ).fetchall()
            return {"available_jobs": [{"id": r["id"], "title": r["title"]} for r in jobs]}
        except Exception as e:
            return {"jobs": [], "note": "No jobs available currently."}

    def _skill_analysis(self, message: str) -> dict:
        from ai_engine.skills import SkillExtractor
        extractor = SkillExtractor()
        skills = extractor.extract(message)
        return {"detected_skills": skills, "count": len(skills)}

    def _career_advice(self, message: str) -> dict:
        return {
            "advice": [
                "Focus on building T-shaped skills — deep in one area, broad across many.",
                "Contribute to open-source projects to build a visible portfolio.",
                "Obtain certifications in your target domain to validate expertise.",
                "Network actively and maintain an updated LinkedIn profile.",
                "Practice system design and coding challenges regularly.",
            ]
        }

    def _format_response(self, result: dict, tools_used: list, reasoning: list) -> dict:
        return {
            "answer": json.dumps(result, ensure_ascii=False),
            "reasoning_summary": " -> ".join(reasoning),
            "tools_used": tools_used,
            "citations": [],
        }


candidate_copilot_agent = CandidateCopilotAgent()
