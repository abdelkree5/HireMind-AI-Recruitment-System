"""
Market Intelligence Service — Phase 5

Analyzes hiring trends, skill demand, and technology shifts from internal data.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from collections import Counter
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MarketIntelligenceService:
    """Aggregates and analyzes hiring data for market insights."""

    def get_skill_trends(self) -> dict[str, Any]:
        """Aggregate required_skills across all posted jobs to identify trends."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT required_skills FROM posted_jobs ORDER BY created_at DESC"
                ).fetchall()

            skill_counter: Counter = Counter()
            for row in rows:
                raw = row["required_skills"]
                skills = json.loads(raw) if isinstance(raw, str) else raw
                for s in skills:
                    skill_counter[s.lower()] += 1

            top_skills = skill_counter.most_common(20)
            return {
                "total_jobs_analyzed": len(rows),
                "top_skills": [{"skill": s, "demand_count": c} for s, c in top_skills],
                "unique_skills": len(skill_counter),
            }
        except Exception as e:
            logger.warning("Failed to compute skill trends: %s", e)
            return {"top_skills": [], "error": str(e)}

    def get_hiring_trends(self) -> dict[str, Any]:
        """Analyze hiring volume over time."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                jobs = conn.execute(
                    "SELECT created_at FROM posted_jobs ORDER BY created_at"
                ).fetchall()
                apps = conn.execute(
                    "SELECT created_at FROM job_applications ORDER BY created_at"
                ).fetchall()
                hires = conn.execute(
                    "SELECT created_at FROM recruiter_feedback WHERE is_hired = 1"
                ).fetchall()

            return {
                "total_jobs_posted": len(jobs),
                "total_applications": len(apps),
                "total_hires": len(hires),
                "application_to_hire_ratio": round(len(hires) / max(1, len(apps)) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_technology_trends(self) -> dict[str, Any]:
        """Identify emerging skill clusters using the Skill Knowledge Graph."""
        from ai_engine.skill_graph import skill_graph

        domain_clusters = {}
        for node in skill_graph.graph.nodes():
            neighbors = list(skill_graph.graph.neighbors(node))
            if len(neighbors) >= 3:
                domain_clusters[node] = {
                    "connected_skills": neighbors,
                    "cluster_size": len(neighbors),
                }

        sorted_clusters = sorted(domain_clusters.items(), key=lambda x: x[1]["cluster_size"], reverse=True)

        return {
            "technology_clusters": [
                {"technology": name, **data}
                for name, data in sorted_clusters[:10]
            ],
        }

    def get_domain_distribution(self) -> dict[str, Any]:
        """Analyze distribution of jobs across domains."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT domain, COUNT(*) as cnt FROM posted_jobs GROUP BY domain ORDER BY cnt DESC"
                ).fetchall()
            return {"domains": [{"domain": r["domain"] or "unspecified", "count": r["cnt"]} for r in rows]}
        except Exception:
            return {"domains": []}


market_intelligence_service = MarketIntelligenceService()
