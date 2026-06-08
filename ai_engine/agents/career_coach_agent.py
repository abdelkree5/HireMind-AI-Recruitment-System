"""
Career Coach Agent — Phase 1: Candidate AI Ecosystem

Responsibilities:
  - Skill gap analysis against target roles
  - Career roadmap generation using Skill Knowledge Graph
  - Personalized learning plan creation
  - Certification recommendations
  - Promotion readiness analysis
"""
from __future__ import annotations

import json
import uuid
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent


class CareerCoachAgent(BaseAgent):
    """Analyzes candidate profiles and produces career development plans."""

    def __init__(self) -> None:
        super().__init__(name="career_coach")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "skill_gap_analysis":
            result = self.skill_gap_analysis(payload)
        elif task == "career_roadmap":
            result = self.career_roadmap(payload)
        elif task == "learning_plan":
            result = self.learning_plan(payload)
        elif task == "certification_recommendations":
            result = self.certification_recommendations(payload)
        elif task == "promotion_readiness":
            result = self.promotion_readiness(payload)
        else:
            raise ValueError(f"CareerCoachAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def skill_gap_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Compare candidate skills against a target role.

        Required: candidate_skills (list), target_role (str)
        Optional: candidate_text (str)
        """
        from ai_engine.role_requirements import build_role_requirements

        candidate_skills = set(s.lower() for s in payload.get("candidate_skills", []))
        target_role = payload.get("target_role", "")

        requirements = build_role_requirements(target_role, "")
        required = set(s.lower() for s in requirements.required_skills)
        advanced = set(s.lower() for s in requirements.advanced_skills)

        matched = candidate_skills & required
        missing_required = required - candidate_skills
        missing_advanced = advanced - candidate_skills
        coverage = len(matched) / max(1, len(required))

        # Prioritize missing skills by criticality
        critical_gaps = sorted(missing_required)[:5]
        growth_gaps = sorted(missing_advanced)[:5]

        return {
            "target_role": target_role,
            "coverage_percentage": round(coverage * 100, 1),
            "matched_skills": sorted(matched),
            "critical_gaps": critical_gaps,
            "growth_opportunities": growth_gaps,
            "total_required": len(required),
            "total_matched": len(matched),
            "readiness_level": "Ready" if coverage >= 0.8 else "Almost Ready" if coverage >= 0.6 else "Developing" if coverage >= 0.4 else "Early Stage",
        }

    def career_roadmap(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a career roadmap using the Skill Knowledge Graph.

        Required: candidate_skills (list), target_role (str)
        """
        from ai_engine.skill_graph import skill_graph
        from ai_engine.role_requirements import build_role_requirements

        candidate_skills = payload.get("candidate_skills", [])
        target_role = payload.get("target_role", "")

        requirements = build_role_requirements(target_role, "")
        required_skills = [s.lower() for s in requirements.required_skills]
        candidate_set = set(s.lower() for s in candidate_skills)

        # Build roadmap steps using graph adjacency
        steps = []
        for skill in required_skills:
            if skill not in candidate_set:
                # Find bridge skills the candidate already has
                expanded = skill_graph.get_expanded_skills([skill])
                bridges = expanded & candidate_set
                step = {
                    "skill_to_learn": skill,
                    "bridge_skills": sorted(bridges)[:3],
                    "difficulty": "easy" if bridges else "medium",
                }
                steps.append(step)

        # Sort by difficulty (easy first)
        steps.sort(key=lambda s: 0 if s["difficulty"] == "easy" else 1)

        phases = []
        for i in range(0, len(steps), 3):
            phase_steps = steps[i:i+3]
            phases.append({
                "phase": f"Phase {i // 3 + 1}",
                "skills": [s["skill_to_learn"] for s in phase_steps],
                "estimated_weeks": len(phase_steps) * 4,
            })

        return {
            "target_role": target_role,
            "total_skills_to_acquire": len(steps),
            "phases": phases[:5],
            "steps": steps[:15],
        }

    def learning_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate a prioritized learning plan from gap analysis."""
        gap = self.skill_gap_analysis(payload)
        all_gaps = gap["critical_gaps"] + gap["growth_opportunities"]

        plan = []
        for i, skill in enumerate(all_gaps):
            plan.append({
                "priority": i + 1,
                "skill": skill,
                "category": "critical" if skill in gap["critical_gaps"] else "growth",
                "suggested_resources": [
                    f"Online course: {skill} fundamentals",
                    f"Hands-on project: Build with {skill}",
                    f"Documentation: Official {skill} docs",
                ],
                "estimated_hours": 40 if skill in gap["critical_gaps"] else 20,
            })

        return {
            "target_role": payload.get("target_role", ""),
            "readiness_level": gap["readiness_level"],
            "plan_items": plan,
            "total_estimated_hours": sum(p["estimated_hours"] for p in plan),
        }

    def certification_recommendations(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Map skill gaps to industry certifications."""
        CERT_MAP = {
            "aws": ["AWS Solutions Architect Associate", "AWS Developer Associate"],
            "azure": ["Azure Administrator Associate", "Azure Developer Associate"],
            "gcp": ["Google Cloud Associate Cloud Engineer"],
            "kubernetes": ["Certified Kubernetes Administrator (CKA)", "CKAD"],
            "docker": ["Docker Certified Associate"],
            "python": ["PCEP", "PCAP"],
            "terraform": ["HashiCorp Terraform Associate"],
            "cisco": ["CCNA", "CCNP"],
            "networking": ["CompTIA Network+", "CCNA"],
            "linux": ["LPIC-1", "CompTIA Linux+"],
            "machine learning": ["Google ML Engineer", "AWS ML Specialty"],
            "postgresql": ["PostgreSQL Certified Associate"],
            "ci/cd": ["Jenkins Certified Engineer"],
            "monitoring": ["Prometheus Certified Associate"],
        }

        gap = self.skill_gap_analysis(payload)
        all_gaps = gap["critical_gaps"] + gap["growth_opportunities"]

        recommendations = []
        seen = set()
        for skill in all_gaps:
            for cert in CERT_MAP.get(skill, []):
                if cert not in seen:
                    seen.add(cert)
                    recommendations.append({
                        "certification": cert,
                        "related_skill": skill,
                        "priority": "high" if skill in gap["critical_gaps"] else "medium",
                    })

        return {
            "target_role": payload.get("target_role", ""),
            "certifications": recommendations[:10],
        }

    def promotion_readiness(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate promotion readiness based on experience and skills."""
        from ai_engine.reasoning import build_candidate_insight

        cv_text = payload.get("candidate_text", "")
        target_seniority = payload.get("target_seniority", "Senior")

        if not cv_text:
            return {"error": "candidate_text is required"}

        insight = build_candidate_insight(cv_text)

        seniority_thresholds = {
            "Senior": {"min_years": 7, "min_leadership": 0.5, "min_depth": 0.5},
            "Mid": {"min_years": 3, "min_leadership": 0.2, "min_depth": 0.3},
            "Junior": {"min_years": 0, "min_leadership": 0.0, "min_depth": 0.0},
        }

        target = seniority_thresholds.get(target_seniority, seniority_thresholds["Senior"])

        scores = {
            "experience": min(1.0, insight.years_of_experience / max(1, target["min_years"])),
            "leadership": min(1.0, insight.leadership_score / max(0.01, target["min_leadership"])),
            "technical_depth": min(1.0, insight.project_depth_score / max(0.01, target["min_depth"])),
        }
        overall = sum(scores.values()) / len(scores)

        return {
            "current_level": insight.level,
            "target_seniority": target_seniority,
            "readiness_score": round(overall * 100, 1),
            "dimension_scores": {k: round(v * 100, 1) for k, v in scores.items()},
            "is_ready": overall >= 0.8,
            "gaps": [k for k, v in scores.items() if v < 0.7],
            "years_of_experience": insight.years_of_experience,
        }


career_coach_agent = CareerCoachAgent()
