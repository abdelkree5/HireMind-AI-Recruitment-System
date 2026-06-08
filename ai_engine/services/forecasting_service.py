"""
Skill Demand Forecasting — Phase 5

Predicts emerging skills, future hiring demand, and industry shifts
from historical job posting data.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from collections import Counter

logger = logging.getLogger(__name__)


class ForecastingService:
    """Trend prediction engine for skill demand and hiring velocity."""

    def forecast_emerging_skills(self) -> dict[str, Any]:
        """Identify skills with accelerating growth in job postings."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT required_skills, created_at FROM posted_jobs ORDER BY created_at"
                ).fetchall()

            if len(rows) < 2:
                return {"emerging_skills": [], "note": "Insufficient data for forecasting."}

            midpoint = len(rows) // 2
            early = rows[:midpoint]
            recent = rows[midpoint:]

            early_counter: Counter = Counter()
            recent_counter: Counter = Counter()

            for row in early:
                skills = json.loads(row["required_skills"]) if isinstance(row["required_skills"], str) else row["required_skills"]
                for s in skills:
                    early_counter[s.lower()] += 1

            for row in recent:
                skills = json.loads(row["required_skills"]) if isinstance(row["required_skills"], str) else row["required_skills"]
                for s in skills:
                    recent_counter[s.lower()] += 1

            # Find skills with growth
            emerging = []
            for skill, recent_count in recent_counter.items():
                early_count = early_counter.get(skill, 0)
                if recent_count > early_count:
                    growth = ((recent_count - early_count) / max(1, early_count)) * 100
                    emerging.append({
                        "skill": skill,
                        "early_period_count": early_count,
                        "recent_period_count": recent_count,
                        "growth_percentage": round(growth, 1),
                        "trend": "accelerating" if growth > 100 else "growing" if growth > 0 else "stable",
                    })

            emerging.sort(key=lambda x: x["growth_percentage"], reverse=True)
            return {"emerging_skills": emerging[:15], "jobs_analyzed": len(rows)}
        except Exception as e:
            return {"emerging_skills": [], "error": str(e)}

    def forecast_hiring_demand(self) -> dict[str, Any]:
        """Predict hiring velocity based on historical patterns."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                jobs = conn.execute("SELECT COUNT(*) as cnt FROM posted_jobs").fetchone()
                apps = conn.execute("SELECT COUNT(*) as cnt FROM job_applications").fetchone()
                hires = conn.execute("SELECT COUNT(*) as cnt FROM recruiter_feedback WHERE is_hired = 1").fetchone()

            total_jobs = jobs["cnt"] if jobs else 0
            total_apps = apps["cnt"] if apps else 0
            total_hires = hires["cnt"] if hires else 0

            avg_apps_per_job = total_apps / max(1, total_jobs)
            hire_rate = total_hires / max(1, total_apps)

            return {
                "current_open_positions": total_jobs,
                "total_applications": total_apps,
                "total_hires": total_hires,
                "avg_applications_per_job": round(avg_apps_per_job, 1),
                "hire_rate_percentage": round(hire_rate * 100, 1),
                "forecast": {
                    "expected_applications_next_period": round(avg_apps_per_job * total_jobs * 1.1, 0),
                    "expected_hires_next_period": round(total_hires * 1.1, 0),
                    "confidence": "low" if total_jobs < 10 else "medium" if total_jobs < 50 else "high",
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def detect_industry_shifts(self) -> dict[str, Any]:
        """Detect domain-level migration patterns."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT domain, COUNT(*) as cnt FROM posted_jobs GROUP BY domain ORDER BY cnt DESC"
                ).fetchall()

            domains = [{"domain": r["domain"] or "unspecified", "job_count": r["cnt"]} for r in rows]
            total = sum(d["job_count"] for d in domains)

            for d in domains:
                d["market_share_pct"] = round(d["job_count"] / max(1, total) * 100, 1)

            return {"industry_distribution": domains, "total_positions": total}
        except Exception:
            return {"industry_distribution": []}


forecasting_service = ForecastingService()
