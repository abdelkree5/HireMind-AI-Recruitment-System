from __future__ import annotations

from backend.app.schemas import CandidateMatchResponse, JobInput
from ai_engine.parser import ResumeParser
from ai_engine.skills import SkillExtractor
from ai_engine.matcher import RecruitmentMatcher


class MatchingService:
    def __init__(self) -> None:
        self.parser = ResumeParser()
        self.skill_extractor = SkillExtractor()
        self.matcher = RecruitmentMatcher()

    def analyze_resume(self, file_bytes: bytes, filename: str, job: JobInput) -> CandidateMatchResponse:
        logs = ["بدء تحليل السيرة الذاتية...", "استخراج المهارات..."]
        
        # 1. Parse Document
        text = self.parser.parse(file_bytes, filename)
        if not text.strip():
            raise ValueError("ملف السيرة الذاتية فارغ أو غير قابل للقراءة.")

        # 2. Extract Skills
        resume_skills = self.skill_extractor.extract(text)
        logs.append(f"المهارات المكتشفة: {', '.join(resume_skills) if resume_skills else 'لا يوجد'}")
        
        # 3. Match against Job
        report = self.matcher.score(
            candidate_text=text,
            candidate_skills=resume_skills,
            job_title=job.title,
            job_description=job.description,
            required_skills=job.required_skills,
            candidate_level=self._infer_seniority(text),
            job_level=self._infer_seniority(f"{job.title} {job.description}")
        )
        
        logs.extend(report.logs)
        
        return CandidateMatchResponse(
            job_title=job.title,
            match_percentage=round(report.match_percentage, 2),
            similarity=round(report.similarity, 4),
            skill_score=round(report.skill_score, 4),
            title_score=round(report.title_score, 4),
            missing_skills=report.missing_skills,
            matched_skills=report.matched_skills,
            feedback=self._build_feedback(report.missing_skills),
            recommendation=report.recommendation,
            reason=f"تم مطابقة {len(report.matched_skills)} من أصل {len(report.matched_skills) + len(report.missing_skills)} مهارات مطلوبة.",
            confidence_score=round(report.match_percentage, 2),
            match_level=report.recommendation,
            score_breakdown=report.score_breakdown,
            logs=logs,
        )

    def _build_feedback(self, missing_skills: list[str]) -> str:
        if not missing_skills:
            return "المرشح مناسب جداً للوظيفة."
        return f"نوصي بالتركيز على المهارات التالية: {', '.join(missing_skills)}"

    def _infer_seniority(self, text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]):
            return "senior"
        if any(token in lowered for token in ["junior", "entry", "intern"]):
            return "junior"
        return "unknown"

matching_service = MatchingService()
