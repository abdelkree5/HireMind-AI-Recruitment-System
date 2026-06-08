"""
AI CV Builder Service — Phase 1: Candidate AI Ecosystem

Constructs optimized resumes from multiple input sources in three formats:
ATS-Friendly, Modern, and Recruiter-Optimized.
"""
from __future__ import annotations

import json
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CVBuilderService:
    """Builds optimized CVs from candidate data."""

    def generate_cv(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Generate an optimized CV.

        payload keys: candidate_text (str), format_type (str), target_job (dict, optional),
                      linkedin_data (dict, optional), github_data (dict, optional)
        """
        from ai_engine.reasoning import build_candidate_insight

        candidate_text = payload.get("candidate_text", "")
        format_type = payload.get("format_type", "ats_friendly")
        target_job = payload.get("target_job", {})
        candidate_id = payload.get("candidate_id", "")

        # Extract structured data
        insight = build_candidate_insight(candidate_text)
        linkedin = payload.get("linkedin_data", {})
        github = payload.get("github_data", {})

        # Merge sources
        all_skills = list(set(insight.skills + linkedin.get("skills", []) + github.get("languages", [])))
        experience_years = max(insight.years_of_experience, linkedin.get("years", 0))

        if format_type == "ats_friendly":
            cv = self._build_ats(insight, all_skills, experience_years, linkedin, github)
        elif format_type == "modern":
            cv = self._build_modern(insight, all_skills, experience_years, linkedin, github)
        elif format_type == "recruiter_optimized":
            cv = self._build_recruiter(insight, all_skills, experience_years, target_job)
        else:
            cv = self._build_ats(insight, all_skills, experience_years, linkedin, github)

        cv_id = str(uuid.uuid4())
        self._save_cv(cv_id, candidate_id, format_type, payload, cv)

        return {"cv_id": cv_id, "format": format_type, "content": cv}

    def _build_ats(self, insight, skills, years, linkedin, github) -> str:
        """ATS-friendly: keyword-dense, plain formatting."""
        sections = []
        sections.append(f"PROFESSIONAL SUMMARY")
        sections.append(f"{insight.level} professional with {years} years of experience.")
        sections.append(f"Primary domain: {insight.primary_domain}")
        sections.append("")
        sections.append("TECHNICAL SKILLS")
        sections.append(", ".join(skills[:20]))
        sections.append("")
        sections.append("EXPERIENCE")
        sections.append(f"- {years} years of professional experience")
        sections.append(f"- Domain expertise: {insight.primary_domain}")
        if insight.leadership_score > 0.3:
            sections.append(f"- Leadership experience demonstrated")
        sections.append("")
        if github.get("repos"):
            sections.append("PROJECTS")
            for repo in github["repos"][:3]:
                sections.append(f"- {repo}")
        return "\n".join(sections)

    def _build_modern(self, insight, skills, years, linkedin, github) -> str:
        """Modern: structured sections with metrics."""
        sections = []
        sections.append(f"## {insight.level} {insight.primary_domain.replace('_', ' ').title()} Professional")
        sections.append(f"")
        sections.append(f"**{years}+ years** | **{len(skills)} technical skills** | **{insight.primary_domain}**")
        sections.append("")
        sections.append("### Core Competencies")
        for i in range(0, min(12, len(skills)), 3):
            row = " | ".join(skills[i:i+3])
            sections.append(f"  {row}")
        sections.append("")
        sections.append("### Key Strengths")
        if insight.leadership_score > 0.3:
            sections.append(f"- Leadership: {round(insight.leadership_score * 100)}% score")
        sections.append(f"- Technical Depth: {round(insight.project_depth_score * 100)}% score")
        return "\n".join(sections)

    def _build_recruiter(self, insight, skills, years, target_job) -> str:
        """Recruiter-optimized: highlights matching skills against target job."""
        job_skills = set(s.lower() for s in target_job.get("required_skills", []))
        matched = [s for s in skills if s.lower() in job_skills]
        additional = [s for s in skills if s.lower() not in job_skills]

        sections = []
        sections.append(f"CANDIDATE PROFILE — Optimized for: {target_job.get('title', 'Target Role')}")
        sections.append("")
        sections.append(f"Match Highlights:")
        if matched:
            sections.append(f"  ✅ Matched Skills ({len(matched)}): {', '.join(matched)}")
        sections.append(f"  📊 Experience: {years} years")
        sections.append(f"  🎯 Domain: {insight.primary_domain}")
        sections.append("")
        sections.append("Additional Skills:")
        sections.append(f"  {', '.join(additional[:10])}")
        return "\n".join(sections)

    def _save_cv(self, cv_id, candidate_id, format_type, input_data, content):
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO generated_cvs (id, candidate_id, format_type, input_sources_json, output_content, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (cv_id, candidate_id, format_type, json.dumps({"keys": list(input_data.keys())}),
                     content, datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            logger.warning("Failed to save generated CV: %s", e)


cv_builder_service = CVBuilderService()
