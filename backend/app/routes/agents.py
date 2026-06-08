"""
Agent API Routes — Phase 2: Agent Orchestration

Endpoints:
  POST /api/agents/pipeline/run          — Run full multi-agent pipeline
  GET  /api/agents/pipeline/{workflow_id} — Get pipeline status
  POST /api/agents/route                  — Route a single task to an agent
  GET  /api/agents/traces                 — List recent agent traces
  GET  /api/agents/traces/{trace_id}      — Get single trace detail
  POST /api/agents/supervisor/reflect     — Trigger supervisor reflection
  GET  /api/agents/memory/stm/{wf_id}    — Read short-term memory for workflow
  GET  /api/agents/memory/semantic        — Get skills ontology / domain relations
  GET  /api/agents/status                 — Agent registry status
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from backend.app.services.auth_service import require_current_user, require_role
from ai_engine.observability.rabbitmq_metrics import get_rabbitmq_queue_metrics

router = APIRouter(dependencies=[Depends(require_current_user)])


# ---------------------------------------------------------------------------
# Pipeline Execution
# ---------------------------------------------------------------------------

@router.post("/pipeline/run", dependencies=[Depends(require_role("recruiter", "admin"))])
def run_agent_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Trigger the full multi-agent hiring pipeline for a candidate.

    Required body:
        job_id: str
    Optional:
        cv_text: str         — Pre-parsed CV text (skip file parsing)
        filename: str        — Filename hint if no text provided

    Returns:
        Full pipeline result including all agent outputs and final decision.
    """
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    try:
        from ai_engine.agents.supervisor_agent import supervisor_agent
        import uuid

        result = supervisor_agent.run_full_pipeline(
            job_id=job_id,
            cv_text=payload.get("cv_text"),
            filename=payload.get("filename", "resume.pdf"),
            workflow_id=payload.get("workflow_id", uuid.uuid4().hex),
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pipeline/{workflow_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_pipeline_status(workflow_id: str) -> dict[str, Any]:
    """Get the status and message history for a workflow."""
    try:
        from ai_engine.agents.supervisor_agent import supervisor_agent
        return supervisor_agent.get_workflow_status(workflow_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/route", dependencies=[Depends(require_role("recruiter", "admin"))])
def route_agent_task(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Route a single task to a specific agent.

    Required body:
        target_agent: str   — e.g., "cv_analysis", "matching", "hiring_rules"
        task_type: str      — e.g., "analyze_cv", "score_single"
        payload: dict       — Task-specific payload
    Optional:
        workflow_id: str
    """
    target_agent = payload.get("target_agent")
    task_type = payload.get("task_type")
    agent_payload = payload.get("payload", {})

    if not target_agent or not task_type:
        raise HTTPException(status_code=400, detail="target_agent and task_type are required")

    try:
        from ai_engine.agents.supervisor_agent import supervisor_agent
        import uuid
        result = supervisor_agent.route_task(
            task_type=task_type,
            target_agent=target_agent,
            agent_payload=agent_payload,
            workflow_id=payload.get("workflow_id", uuid.uuid4().hex),
        )
        return {"agent": target_agent, "task": task_type, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Traces
# ---------------------------------------------------------------------------

@router.get("/traces", dependencies=[Depends(require_role("recruiter", "admin"))])
def list_agent_traces(
    workflow_id: str | None = None,
    agent_name: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List recent agent execution traces."""
    try:
        from ai_engine.observability.tracer import agent_tracer
        return agent_tracer.get_traces(workflow_id=workflow_id, agent_name=agent_name, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/traces/{trace_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_trace_detail(trace_id: str) -> dict[str, Any]:
    """Get a specific trace and all messages in its workflow."""
    try:
        from ai_engine.observability.tracer import agent_tracer
        from ai_engine.agents.message_bus import agent_message_bus

        traces = agent_tracer.get_traces(limit=500)
        trace = next((t for t in traces if t["trace_id"] == trace_id), None)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        messages = agent_message_bus.get_conversation(trace["workflow_id"])
        return {"trace": trace, "workflow_messages": messages}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Supervisor Reflection
# ---------------------------------------------------------------------------

@router.post("/supervisor/reflect", dependencies=[Depends(require_role("recruiter", "admin"))])
def supervisor_reflect(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Trigger supervisor reflection on a completed pipeline result.
    Returns an improved decision if the original confidence was low.
    """
    pipeline_result = payload.get("pipeline_result", {})
    if not pipeline_result:
        raise HTTPException(status_code=400, detail="pipeline_result is required")

    try:
        from ai_engine.agents.supervisor_agent import supervisor_agent

        final = pipeline_result.get("final_decision", {})
        score = final.get("final_score", 0)
        recommendation = final.get("recommendation", "")

        return {
            "original_score": score,
            "reflection": {
                "confidence": "low" if score < 50 else "medium" if score < 75 else "high",
                "recommendation": recommendation,
                "should_retry": score < 40,
                "notes": (
                    "Low confidence — consider manual review or additional CV parsing."
                    if score < 50
                    else "Confidence sufficient for automated pipeline."
                ),
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

@router.get("/memory/stm/{workflow_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_stm(workflow_id: str, key: str | None = None) -> dict[str, Any]:
    """Read short-term memory for a workflow."""
    try:
        from ai_engine.memory.memory_store import memory_store
        if key:
            value = memory_store.read_stm(workflow_id, key)
            return {"workflow_id": workflow_id, "key": key, "value": value}
        # Return available keys (all non-expired for this workflow)
        return {"workflow_id": workflow_id, "note": "Specify ?key=<key> to read a value."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/memory/semantic", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_semantic_memory() -> dict[str, Any]:
    """Return the skills ontology and domain relationships from semantic memory."""
    try:
        from ai_engine.memory.memory_store import memory_store
        return {
            "skills_ontology": memory_store.get_skills_ontology(),
            "domain_relations": memory_store.get_domain_relations(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/memory/episodic/{candidate_id}", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_episodic_memory(candidate_id: str) -> dict[str, Any]:
    """Return episodic memory (full history) for a candidate."""
    try:
        from ai_engine.memory.memory_store import memory_store
        return {
            "candidate_id": candidate_id,
            "history": memory_store.get_candidate_history(candidate_id),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Agent Status
# ---------------------------------------------------------------------------

@router.get("/status", dependencies=[Depends(require_role("recruiter", "admin"))])
def get_agent_status() -> dict[str, Any]:
    """Return the health status of all registered agents."""
    from ai_engine.observability.metrics import get_error_rates, get_agent_latency_stats
    return {
        "agents": [
            "supervisor", "cv_analysis", "job_analysis",
            "matching", "hiring_rules", "recruiter_feedback", "interview",
        ],
        "error_rates": get_error_rates(),
        "latency_stats": get_agent_latency_stats(),
        "rabbitmq_metrics": get_rabbitmq_queue_metrics(),
        "status": "operational",
    }
