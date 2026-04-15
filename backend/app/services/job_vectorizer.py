from __future__ import annotations

from backend.app.schemas import PostedJob


def build_job_text(job: PostedJob) -> str:
    return " ".join(
        [
            f"title: {job.title}",
            f"description: {job.description}",
            "responsibilities: " + ", ".join(job.responsibilities or []),
            "required_skills: " + ", ".join(job.required_skills or []),
            "preferred_skills: " + ", ".join(job.preferred_skills or []),
            "tools: " + ", ".join(job.tools or []),
            f"experience_level: {job.experience_level}",
            f"domain: {job.domain}",
        ]
    ).strip().lower()
