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
from backend.app.services.recruitment_db import get_connection, init_recruitment_db
from backend.app.services.cv_parser import extract_candidate_profile_text
from backend.app.services.document_parser import extract_text_from_resume
from backend.app.services.embedding_engine import embed_text_semantic
from backend.app.services.feedback_service import build_feedback
from backend.app.services.job_vectorizer import build_job_text
from backend.app.services.matching_service import matching_service
from backend.app.services.similarity_engine import (
    apply_smart_adjustments,
    cosine_similarity,
    map_similarity_to_score,
    to_match_level,
)
from backend.app.services.skill_extractor import SkillExtractor


class RecruitmentService:
    def __init__(self) -> None:
        init_recruitment_db()
        self.skill_extractor = SkillExtractor()

    def _complete_job_payload(self, payload: JobInput) -> JobInput:
        title = payload.title.lower()
        skills = [skill.lower() for skill in payload.required_skills]

        defaults = {
            "backend": {
                "responsibilities": [
                    "Design and maintain backend services",
                    "Build and document APIs",
                    "Improve performance and reliability",
                    "Collaborate across product and engineering",
                ],
                "preferred_skills": ["docker", "kubernetes", "redis", "message queues"],
                "tools": ["fastapi", "postgresql", "docker", "github actions"],
                "experience_level": "mid",
                "domain": "backend",
            },
            "devops": {
                "responsibilities": [
                    "Automate infrastructure provisioning and deployments",
                    "Build CI/CD workflows",
                    "Monitor services and improve reliability",
                    "Support incident response and postmortems",
                ],
                "preferred_skills": ["ansible", "helm", "linux", "observability"],
                "tools": ["terraform", "kubernetes", "grafana", "prometheus", "github actions"],
                "experience_level": "mid",
                "domain": "devops",
            },
            "data": {
                "responsibilities": [
                    "Build ETL and ELT pipelines",
                    "Model warehouse data and analytics layers",
                    "Ensure data quality and governance",
                    "Partner with analysts and ML teams",
                ],
                "preferred_skills": ["dbt", "kafka", "snowflake", "spark"],
                "tools": ["airflow", "spark", "dbt", "postgresql"],
                "experience_level": "mid",
                "domain": "data",
            },
            "frontend": {
                "responsibilities": [
                    "Build responsive UI features",
                    "Integrate APIs and state management",
                    "Improve accessibility and performance",
                    "Write unit and e2e tests",
                ],
                "preferred_skills": ["next.js", "storybook", "playwright", "performance profiling"],
                "tools": ["react", "vite", "typescript", "eslint", "jest"],
                "experience_level": "mid",
                "domain": "frontend",
            },
            "mobile": {
                "responsibilities": [
                    "Ship mobile features and releases",
                    "Integrate APIs and offline storage",
                    "Improve app stability and performance",
                    "Support analytics and crash monitoring",
                ],
                "preferred_skills": ["flutter", "dart", "firebase", "state management"],
                "tools": ["flutter", "dart", "firebase", "fastlane"],
                "experience_level": "mid",
                "domain": "mobile",
            },
            "qa": {
                "responsibilities": [
                    "Create automated test coverage",
                    "Integrate tests into CI/CD",
                    "Track flaky tests and quality metrics",
                    "Work closely with developers to improve testability",
                ],
                "preferred_skills": ["playwright", "postman", "performance testing", "security testing"],
                "tools": ["pytest", "selenium", "postman", "allure", "github actions"],
                "experience_level": "mid",
                "domain": "qa",
            },
            "ml": {
                "responsibilities": [
                    "Train, evaluate, and deploy ML models",
                    "Build inference services",
                    "Monitor drift and model quality",
                    "Collaborate with data engineering and product",
                ],
                "preferred_skills": ["pytorch", "tensorflow", "mlflow", "feature store"],
                "tools": ["python", "scikit-learn", "mlflow", "docker", "grafana"],
                "experience_level": "mid",
                "domain": "ai_ml",
            },
            "security": {
                "responsibilities": [
                    "Investigate alerts and suspicious activity",
                    "Run vulnerability assessments",
                    "Improve security controls and hardening",
                    "Coordinate incident response",
                ],
                "preferred_skills": ["splunk", "threat hunting", "cloud security", "python"],
                "tools": ["splunk", "wireshark", "nmap", "edr", "firewall"],
                "experience_level": "mid",
                "domain": "security",
            },
            "product": {
                "responsibilities": [
                    "Define roadmap and priorities",
                    "Gather customer insights",
                    "Write PRDs and success metrics",
                    "Coordinate cross-functional delivery",
                ],
                "preferred_skills": ["sql", "experimentation", "ux research", "saas"],
                "tools": ["jira", "confluence", "mixpanel", "figma"],
                "experience_level": "senior",
                "domain": "product",
            },
        }

        template_key = next((key for key in defaults if key in title or key in skills), "backend")
        profile = defaults[template_key]

        responsibilities = payload.responsibilities or profile["responsibilities"]
        preferred_skills = payload.preferred_skills or profile["preferred_skills"]
        tools = payload.tools or profile["tools"]
        experience_level = payload.experience_level or profile["experience_level"]
        domain = payload.domain or profile["domain"]

        return JobInput(
            title=payload.title,
            description=payload.description,
            required_skills=payload.required_skills,
            responsibilities=responsibilities,
            preferred_skills=preferred_skills,
            tools=tools,
            experience_level=experience_level,
            domain=domain,
        )

    def create_job(self, payload: JobInput) -> PostedJob:
        payload = self._complete_job_payload(payload)
        job_id = uuid.uuid4().hex
        job = PostedJob(
            id=job_id,
            title=payload.title,
            description=payload.description,
            required_skills=payload.required_skills,
            responsibilities=payload.responsibilities,
            preferred_skills=payload.preferred_skills,
            tools=payload.tools,
            experience_level=payload.experience_level,
            domain=payload.domain,
            created_at=datetime.utcnow().isoformat(),
        )
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO posted_jobs (
                    id,
                    title,
                    description,
                    required_skills,
                    responsibilities,
                    preferred_skills,
                    tools,
                    experience_level,
                    domain,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.title,
                    job.description,
                    json.dumps(job.required_skills),
                    json.dumps(job.responsibilities),
                    json.dumps(job.preferred_skills),
                    json.dumps(job.tools),
                    job.experience_level,
                    job.domain,
                    job.created_at,
                ),
            )
        return job

    def list_jobs(self) -> list[PostedJob]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    title,
                    description,
                    required_skills,
                    responsibilities,
                    preferred_skills,
                    tools,
                    experience_level,
                    domain,
                    created_at
                FROM posted_jobs
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_job(self, job_id: str) -> PostedJob:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    title,
                    description,
                    required_skills,
                    responsibilities,
                    preferred_skills,
                    tools,
                    experience_level,
                    domain,
                    created_at
                FROM posted_jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()

        if not row:
            raise ValueError("Job not found")
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
                    domain = ?
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
                    job_id,
                ),
            )
        return self.get_job(job_id)

    def delete_job(self, job_id: str) -> None:
        self.get_job(job_id)
        with get_connection() as connection:
            connection.execute("DELETE FROM posted_jobs WHERE id = ?", (job_id,))

    def apply_to_job(
        self,
        job_id: str,
        file_bytes: bytes,
        filename: str,
        candidate: CandidateProfile,
    ) -> JobApplication:
        job = self.get_job(job_id)

        resume_text = extract_text_from_resume(file_bytes, filename)
        if not resume_text.strip():
            raise ValueError("Uploaded CV is empty or unreadable.")

        extracted_skills = self.skill_extractor.extract(resume_text)
        combined_skills = sorted(set([*candidate.skills, *extracted_skills]))
        candidate_text = f"{candidate.headline}. {candidate.summary}. {resume_text}. {' '.join(combined_skills)}"

        match = matching_service.match_against_job(
            JobInput(
                title=job.title,
                description=job.description,
                required_skills=job.required_skills,
            ),
            candidate_text,
            combined_skills,
        )

        application = JobApplication(
            id=uuid.uuid4().hex,
            job_id=job_id,
            candidate_name=candidate.name,
            candidate_headline=candidate.headline,
            candidate_skills=combined_skills,
            match_score=round(match.match_percentage, 2),
            missing_skills=match.missing_skills,
            score_breakdown=match.score_breakdown,
            feedback=build_feedback(match.missing_skills),
            created_at=datetime.utcnow().isoformat(),
        )

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO job_applications (
                    id,
                    job_id,
                    candidate_name,
                    candidate_headline,
                    candidate_skills,
                    match_score,
                    missing_skills,
                    score_breakdown,
                    feedback,
                    created_at
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
        return application

    def apply_to_job_cv_only(
        self,
        job_id: str,
        file_bytes: bytes,
        filename: str,
        confirmed_skills: list[str] | None = None,
    ) -> dict:
        job = self.get_job(job_id)

        # Use the main matching_service pipeline for consistent, high-quality scoring.
        job_input = JobInput(
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
        )

        if confirmed_skills:
            # If user manually confirmed skills, we re-run matching with these skills as the candidate source
            resume_text = extract_text_from_resume(file_bytes, filename)
            match_result = matching_service.match_against_job(job_input, resume_text, confirmed_skills)
        else:
            match_result = matching_service.analyze_resume(file_bytes, filename, job_input)

        # Use the match_percentage from the proper skill-based matcher.
        final_score = match_result.match_percentage
        match_level = match_result.match_level

        # Build reason from matched/missing skills.
        reason_parts = [
            f"Matched skills: {', '.join(match_result.matched_skills) if match_result.matched_skills else 'none'}",
            f"Missing skills: {', '.join(match_result.missing_skills) if match_result.missing_skills else 'none'}",
        ]
        
        # Handle both MatchResult dataclass and CandidateMatchResponse pydantic
        res_reason = getattr(match_result, "reason", "")
        if res_reason:
            reason_parts.append(res_reason)
        reason = " | ".join(reason_parts)

        candidate_name = Path(filename).stem or "Candidate"
        
        # Feedback logic
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
                    id,
                    job_id,
                    candidate_name,
                    candidate_headline,
                    candidate_skills,
                    match_score,
                    missing_skills,
                    score_breakdown,
                    feedback,
                    created_at
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

        return {
            "score": round(match_result.match_percentage, 2),
            "match_level": match_result.match_level,
            "matched_skills": match_result.matched_skills,
            "missing_skills": match_result.missing_skills,
            "all_extracted_skills": match_result.logs, # matching_service.analyze_resume logs extracted skills
            "job_required_skills": job.required_skills,
            "candidate_level": match_result.evidence.get("candidate_level", "unknown"),
            "candidate_domain": match_result.evidence.get("candidate_domain", "general"),
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
        templates = [
            JobInput(
                title="Senior Backend Engineer",
                description="Build scalable API services for product and data platforms.",
                responsibilities=[
                    "Design and maintain microservices",
                    "Optimize query performance and caching",
                    "Drive architecture reviews and code quality",
                    "Collaborate with frontend and ML teams",
                ],
                required_skills=["python", "fastapi", "postgresql", "redis", "docker", "rest api"],
                preferred_skills=["kubernetes", "gcp", "message queues", "grpc"],
                tools=["fastapi", "postgresql", "redis", "docker", "github actions"],
                experience_level="senior",
                domain="backend",
            ),
            JobInput(
                title="ML Engineer",
                description="Productionize ML models for ranking, forecasting, and personalization.",
                responsibilities=[
                    "Train and evaluate ML models",
                    "Build model inference services",
                    "Monitor model drift and quality",
                    "Work with data engineering on pipelines",
                ],
                required_skills=["python", "machine learning", "scikit-learn", "pandas", "sql", "docker"],
                preferred_skills=["pytorch", "feature store", "airflow", "mlflow"],
                tools=["python", "scikit-learn", "mlflow", "docker", "grafana"],
                experience_level="mid",
                domain="ai_ml",
            ),
            JobInput(
                title="DevOps Engineer",
                description="Own CI/CD and cloud infrastructure reliability at scale.",
                responsibilities=[
                    "Automate infrastructure provisioning",
                    "Maintain CI/CD pipelines",
                    "Improve observability and alerting",
                    "Support incident response and recovery",
                ],
                required_skills=["aws", "kubernetes", "terraform", "ci/cd", "monitoring", "linux"],
                preferred_skills=["ansible", "helm", "python", "cost optimization"],
                tools=["terraform", "kubernetes", "grafana", "prometheus", "github actions"],
                experience_level="mid",
                domain="devops",
            ),
            JobInput(
                title="Data Engineer",
                description="Build robust batch and streaming pipelines for analytics and ML.",
                responsibilities=[
                    "Design ELT pipelines",
                    "Model warehouse data",
                    "Implement data quality checks",
                    "Collaborate with BI and ML teams",
                ],
                required_skills=["python", "sql", "airflow", "spark", "data modeling", "postgresql"],
                preferred_skills=["dbt", "kafka", "snowflake", "terraform"],
                tools=["airflow", "spark", "dbt", "postgresql", "great expectations"],
                experience_level="mid",
                domain="data",
            ),
            JobInput(
                title="Frontend Engineer",
                description="Develop responsive product experiences with strong UX performance.",
                responsibilities=[
                    "Build reusable UI components",
                    "Integrate APIs and state management",
                    "Improve accessibility and performance",
                    "Write tests and maintain design consistency",
                ],
                required_skills=["javascript", "typescript", "react", "html", "css", "rest api"],
                preferred_skills=["next.js", "playwright", "storybook", "performance profiling"],
                tools=["react", "vite", "typescript", "eslint", "jest"],
                experience_level="mid",
                domain="frontend",
            ),
            JobInput(
                title="Mobile Engineer (Flutter)",
                description="Build cross-platform mobile apps with robust offline-first behavior.",
                responsibilities=[
                    "Implement app features in Flutter",
                    "Integrate APIs and local persistence",
                    "Handle app release lifecycle",
                    "Improve performance and crash-free sessions",
                ],
                required_skills=["flutter", "dart", "rest api", "firebase", "state management"],
                preferred_skills=["clean architecture", "ci/cd", "analytics"],
                tools=["flutter", "dart", "firebase", "fastlane", "sentry"],
                experience_level="mid",
                domain="mobile",
            ),
            JobInput(
                title="Site Reliability Engineer",
                description="Ensure reliability, scalability, and incident excellence for platform services.",
                responsibilities=[
                    "Define SLIs/SLOs and error budgets",
                    "Automate operational runbooks",
                    "Lead incident response improvements",
                    "Continuously tune monitoring strategy",
                ],
                required_skills=["linux", "kubernetes", "monitoring", "incident response", "aws", "scripting"],
                preferred_skills=["go", "chaos testing", "capacity planning"],
                tools=["prometheus", "grafana", "kubernetes", "pagerduty", "aws"],
                experience_level="senior",
                domain="devops",
            ),
            JobInput(
                title="QA Automation Engineer",
                description="Design and maintain automated quality gates across web and API surfaces.",
                responsibilities=[
                    "Create end-to-end and API test suites",
                    "Integrate tests into CI pipelines",
                    "Track flaky tests and quality metrics",
                    "Collaborate with engineers on testability",
                ],
                required_skills=["python", "selenium", "api testing", "ci/cd", "test automation"],
                preferred_skills=["playwright", "performance testing", "security testing"],
                tools=["pytest", "selenium", "postman", "github actions", "allure"],
                experience_level="mid",
                domain="qa",
            ),
            JobInput(
                title="Product Manager",
                description="Drive product strategy and delivery for B2B SaaS features.",
                responsibilities=[
                    "Define roadmap and feature priorities",
                    "Gather customer insights and requirements",
                    "Write PRDs and success metrics",
                    "Coordinate cross-functional execution",
                ],
                required_skills=["product strategy", "roadmapping", "analytics", "stakeholder management"],
                preferred_skills=["sql", "experimentation", "saas", "ux research"],
                tools=["jira", "confluence", "mixpanel", "figma"],
                experience_level="senior",
                domain="product",
            ),
            JobInput(
                title="Cybersecurity Analyst",
                description="Protect systems through proactive monitoring, detection, and response.",
                responsibilities=[
                    "Monitor SIEM alerts and investigate threats",
                    "Perform vulnerability assessments",
                    "Implement security hardening controls",
                    "Coordinate incident handling and reporting",
                ],
                required_skills=["network security", "siem", "incident response", "firewall", "linux"],
                preferred_skills=["splunk", "threat hunting", "python", "cloud security"],
                tools=["splunk", "wireshark", "nmap", "edr", "firewall"],
                experience_level="mid",
                domain="security",
            ),
        ]

        existing_jobs = {job.title.lower().strip(): job for job in self.list_jobs()}
        created: list[PostedJob] = []
        updated: list[PostedJob] = []
        for template in templates:
            key = template.title.lower().strip()
            if key in existing_jobs:
                target = existing_jobs[key]
                updated.append(self.update_job(target.id, template))
                continue
            created_job = self.create_job(template)
            created.append(created_job)
            existing_jobs[key] = created_job

        return {"created": created, "updated": updated}

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

        return [self._row_to_application(row) for row in rows]

    def _row_to_job(self, row) -> PostedJob:
        return PostedJob(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            required_skills=json.loads(row["required_skills"]),
            responsibilities=json.loads(row["responsibilities"]) if "responsibilities" in row.keys() else [],
            preferred_skills=json.loads(row["preferred_skills"]) if "preferred_skills" in row.keys() else [],
            tools=json.loads(row["tools"]) if "tools" in row.keys() else [],
            experience_level=row["experience_level"] if "experience_level" in row.keys() else "",
            domain=row["domain"] if "domain" in row.keys() else "",
            created_at=row["created_at"],
        )

    def _infer_candidate_level(self, cv_text: str) -> str:
        lowered = cv_text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]):
            return "senior"
        if any(token in lowered for token in ["junior", "intern", "entry"]):
            return "junior"
        return "mid"

    def _infer_candidate_domain(self, skills: list[str], cv_text: str) -> str:
        skill_set = {skill.lower() for skill in skills}
        lowered = cv_text.lower()
        if any(token in skill_set for token in ["kubernetes", "terraform", "aws", "monitoring"]):
            return "devops"
        if any(token in skill_set for token in ["python", "fastapi", "django", "rest api"]):
            return "backend"
        if any(token in lowered for token in ["telecom", "network", "routing", "switching"]):
            return "telecom"
        return "general"

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
