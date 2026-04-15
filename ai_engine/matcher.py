from __future__ import annotations

from dataclasses import dataclass
import re

import numpy as np

from ai_engine.config import CONTEXT_WEIGHT, SEMANTIC_WEIGHT, SKILL_WEIGHT, TITLE_WEIGHT
from ai_engine.embeddings import EmbeddingEngine
from ai_engine.skills import SkillExtractor


@dataclass
class MatchReport:
    similarity: float
    skill_score: float
    title_score: float
    context_score: float
    match_percentage: float
    missing_skills: list[str]
    score_breakdown: dict[str, float]
    logs: list[str]


class RecruitmentMatcher:
    def __init__(self) -> None:
        self.embedding_engine = EmbeddingEngine()
        self.skill_extractor = SkillExtractor()

    def score(self, candidate_text: str, candidate_skills: list[str], job_title: str, job_description: str, required_skills: list[str]) -> MatchReport:
        job_text = f"{job_title}. {job_description}. {' '.join(required_skills)}"
        candidate_vector = self.embedding_engine.encode(candidate_text)
        job_vector = self.embedding_engine.encode(job_text)
        similarity = self._cosine_similarity(candidate_vector, job_vector)
        skill_score = self.skill_extractor.overlap_score(candidate_skills, required_skills)
        title_score = self._title_alignment(candidate_text, job_title)
        context_score = self._context_quality(candidate_text)
        missing_skills = self.skill_extractor.missing_skills(candidate_skills, required_skills)
        match_percentage = max(
            0.0,
            min(
                100.0,
                (
                    similarity * SEMANTIC_WEIGHT
                    + skill_score * SKILL_WEIGHT
                    + title_score * TITLE_WEIGHT
                    + context_score * CONTEXT_WEIGHT
                )
                * 100.0,
            ),
        )
        logs = [
            "أنا حسبت الـ embeddings عشان أفهم المعنى العام",
            "وبعدين حسبت تغطية المهارات عشان أزود الدقة",
            "وضفت title/context scores عشان أقلل الـ false positives",
        ]
        return MatchReport(
            similarity,
            skill_score,
            title_score,
            context_score,
            match_percentage,
            missing_skills,
            {
                "semantic": round(similarity, 4),
                "skill": round(skill_score, 4),
                "title": round(title_score, 4),
                "context": round(context_score, 4),
            },
            logs,
        )

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        if denominator == 0.0:
            return 0.0
        return float(np.dot(left, right) / denominator)

    def _title_alignment(self, resume_text: str, job_title: str) -> float:
        title_tokens = {token for token in re.findall(r"\w+", job_title.lower()) if len(token) > 2}
        if not title_tokens:
            return 0.0
        resume_tokens = set(re.findall(r"\w+", resume_text.lower()))
        return len(title_tokens & resume_tokens) / len(title_tokens)

    def _context_quality(self, resume_text: str) -> float:
        tokens = re.findall(r"\w+", resume_text.lower())
        if not tokens:
            return 0.0
        unique_ratio = len(set(tokens)) / len(tokens)
        length_factor = min(1.0, len(tokens) / 180.0)
        return max(0.0, min(1.0, 0.6 * unique_ratio + 0.4 * length_factor))
