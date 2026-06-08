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
    HiringRules,
)
from database.connection import get_connection
from database.init_db import init_recruitment_db
from ai_engine.parser import ResumeParser
from ai_engine.embeddings import EmbeddingEngine
from ai_engine.matcher import RecruitmentMatcher
from ai_engine.skills import SkillExtractor
from backend.app.services.matching_service import matching_service


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
            hiring_rules=payload.hiring_rules,
            created_at=datetime.utcnow().isoformat(),
        )
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO posted_jobs (id, title, description, required_skills, responsibilities, 
                preferred_skills, tools, experience_level, domain, hiring_rules, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job.id, job.title, job.description, json.dumps(job.required_skills), 
                 json.dumps(job.responsibilities), json.dumps(job.preferred_skills), 
                 json.dumps(job.tools), job.experience_level, job.domain,
                 json.dumps(job.hiring_rules.model_dump()) if job.hiring_rules else "{}", job.created_at),
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
        
        report = self.matcher.score(
            resume_text,
            extracted_skills,
            job.title,
            job.description,
            job.required_skills,
            hiring_rules=job.hiring_rules
        )
        
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
        hiring_rules = None
        if "hiring_rules" in row.keys() and row["hiring_rules"]:
            try:
                hiring_rules = HiringRules(**json.loads(row["hiring_rules"]))
            except Exception:
                pass
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
            hiring_rules=hiring_rules,
            created_at=row["created_at"],
        )

    def get_job(self, job_id: str) -> PostedJob:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM posted_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row: raise ValueError("Job not found")
        return self._row_to_job(row)

    def get_job_details(self, job_id: str) -> PostedJobDetails:
        job = self.get_job(job_id)
        with get_connection() as connection:
            count_row = connection.execute(
                "SELECT COUNT(*) AS count FROM job_applications WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return PostedJobDetails(job=job, applicants_count=int(count_row["count"]))

    def update_job(self, job_id: str, payload: JobInput) -> PostedJob:
        payload = self._complete_job_payload(payload)
        self.get_job(job_id)
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE posted_jobs
                SET
                    title = ?,
                    description = ?,
                    required_skills = ?,
                    responsibilities = ?,
                    preferred_skills = ?,
                    tools = ?,
                    experience_level = ?,
                    domain = ?,
                    hiring_rules = ?
                WHERE id = ?
                """,
                (
                    payload.title,
                    payload.description,
                    json.dumps(payload.required_skills),
                    json.dumps(payload.responsibilities),
                    json.dumps(payload.preferred_skills),
                    json.dumps(payload.tools),
                    payload.experience_level,
                    payload.domain,
                    json.dumps(payload.hiring_rules.model_dump()) if payload.hiring_rules else "{}",
                    job_id,
                ),
            )
        return self.get_job(job_id)


    def delete_job(self, job_id: str) -> None:
        self.get_job(job_id)
        with get_connection() as connection:
            connection.execute("DELETE FROM posted_jobs WHERE id = ?", (job_id,))

    def apply_to_job_cv_only(
        self,
        job_id: str,
        file_bytes: bytes,
        filename: str,
        confirmed_skills: list[str] | None = None,
    ) -> dict:
        job = self.get_job(job_id)

        job_input = JobInput(
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
        )

        if confirmed_skills:
            resume_text = self.parser.parse(file_bytes, filename)
            match_result = matching_service.match_against_job(job_input, resume_text, confirmed_skills)
        else:
            match_result = matching_service.analyze_resume(file_bytes, filename, job_input)

        final_score = match_result.match_percentage
        match_level = match_result.match_level

        reason_parts = [
            f"Matched skills: {', '.join(match_result.matched_skills) if match_result.matched_skills else 'none'}",
            f"Missing skills: {', '.join(match_result.missing_skills) if match_result.missing_skills else 'none'}",
        ]
        
        res_reason = getattr(match_result, "reason", "")
        if res_reason:
            reason_parts.append(res_reason)
        reason = " | ".join(reason_parts)

        candidate_name = Path(filename).stem or "Candidate"
        
        feedback = ""
        if hasattr(match_result, "feedback") and match_result.feedback:
            feedback = match_result.feedback
        elif hasattr(match_result, "recommendation") and match_result.recommendation:
            feedback = match_result.recommendation
        else:
            feedback = reason

        application = JobApplication(
            id=uuid.uuid4().hex,
            job_id=job_id,
            candidate_name=candidate_name,
            candidate_headline="AI Parsed Candidate",
            candidate_skills=sorted(s.lower() for s in (match_result.matched_skills or [])),
            match_score=round(final_score, 2),
            missing_skills=match_result.missing_skills,
            score_breakdown=match_result.score_breakdown,
            feedback=feedback,
            created_at=datetime.utcnow().isoformat(),
        )

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO job_applications (
                    id, job_id, candidate_name, candidate_headline,
                    candidate_skills, match_score, missing_skills, score_breakdown, feedback, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application.id,
                    application.job_id,
                    application.candidate_name,
                    application.candidate_headline,
                    json.dumps(application.candidate_skills),
                    application.match_score,
                    json.dumps(application.missing_skills),
                    json.dumps(application.score_breakdown),
                    application.feedback,
                    application.created_at,
                ),
            )

        return {
            "score": round(final_score, 2),
            "match_score": round(final_score, 2),
            "match_level": match_level,
            "matched_keywords": match_result.matched_skills,
            "missing_keywords": match_result.missing_skills,
            "reason": reason,
            "application_id": application.id,
        }

    def pre_match_report(self, job_id: str, file_bytes: bytes, filename: str) -> dict:
        job = self.get_job(job_id)
        job_input = JobInput(
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
        )
        match_result = matching_service.analyze_resume(file_bytes, filename, job_input)

        evidence = getattr(match_result, "evidence", {})
        return {
            "score": round(match_result.match_percentage, 2),
            "match_level": match_result.match_level,
            "matched_skills": match_result.matched_skills,
            "missing_skills": match_result.missing_skills,
            "all_extracted_skills": getattr(match_result, "logs", []),
            "job_required_skills": job.required_skills,
            "candidate_level": evidence.get("candidate_level", "unknown"),
            "candidate_domain": evidence.get("candidate_domain", "general"),
        }

    def company_dashboard(
        self,
        sort_by: str = "score",
        order: str = "desc",
        min_score: float | None = None,
        since_date: str | None = None,
    ) -> CompanyDashboardResponse:
        jobs = self.list_jobs()
        dashboard_jobs: list[CompanyDashboardJob] = []
        total_applications = 0

        for job in jobs:
            applicants = self._list_job_applications(
                job.id,
                sort_by=sort_by,
                order=order,
                min_score=min_score,
                since_date=since_date,
            )
            total_applications += len(applicants)
            dashboard_jobs.append(CompanyDashboardJob(job=job, applicants=applicants))

        return CompanyDashboardResponse(
            total_jobs=len(jobs),
            total_applications=total_applications,
            jobs=dashboard_jobs,
        )

    def seed_realistic_jobs(self) -> dict[str, list[PostedJob]]:
        from backend.app.services.recruitment_service_old import RecruitmentService as RS_Old
        rs_old = RS_Old()
        outcome = rs_old.seed_realistic_jobs()
        # Seeded jobs are written to the database. We reload and return them.
        return outcome

    def _list_job_applications(
        self,
        job_id: str,
        sort_by: str,
        order: str,
        min_score: float | None,
        since_date: str | None,
    ) -> list[JobApplication]:
        valid_sort_by = "created_at" if sort_by == "date" else "match_score"
        valid_order = "ASC" if order.lower() == "asc" else "DESC"

        query = (
            "SELECT id, job_id, candidate_name, candidate_headline, candidate_skills, "
            "match_score, missing_skills, score_breakdown, feedback, created_at "
            "FROM job_applications WHERE job_id = ?"
        )
        params: list[object] = [job_id]

        if min_score is not None:
            query += " AND match_score >= ?"
            params.append(min_score)

        if since_date:
            query += " AND created_at >= ?"
            params.append(since_date)

        query += f" ORDER BY {valid_sort_by} {valid_order}"

        with get_connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        applications = [self._row_to_application(row) for row in rows]

        # Apply LTR re-ranking if sorting by score
        if sort_by == "score":
            try:
                from ai_engine.training.ltr_pipeline import ltr_pipeline
                job = self.get_job(job_id)
                job_dict = job.model_dump()
                applications = ltr_pipeline.rerank_candidates(job_dict, applications)
            except Exception:
                pass

        return applications


    def _row_to_application(self, row) -> JobApplication:
        interview_status = None
        interview_score = None
        with get_connection() as connection:
            latest_interview = connection.execute(
                """
                SELECT status, final_score
                FROM interview_sessions
                WHERE application_id = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (row["id"],),
            ).fetchone()

        if latest_interview:
            interview_status = latest_interview["status"]
            score_value = latest_interview["final_score"]
            interview_score = float(score_value) if score_value is not None else None

        return JobApplication(
            id=row["id"],
            job_id=row["job_id"],
            candidate_name=row["candidate_name"],
            candidate_headline=row["candidate_headline"],
            candidate_skills=json.loads(row["candidate_skills"]),
            match_score=float(row["match_score"]),
            missing_skills=json.loads(row["missing_skills"]),
            score_breakdown=json.loads(row["score_breakdown"]),
            feedback=row["feedback"],
            interview_status=interview_status,
            interview_score=interview_score,
            created_at=row["created_at"],
        )

recruitment_service = RecruitmentService()

