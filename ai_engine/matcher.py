from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import ceil
import numpy as np

from ai_engine.embeddings import EmbeddingEngine
from ai_engine.skills import SkillExtractor


@dataclass
class MatchReport:
    similarity: float
    skill_score: float
    title_score: float
    context_score: float
    match_percentage: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    recommendation: str = ""

@dataclass
class RoleMatchResult:
    role_name: str
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    confidence: float = 0.0
    composite: float = 0.0
    match_level: str = "Low"
    priority_score: float = 0.0
    reason: str = ""

class RecruitmentMatcher:
    def __init__(self) -> None:
        self.embedding_engine = EmbeddingEngine()
        self.skill_extractor = SkillExtractor()

    def score(
        self,
        candidate_text: str,
        candidate_skills: list[str],
        job_title: str,
        job_description: str,
        required_skills: list[str],
        candidate_level: str | None = None,
        job_level: str | None = None,
    ) -> MatchReport:
        # Semantic & Skill Scoring logic
        job_text = f"{job_title}. {job_description}. {' '.join(required_skills)}"
        candidate_vector = self.embedding_engine.encode(candidate_text)
        job_vector = self.embedding_engine.encode(job_text)
        similarity = self._cosine_similarity(candidate_vector, job_vector)

        normalized_job = self._normalize_skills(required_skills)
        normalized_candidate = self._normalize_skills(candidate_skills)
        
        matched_skills = [s for s in normalized_job if s in normalized_candidate]
        missing_skills = [s for s in normalized_job if s not in matched_skills]
        
        skill_score = self._calculate_weighted_skill_score(normalized_job, normalized_candidate)
        title_score = self._title_alignment(candidate_text, job_title)
        context_score = self._context_quality(candidate_text)

        match_percentage = (similarity * 0.4 + skill_score * 0.4 + title_score * 0.1 + context_score * 0.1) * 100.0
        
        penalties = []
        if candidate_level and job_level and candidate_level != job_level:
            match_percentage -= 5.0
            penalties.append("Seniority mismatch (-5%)")

        match_percentage = max(0.0, min(100.0, match_percentage))

        return MatchReport(
            similarity=similarity,
            skill_score=skill_score,
            title_score=title_score,
            context_score=context_score,
            match_percentage=match_percentage,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            penalties=penalties,
            score_breakdown={
                "semantic": round(similarity, 4),
                "skill": round(skill_score, 4),
                "title": round(title_score, 4),
                "context": round(context_score, 4),
            },
            recommendation=self._build_recommendation(match_percentage / 100.0),
            logs=["تم التحليل باستخدام الـ Embeddings والمطابقة المباشرة."]
        )

    def compare_role_match(
        self,
        candidate_skills: list[str],
        required_skills: list[str],
        normalized_text: str,
        **kwargs
    ) -> RoleMatchResult:
        """Detailed role comparison for automated recommendations."""
        candidate_set = {s.lower() for s in candidate_skills}
        matched = [s for s in required_skills if s.lower() in candidate_set or s.lower() in normalized_text.lower()]
        missing = [s for s in required_skills if s not in matched]
        
        confidence = len(matched) / len(required_skills) if required_skills else 0.0
        
        return RoleMatchResult(
            role_name=kwargs.get("role_name", "Unknown"),
            required_skills=required_skills,
            matched_skills=matched,
            missing_skills=missing,
            confidence=confidence,
            composite=confidence, # Simplified for now
            match_level="High" if confidence > 0.7 else "Medium" if confidence > 0.4 else "Low",
            reason=f"تم مطابقة {len(matched)} مهارة."
        )

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        denom = float(np.linalg.norm(left) * np.linalg.norm(right))
        return float(np.dot(left, right) / denom) if denom != 0 else 0.0

    def _normalize_skills(self, skills: list[str]) -> list[str]:
        return sorted(list(set(s.lower().strip() for s in skills if s)))

    def _calculate_weighted_skill_score(self, required: list[str], candidate: list[str]) -> float:
        if not required: return 0.0
        total = len(required)
        core_count = max(1, ceil(total * 0.6))
        core_skills = required[:core_count]
        other_skills = required[core_count:]
        
        def hit_ratio(bucket):
            if not bucket: return 0.0
            return sum(1 for s in bucket if s in candidate) / len(bucket)
            
        return (hit_ratio(core_skills) * 0.7) + (hit_ratio(other_skills) * 0.3)

    def _title_alignment(self, text: str, title: str) -> float:
        tokens = {t for t in re.findall(r"\w+", title.lower()) if len(t) > 2}
        if not tokens: return 0.0
        resume_tokens = set(re.findall(r"\w+", text.lower()))
        return len(tokens & resume_tokens) / len(tokens)

    def _context_quality(self, text: str) -> float:
        tokens = re.findall(r"\w+", text.lower())
        if not tokens: return 0.0
        return min(1.0, len(tokens) / 200.0)

    def _build_recommendation(self, score: float) -> str:
        if score > 0.8: return "Strong Match"
        if score >= 0.5: return "Good Fit"
        if score >= 0.3: return "Partial Match"
        return "Weak Match"
