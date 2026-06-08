"""
Workflow Builder — Phase 3: Recruiting Automation

Enables recruiters to create custom Trigger → Agent → Tool → Action workflows.
"""
from __future__ import annotations

import json
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Create and manage custom recruiting workflows."""

    AVAILABLE_TRIGGERS = [
        "application_received", "interview_completed", "feedback_submitted",
        "candidate_hired", "candidate_rejected", "manual",
    ]

    AVAILABLE_AGENTS = [
        "cv_analysis", "matching", "hiring_rules", "interview",
        "outreach", "career_coach", "debate_orchestrator",
    ]

    AVAILABLE_ACTIONS = [
        "send_email", "update_status", "schedule_interview",
        "generate_report", "notify_recruiter", "add_to_pipeline",
    ]

    def create_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new workflow definition."""
        name = payload.get("name", "Untitled Workflow")
        description = payload.get("description", "")
        trigger_event = payload.get("trigger_event", "manual")
        steps = payload.get("steps", [])
        created_by = payload.get("created_by", "system")

        if trigger_event not in self.AVAILABLE_TRIGGERS:
            return {"error": f"Unknown trigger: {trigger_event}. Available: {self.AVAILABLE_TRIGGERS}"}

        # Validate steps
        validated_steps = []
        for step in steps:
            validated_steps.append({
                "order": step.get("order", len(validated_steps) + 1),
                "agent": step.get("agent", ""),
                "action": step.get("action", ""),
                "config": step.get("config", {}),
            })

        workflow_id = str(uuid.uuid4())
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO workflow_definitions (id, name, description, trigger_event, steps_json, created_by, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (workflow_id, name, description, trigger_event,
                     json.dumps(validated_steps), created_by,
                     datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            return {"error": str(e)}

        return {
            "workflow_id": workflow_id,
            "name": name,
            "trigger_event": trigger_event,
            "steps": validated_steps,
            "status": "created",
        }

    def list_workflows(self) -> dict[str, Any]:
        """List all workflow definitions."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, name, trigger_event, is_active, created_at FROM workflow_definitions ORDER BY created_at DESC"
                ).fetchall()
            return {
                "workflows": [
                    {"id": r["id"], "name": r["name"], "trigger": r["trigger_event"],
                     "active": bool(r["is_active"]), "created_at": r["created_at"]}
                    for r in rows
                ]
            }
        except Exception:
            return {"workflows": []}

    def get_available_components(self) -> dict[str, Any]:
        """List available triggers, agents, and actions."""
        return {
            "triggers": self.AVAILABLE_TRIGGERS,
            "agents": self.AVAILABLE_AGENTS,
            "actions": self.AVAILABLE_ACTIONS,
        }


workflow_builder = WorkflowBuilder()
