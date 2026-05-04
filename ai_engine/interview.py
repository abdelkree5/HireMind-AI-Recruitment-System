from __future__ import annotations

import re
from dataclasses import dataclass, field
from ai_engine.skills import SkillExtractor

TECHNICAL_TARGETS = {
    "rest api": [
        "How did you handle performance, scaling, and error handling in that API?",
        "What was your strategy for API versioning and documentation for other teams?",
        "If the API started receiving 10x more traffic tomorrow, what's the first thing you'd refactor?",
    ],
    "postgresql": [
        "How did you design indexes, queries, and transactions for that data model?",
        "Explain how you'd handle a long-running migration on a table with millions of rows.",
        "How do you ensure data integrity when multiple services are writing to the same database?",
    ],
    "python": [
        "Which Python patterns, testing approach, or architecture choices did you use?",
        "How do you manage memory and performance in Python when processing large datasets?",
        "Tell me about a time you had to debug a complex race condition or performance bottleneck in Python.",
    ],
    "fastapi": [
        "How did you structure dependencies, validation, and background tasks in FastAPI?",
        "Why did you choose FastAPI over other frameworks for that specific project?",
    ],
}

PERSONAS = [
    {"name": "سارة", "role": "Senior Architect", "style": "technical and thorough"},
    {"name": "أليكس", "role": "Engineering Lead", "style": "practical and team-focused"},
    {"name": "مايا", "role": "Staff Engineer", "style": "system-oriented and analytical"},
]

class InterviewEngine:
    def __init__(self) -> None:
        self.skill_extractor = SkillExtractor()

    def score_answer(self, question: str, answer: str) -> dict:
        detected_skills = self.skill_extractor.extract(answer)
        
        tech_score = self._score_depth(answer, detected_skills)
        clarity_score = self._score_clarity(answer)
        
        total_score = (tech_score * 0.6) + (clarity_score * 0.4)
        
        return {
            "total_score": round(total_score, 2),
            "detected_skills": detected_skills,
            "feedback": "إجابة جيدة، حاول توضح أكتر الجوانب التقنية." if total_score < 70 else "إجابة ممتازة وشاملة."
        }

    def generate_next_question(self, history: list[dict], job_title: str) -> str:
        # Simple heuristic for now, can be expanded
        if not history:
            return f"ممكن تكلمنا عن مشروع اشتغلت عليه في {job_title}؟"
        
        last_answer = history[-1].get("answer", "")
        skills = self.skill_extractor.extract(last_answer)
        
        for skill in skills:
            skill_key = skill.lower()
            if skill_key in TECHNICAL_TARGETS:
                return TECHNICAL_TARGETS[skill_key][0]
                
        return "إيه أكبر تحدي تقني واجهته في مشروعك الأخير؟"

    def _score_depth(self, text: str, skills: list[str]) -> float:
        markers = ["architecture", "scaling", "latency", "optimization", "built", "deployed"]
        hits = sum(1 for m in markers if m in text.lower())
        return min(100.0, (len(skills) * 10) + (hits * 15) + 20)

    def _score_clarity(self, text: str) -> float:
        words = text.split()
        if len(words) < 10: return 30.0
        if len(words) > 50: return 90.0
        return 70.0
