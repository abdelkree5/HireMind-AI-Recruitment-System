"""
Job Recommendation Engine — Phase 5

Candidate-facing job recommendations using reverse matching,
career path suggestions, and skill-to-learn prioritization.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RecommendationService:
    """Generates personalized job and career recommendations for candidates."""

    def recommend_jobs(self, candidate_skills: list[str], limit: int = 10) -> dict[str, Any]:
        """Reverse-match candidate against all open jobs."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, title, required_skills, domain FROM posted_jobs ORDER BY created_at DESC"
                ).fetchall()

            candidate_set = set(s.lower() for s in candidate_skills)
            scored = []

            for row in rows:
                raw = row["required_skills"]
                required = json.loads(raw) if isinstance(raw, str) else raw
                required_set = set(s.lower() for s in required)
                matched = candidate_set & required_set
                score = len(matched) / max(1, len(required_set)) * 100

                scored.append({
                    "job_id": row["id"],
                    "title": row["title"],
                    "domain": row["domain"] or "",
                    "match_score": round(score, 1),
                    "matched_skills": sorted(matched),
                    "missing_skills": sorted(required_set - candidate_set),
                })

            scored.sort(key=lambda x: x["match_score"], reverse=True)
            return {"recommendations": scored[:limit], "total_jobs_evaluated": len(rows)}
        except Exception as e:
            return {"recommendations": [], "error": str(e)}

    def suggest_career_paths(self, candidate_skills: list[str]) -> dict[str, Any]:
        """Use Skill Knowledge Graph to suggest adjacent career paths."""
        from ai_engine.skill_graph import skill_graph

        expanded = skill_graph.get_expanded_skills(candidate_skills, max_depth=2)
        new_skills = expanded - set(s.lower() for s in candidate_skills)

        # Group new skills by adjacency
        from ai_engine.memory.memory_store import memory_store
        domains = memory_store.get_domain_relations()

        path_suggestions = []
        for domain, domain_skills in domains.items():
            overlap = set(s.lower() for s in domain_skills) & set(s.lower() for s in candidate_skills)
            if len(overlap) >= 2:
                missing = set(s.lower() for s in domain_skills) - set(s.lower() for s in candidate_skills)
                path_suggestions.append({
                    "domain": domain,
                    "readiness": round(len(overlap) / max(1, len(domain_skills)) * 100, 1),
                    "skills_you_have": sorted(overlap),
                    "skills_to_learn": sorted(missing)[:5],
                })

        path_suggestions.sort(key=lambda x: x["readiness"], reverse=True)
        return {"career_paths": path_suggestions[:5]}

    def prioritize_skills_to_learn(self, candidate_skills: list[str]) -> dict[str, Any]:
        """Identify highest-value skills to learn based on market demand."""
        from ai_engine.services.market_intelligence import market_intelligence_service

        trends = market_intelligence_service.get_skill_trends()
        top_market = {s["skill"]: s["demand_count"] for s in trends.get("top_skills", [])}

        candidate_set = set(s.lower() for s in candidate_skills)
        opportunities = []

        for skill, demand in top_market.items():
            if skill not in candidate_set:
                opportunities.append({
                    "skill": skill,
                    "market_demand": demand,
                    "priority": "high" if demand >= 5 else "medium" if demand >= 2 else "low",
                })

        opportunities.sort(key=lambda x: x["market_demand"], reverse=True)
        return {"skills_to_learn": opportunities[:10]}


recommendation_service = RecommendationService()
