"""
Analytics Service — Phase 6: Analytics & Decision Intelligence

Unified analytics for recruiter, AI performance, and executive dashboards.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Aggregates metrics across all HireMind system layers."""

    def recruiter_dashboard(self, job_id: str | None = None) -> dict[str, Any]:
        """Recruiter-facing metrics: time-to-hire, funnel, success rate."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                if job_id:
                    apps = conn.execute(
                        "SELECT COUNT(*) as cnt FROM job_applications WHERE job_id = ?", (job_id,)
                    ).fetchone()
                    interviews = conn.execute(
                        "SELECT COUNT(*) as cnt FROM interview_sessions WHERE job_id = ?", (job_id,)
                    ).fetchone()
                    completed_interviews = conn.execute(
                        "SELECT COUNT(*) as cnt FROM interview_sessions WHERE job_id = ? AND status = 'completed'", (job_id,)
                    ).fetchone()
                    feedback = conn.execute(
                        "SELECT COUNT(*) as total, SUM(is_accepted) as accepted, SUM(is_hired) as hired FROM recruiter_feedback WHERE job_id = ?",
                        (job_id,)
                    ).fetchone()
                else:
                    apps = conn.execute("SELECT COUNT(*) as cnt FROM job_applications").fetchone()
                    interviews = conn.execute("SELECT COUNT(*) as cnt FROM interview_sessions").fetchone()
                    completed_interviews = conn.execute(
                        "SELECT COUNT(*) as cnt FROM interview_sessions WHERE status = 'completed'"
                    ).fetchone()
                    feedback = conn.execute(
                        "SELECT COUNT(*) as total, SUM(is_accepted) as accepted, SUM(is_hired) as hired FROM recruiter_feedback"
                    ).fetchone()

            total_apps = apps["cnt"] if apps else 0
            total_interviews = interviews["cnt"] if interviews else 0
            completed = completed_interviews["cnt"] if completed_interviews else 0
            fb_total = feedback["total"] if feedback else 0
            accepted = feedback["accepted"] or 0 if feedback else 0
            hired = feedback["hired"] or 0 if feedback else 0

            return {
                "funnel": {
                    "applications": total_apps,
                    "interviews_scheduled": total_interviews,
                    "interviews_completed": completed,
                    "offers_extended": int(accepted),
                    "hires": int(hired),
                },
                "interview_success_rate": round(completed / max(1, total_interviews) * 100, 1),
                "acceptance_rate": round(int(accepted) / max(1, fb_total) * 100, 1),
                "hire_rate": round(int(hired) / max(1, total_apps) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}

    def ai_performance_dashboard(self) -> dict[str, Any]:
        """AI system performance: agent accuracy, latency, tool success."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                traces = conn.execute("""
                    SELECT agent_name,
                           COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                           AVG(latency_ms) as avg_latency,
                           MAX(latency_ms) as max_latency
                    FROM agent_traces
                    GROUP BY agent_name
                """).fetchall()

            agents = []
            total_tasks = 0
            total_completed = 0
            for t in traces:
                total = t["total"]
                comp = t["completed"]
                total_tasks += total
                total_completed += comp
                agents.append({
                    "agent": t["agent_name"],
                    "total_tasks": total,
                    "success_rate": round(comp / max(1, total) * 100, 1),
                    "failure_rate": round(t["failed"] / max(1, total) * 100, 1),
                    "avg_latency_ms": round(t["avg_latency"] or 0, 1),
                    "max_latency_ms": round(t["max_latency"] or 0, 1),
                })

            return {
                "agent_metrics": agents,
                "system_success_rate": round(total_completed / max(1, total_tasks) * 100, 1),
                "total_agent_tasks": total_tasks,
            }
        except Exception as e:
            return {"error": str(e)}

    def executive_dashboard(self) -> dict[str, Any]:
        """Executive summary: hiring velocity, pipeline health, ROI."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                jobs = conn.execute("SELECT COUNT(*) as cnt FROM posted_jobs").fetchone()
                apps = conn.execute("SELECT COUNT(*) as cnt FROM job_applications").fetchone()
                hires = conn.execute("SELECT COUNT(*) as cnt FROM recruiter_feedback WHERE is_hired = 1").fetchone()
                active_interviews = conn.execute(
                    "SELECT COUNT(*) as cnt FROM interview_sessions WHERE status != 'completed'"
                ).fetchone()

            total_jobs = jobs["cnt"] if jobs else 0
            total_apps = apps["cnt"] if apps else 0
            total_hires = hires["cnt"] if hires else 0
            active = active_interviews["cnt"] if active_interviews else 0

            return {
                "hiring_velocity": {
                    "total_positions": total_jobs,
                    "total_hires": total_hires,
                    "fill_rate": round(total_hires / max(1, total_jobs) * 100, 1),
                },
                "talent_pipeline": {
                    "total_candidates": total_apps,
                    "active_interviews": active,
                    "pipeline_health": "healthy" if total_apps > total_jobs else "needs_sourcing",
                },
                "efficiency": {
                    "candidates_per_hire": round(total_apps / max(1, total_hires), 1),
                    "automation_level": "high",
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def candidate_funnel(self, job_id: str) -> dict[str, Any]:
        """Detailed candidate funnel for a specific job."""
        return self.recruiter_dashboard(job_id)


analytics_service = AnalyticsService()
