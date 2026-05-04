from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import uuid

from backend.app.schemas import (
    CandidateProfile,
    CompanyDashboardJob,
    CompanyDashboardResponse,
    JobApplication,
    JobInput,
    PostedJobDetails,
    PostedJob,
)
from database.connection import get_connection
from database.init_db import init_recruitment_db
from ai_engine.parser import ResumeParser
from ai_engine.embeddings import EmbeddingEngine
from ai_engine.matcher import RecruitmentMatcher
from ai_engine.skills import SkillExtractor


class RecruitmentService:
    def __init__(self) -> None:
        init_recruitment_db()
        self.skill_extractor = SkillExtractor()
        self.parser = ResumeParser()
        self.matcher = RecruitmentMatcher()

    def _complete_job_payload(self, payload: JobInput) -> JobInput:
        # Simplified for now, can use ai_engine for smarter completion
        return payload

    def create_job(self, payload: JobInput) -> PostedJob:
        job_id = uuid.uuid4().hex
        job = PostedJob(
            id=job_id,
            title=payload.title,
            description=payload.description,
            required_skills=payload.required_skills,
            responsibilities=payload.responsibilities or [],
            preferred_skills=payload.preferred_skills or [],
            tools=payload.tools or [],
            experience_level=payload.experience_level or "mid",
            domain=payload.domain or "general",
            created_at=datetime.utcnow().isoformat(),
        )
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO posted_jobs (id, title, description, required_skills, responsibilities, 
                preferred_skills, tools, experience_level, domain, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job.id, job.title, job.description, json.dumps(job.required_skills), 
                 json.dumps(job.responsibilities), json.dumps(job.preferred_skills), 
                 json.dumps(job.tools), job.experience_level, job.domain, job.created_at),
            )
        return job

    def list_jobs(self) -> list[PostedJob]:
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM posted_jobs ORDER BY created_at DESC").fetchall()
        return [self._row_to_job(row) for row in rows]

    def apply_to_job(self, job_id: str, file_bytes: bytes, filename: str, candidate: CandidateProfile) -> JobApplication:
        job = self.get_job(job_id)
        resume_text = self.parser.parse(file_bytes, filename)
        extracted_skills = self.skill_extractor.extract(resume_text)
        
        report = self.matcher.score(resume_text, extracted_skills, job.title, job.description, job.required_skills)
        
        application = JobApplication(
            id=uuid.uuid4().hex,
            job_id=job_id,
            candidate_name=candidate.name,
            candidate_headline=candidate.headline,
            candidate_skills=extracted_skills,
            match_score=report.match_percentage,
            missing_skills=report.missing_skills,
            score_breakdown=report.score_breakdown,
            feedback=report.recommendation,
            created_at=datetime.utcnow().isoformat(),
        )
        
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO job_applications (id, job_id, candidate_name, candidate_headline, 
                candidate_skills, match_score, missing_skills, score_breakdown, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (application.id, application.job_id, application.candidate_name, application.candidate_headline,
                 json.dumps(application.candidate_skills), application.match_score, 
                 json.dumps(application.missing_skills), json.dumps(application.score_breakdown), 
                 application.feedback, application.created_at),
            )
        return application

    def _row_to_job(self, row) -> PostedJob:
        return PostedJob(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            required_skills=json.loads(row["required_skills"]),
            responsibilities=json.loads(row["responsibilities"]) if row["responsibilities"] else [],
            preferred_skills=json.loads(row["preferred_skills"]) if row["preferred_skills"] else [],
            tools=json.loads(row["tools"]) if row["tools"] else [],
            experience_level=row["experience_level"],
            domain=row["domain"],
            created_at=row["created_at"],
        )

    def get_job(self, job_id: str) -> PostedJob:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM posted_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row: raise ValueError("Job not found")
        return self._row_to_job(row)
