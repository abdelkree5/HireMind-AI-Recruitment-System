"""
Agent Tracer — Observability Layer

Persists agent execution traces to the `agent_traces` table.
Optionally forwards to Langfuse or OpenTelemetry if configured via .env.

Usage:
    trace_ctx = AgentTraceContext(...)
    # ... execute agent logic ...
    trace_ctx.complete(status="completed", output_summary="...")
    agent_tracer.record(trace_ctx)
"""
from __future__ import annotations

import json
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AgentTracer:
    """
    Internal SQLite-backed tracer with optional external adapter support.

    External adapters (Langfuse, OpenTelemetry) are loaded lazily
    and skipped gracefully if not installed/configured.
    """

    def __init__(self) -> None:
        self._langfuse = None
        self._otel_tracer = None
        self._initialized = False

    def _init_external(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # --- Optional Langfuse ---
        langfuse_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        if langfuse_key:
            try:
                from langfuse import Langfuse
                self._langfuse = Langfuse(
                    public_key=langfuse_key,
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                )
                logger.info("[AgentTracer] Langfuse adapter enabled.")
            except ImportError:
                logger.debug("[AgentTracer] langfuse not installed, skipping.")

        # --- Optional OpenTelemetry ---
        otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if otel_endpoint:
            try:
                from opentelemetry import trace as otel_trace
                self._otel_tracer = otel_trace.get_tracer("hiremind.agents")
                logger.info("[AgentTracer] OpenTelemetry adapter enabled.")
            except ImportError:
                logger.debug("[AgentTracer] opentelemetry-sdk not installed, skipping.")

    def record(self, trace_ctx: Any) -> None:
        """
        Persist a completed AgentTraceContext to the database and
        forward to any configured external adapters.
        """
        self._init_external()
        self._persist_to_db(trace_ctx)
        self._forward_langfuse(trace_ctx)
        self._forward_otel(trace_ctx)

    def _persist_to_db(self, trace_ctx: Any) -> None:
        """Store the trace record in agent_traces table."""
        try:
            from database.connection import get_connection
            trace_id = getattr(trace_ctx, "trace_id", uuid.uuid4().hex)
            workflow_id = getattr(trace_ctx, "workflow_id", "")
            agent_name = getattr(trace_ctx, "agent_name", "unknown")
            task_type = getattr(trace_ctx, "task_type", "")
            input_summary = getattr(trace_ctx, "input_summary", "")
            output_summary = getattr(trace_ctx, "output_summary", "")
            status = getattr(trace_ctx, "status", "unknown")
            latency_ms = getattr(trace_ctx, "latency_ms", 0.0)
            created_at = datetime.now(timezone.utc).isoformat()

            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_traces
                        (id, workflow_id, trace_id, agent_name, task_type,
                         input_summary, output_summary, status, latency_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        workflow_id,
                        trace_id,
                        agent_name,
                        task_type,
                        input_summary[:500],
                        output_summary[:500],
                        status,
                        latency_ms,
                        created_at,
                    ),
                )
        except Exception as exc:
            logger.debug(f"[AgentTracer] DB persist failed: {exc}")

    def _forward_langfuse(self, trace_ctx: Any) -> None:
        if not self._langfuse:
            return
        try:
            self._langfuse.trace(
                name=f"{trace_ctx.agent_name}.{trace_ctx.task_type}",
                input=trace_ctx.input_summary,
                output=trace_ctx.output_summary,
                metadata={
                    "workflow_id": trace_ctx.workflow_id,
                    "trace_id": trace_ctx.trace_id,
                    "latency_ms": trace_ctx.latency_ms,
                    "status": trace_ctx.status,
                },
            )
        except Exception as exc:
            logger.debug(f"[AgentTracer] Langfuse forward failed: {exc}")

    def _forward_otel(self, trace_ctx: Any) -> None:
        if not self._otel_tracer:
            return
        try:
            with self._otel_tracer.start_as_current_span(
                f"{trace_ctx.agent_name}.{trace_ctx.task_type}"
            ) as span:
                span.set_attribute("workflow_id", trace_ctx.workflow_id)
                span.set_attribute("latency_ms", trace_ctx.latency_ms)
                span.set_attribute("status", trace_ctx.status)
        except Exception as exc:
            logger.debug(f"[AgentTracer] OTEL forward failed: {exc}")

    def get_traces(
        self,
        workflow_id: str | None = None,
        agent_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query agent traces from the DB."""
        try:
            from database.connection import get_connection
            query = """
                SELECT id, workflow_id, trace_id, agent_name, task_type,
                       input_summary, output_summary, status, latency_ms, created_at
                FROM agent_traces
                WHERE 1=1
            """
            params: list[Any] = []
            if workflow_id:
                query += " AND workflow_id = ?"
                params.append(workflow_id)
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            with get_connection() as conn:
                rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_why_ranked(self, application_id: str) -> dict[str, Any]:
        """Build an explainability report for why a candidate was ranked."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                app = conn.execute(
                    "SELECT * FROM job_applications WHERE id = ?",
                    (application_id,),
                ).fetchone()
            if not app:
                return {"error": "Application not found"}

            import json as _json
            breakdown = {}
            try:
                breakdown = _json.loads(app["score_breakdown"])
            except Exception:
                pass

            return {
                "application_id": application_id,
                "candidate_name": app["candidate_name"],
                "match_score": float(app["match_score"]),
                "score_breakdown": breakdown,
                "matched_skills": _json.loads(app["candidate_skills"] or "[]"),
                "missing_skills": _json.loads(app["missing_skills"] or "[]"),
                "feedback": app["feedback"],
                "ranking_reason": (
                    f"Candidate scored {app['match_score']:.1f}% based on: "
                    f"dense similarity ({breakdown.get('dense_similarity', 0):.2f}), "
                    f"skill coverage ({breakdown.get('skill_score', 0):.2f}), "
                    f"experience alignment ({breakdown.get('experience_alignment', 0):.2f})."
                ),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def get_why_rejected(self, application_id: str) -> dict[str, Any]:
        """Build an explainability report for why a candidate was rejected."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                fb = conn.execute(
                    "SELECT * FROM recruiter_feedback WHERE application_id = ?",
                    (application_id,),
                ).fetchone()
                app = conn.execute(
                    "SELECT match_score, missing_skills, feedback FROM job_applications WHERE id = ?",
                    (application_id,),
                ).fetchone()

            import json as _json

            reasons = []
            if fb:
                reasons.append(f"Recruiter decision: {fb['recruiter_decision']}")
                if fb["rejection_reason"]:
                    reasons.append(f"Rejection reason: {fb['rejection_reason']}")
                if fb["recruiter_notes"]:
                    reasons.append(f"Notes: {fb['recruiter_notes']}")
            if app:
                missing = _json.loads(app["missing_skills"] or "[]")
                if missing:
                    reasons.append(f"Missing skills: {', '.join(missing[:5])}")
                if float(app["match_score"]) < 50.0:
                    reasons.append(f"Low AI match score: {app['match_score']:.1f}%")

            return {
                "application_id": application_id,
                "recruiter_decision": fb["recruiter_decision"] if fb else "N/A",
                "rejection_reasons": reasons,
                "ai_match_score": float(app["match_score"]) if app else None,
                "missing_skills": _json.loads(app["missing_skills"] or "[]") if app else [],
            }
        except Exception as exc:
            return {"error": str(exc)}


# Singleton
agent_tracer = AgentTracer()
