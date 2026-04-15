from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.schemas import CandidateMatchResponse, JobInput
from backend.app.services.document_parser import extract_text_from_resume
from backend.app.services.job_matcher import extract_candidate_skills, match_job_to_candidate
from backend.app.services.skill_extractor import SkillExtractor


@dataclass
class MatchResult:
    score: float
    similarity: float
    skill_score: float
    title_score: float
    match_percentage: float
    match_level: str
    missing_skills: list[str]
    matched_skills: list[str]
    reason: str
    recommendation: str
    score_breakdown: dict[str, float]
    logs: list[str]


class MatchingService:
    def __init__(self) -> None:
        self.skill_extractor = SkillExtractor()

    def analyze_resume(self, file_bytes: bytes, filename: str, job: JobInput) -> CandidateMatchResponse:
        logs = ["Reading CV...", "Extracting skills..."]
        text = extract_text_from_resume(file_bytes, filename)
        if not text.strip():
            raise ValueError("CV file is empty or unreadable.")

        resume_skills = self.skill_extractor.extract(text)
        logs.append(f"Detected skills in CV: {', '.join(resume_skills) if resume_skills else 'none'}")
        result = self._score(text, resume_skills, job)
        logs.extend(result.logs)
        return CandidateMatchResponse(
            job_title=job.title,
            match_percentage=round(result.match_percentage, 2),
            similarity=round(result.similarity, 4),
            skill_score=round(result.skill_score, 4),
            title_score=round(result.title_score, 4),
            missing_skills=result.missing_skills,
            matched_skills=result.matched_skills,
            feedback=self._build_feedback(result.missing_skills),
            recommendation=result.recommendation,
            reason=result.reason,
            confidence_score=round(result.match_percentage, 2),
            match_level=result.match_level,
            score_breakdown=result.score_breakdown,
            logs=logs,
        )

    def match_against_job(self, job: JobInput, candidate_text: str, candidate_skills: list[str]) -> MatchResult:
        return self._score(candidate_text, candidate_skills, job)

    def _score(self, text: str, resume_skills: list[str], job: JobInput) -> MatchResult:
        logs = ["Preparing direct skill comparison..."]
        job_skills = self._normalize_skills(job.required_skills)
        candidate_skill_source = extract_candidate_skills(text, resume_skills)
        result = match_job_to_candidate(
            job_skills=job_skills,
            candidate_skills=candidate_skill_source,
            candidate_level=self._infer_seniority(text),
            job_level=self._infer_seniority(f"{job.title} {job.description}"),
            candidate_domain=self._infer_domain(text),
            job_domain=self._infer_domain(f"{job.title} {job.description}"),
        )

        skill_score = result.score
        similarity = result.score
        title_score = self._title_alignment(text, job.title)
        match_percentage = result.score * 100.0

        if result.missing_skills:
            logs.append(f"Missing key skills: {', '.join(result.missing_skills)}")
        else:
            logs.append("CV covers required skills well.")

        logs.append("Final scoring: direct skill intersection with small contextual adjustments")
        return MatchResult(
            score=result.score,
            similarity=similarity,
            skill_score=skill_score,
            title_score=title_score,
            match_percentage=match_percentage,
            match_level=result.match_level,
            missing_skills=result.missing_skills,
            matched_skills=result.matched_skills,
            reason=result.reason,
            recommendation=result.recommendation,
            score_breakdown={
                "semantic": round(similarity, 4),
                "skill": round(skill_score, 4),
                "title": round(title_score, 4),
            },
            logs=logs,
        )

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        if denominator == 0.0:
            return 0.0
        return float(np.dot(left, right) / denominator)

    def _build_feedback(self, missing_skills: list[str]) -> str:
        if not missing_skills:
            return "Candidate is a strong fit with no major skill gaps."
        return f"Recommended focus areas: {', '.join(missing_skills)}"

    def _infer_seniority(self, text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]):
            return "senior"
        if any(token in lowered for token in ["junior", "entry", "intern"]):
            return "junior"
        return "unknown"

    def _infer_domain(self, text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["devops", "kubernetes", "terraform", "aws", "monitoring", "ci/cd"]):
            return "devops"
        if any(token in lowered for token in ["telecom", "network", "routing", "switching"]):
            return "telecom"
        if any(token in lowered for token in ["backend", "microservices"]):
            return "backend"
        return "general"

    def _normalize_skills(self, skills: list[str]) -> list[str]:
        mapping = {
            "python3": "python",
            "fast api": "fastapi",
            "postgres": "postgresql",
        }
        normalized: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            value = skill.strip().lower()
            value = mapping.get(value, value)
            if value and value not in seen:
                seen.add(value)
                normalized.append(value)
        return normalized

    def _title_alignment(self, resume_text: str, job_title: str) -> float:
        title_tokens = {token for token in re.findall(r"\w+", job_title.lower()) if len(token) > 2}
        if not title_tokens:
            return 0.0
        resume_tokens = set(re.findall(r"\w+", resume_text.lower()))
        return len(title_tokens & resume_tokens) / len(title_tokens)

matching_service = MatchingService()
