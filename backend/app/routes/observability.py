"""
Observability API Routes — Phase 4

Endpoints:
  GET /api/observability/traces                       — All agent execution traces
  GET /api/observability/metrics                      — Full platform metrics
  GET /api/observability/candidate/{app_id}/why-ranked  — Why candidate was ranked
  GET /api/observability/candidate/{app_id}/why-rejected — Why candidate was rejected
  GET /api/observability/retrieval/quality            — Retrieval quality dashboard
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from backend.app.services.auth_service import require_current_user, require_role

router = APIRouter(dependencies=[Depends(require_current_user)])


@router.get("/traces", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_all_traces(
    workflow_id: str | None = None,
    agent_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List all agent execution traces with optional filters."""
    try:
        from ai_engine.observability.tracer import agent_tracer
        return agent_tracer.get_traces(workflow_id=workflow_id, agent_name=agent_name, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/metrics", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_platform_metrics() -> dict[str, Any]:
    """Return all platform-level observability metrics."""
    try:
        from ai_engine.observability.metrics import get_full_platform_metrics
        return get_full_platform_metrics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/candidate/{application_id}/why-ranked", dependencies=[Depends(require_role("recruiter", "admin"))])
def explain_candidate_ranking(application_id: str) -> dict[str, Any]:
    """Explainability: why was this candidate ranked at their position?"""
    try:
        from ai_engine.observability.tracer import agent_tracer
        result = agent_tracer.get_why_ranked(application_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/candidate/{application_id}/why-rejected", dependencies=[Depends(require_role("recruiter", "admin"))])
def explain_candidate_rejection(application_id: str) -> dict[str, Any]:
    """Explainability: why was this candidate rejected?"""
    try:
        from ai_engine.observability.tracer import agent_tracer
        result = agent_tracer.get_why_rejected(application_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/retrieval/quality", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_retrieval_quality(job_id: str | None = None) -> dict[str, Any]:
    """
    Compute retrieval quality metrics from feedback data.
    Uses recruiter decisions as ground truth to compute P@K, NDCG@K, MRR.
    """
    try:
        from database.connection import get_connection
        from ai_engine.observability.metrics import (
            precision_at_k, ndcg_at_k, mean_reciprocal_rank, recall_at_k
        )

        with get_connection() as conn:
            query = """
                SELECT rf.application_id, rf.is_accepted, ja.match_score, ja.job_id
                FROM recruiter_feedback rf
                JOIN job_applications ja ON rf.application_id = ja.id
            """
            params: list = []
            if job_id:
                query += " WHERE rf.job_id = ?"
                params.append(job_id)
            query += " ORDER BY ja.match_score DESC"
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return {"status": "no_data", "message": "No feedback data available for quality metrics."}

        retrieved_ids = [r["application_id"] for r in rows]
        relevant_ids = {r["application_id"] for r in rows if r["is_accepted"]}

        return {
            "total_retrieved": len(retrieved_ids),
            "total_relevant": len(relevant_ids),
            "precision_at_5": precision_at_k(relevant_ids, retrieved_ids, 5),
            "precision_at_10": precision_at_k(relevant_ids, retrieved_ids, 10),
            "recall_at_10": recall_at_k(relevant_ids, retrieved_ids, 10),
            "ndcg_at_5": ndcg_at_k(relevant_ids, retrieved_ids, 5),
            "ndcg_at_10": ndcg_at_k(relevant_ids, retrieved_ids, 10),
            "mrr": mean_reciprocal_rank(relevant_ids, retrieved_ids),
            "job_id_filter": job_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/agent-messages/{workflow_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_workflow_messages(workflow_id: str) -> dict[str, Any]:
    """Return the full inter-agent message log for a workflow."""
    try:
        from ai_engine.agents.message_bus import agent_message_bus
        messages = agent_message_bus.get_conversation(workflow_id)
        return {"workflow_id": workflow_id, "message_count": len(messages), "messages": messages}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
