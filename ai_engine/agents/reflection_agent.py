"""
Reflection Agent — Phase 4: Agentic Intelligence

Reviews pipeline decisions, detects inconsistencies, and suggests corrections.
Acts as a quality-assurance layer across the multi-agent system.
"""
from __future__ import annotations

import json
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class ReflectionAgent(BaseAgent):
    """Post-decision review agent that detects inconsistencies."""

    def __init__(self) -> None:
        super().__init__(name="reflection")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "review_decision":
            result = self.review_decision(payload)
        elif task == "review_pipeline":
            result = self.review_pipeline(payload)
        else:
            raise ValueError(f"ReflectionAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def review_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Review a single hiring decision for inconsistencies."""
        match_score = payload.get("match_score", 0)
        rule_status = payload.get("rule_status", "PASSED")
        interview_score = payload.get("interview_score")
        recommendation = payload.get("recommendation", "")
        workflow_id = payload.get("workflow_id", "")

        findings = []

        # Check 1: High match + failed rules = inconsistency
        if match_score >= 70 and rule_status == "FAILED":
            findings.append({
                "type": "inconsistency",
                "severity": "high",
                "description": f"Match score is high ({match_score}%) but hiring rules failed. Review rule strictness.",
                "suggestion": "Consider relaxing non-critical rules or flagging for recruiter override.",
            })

        # Check 2: Low match + pass recommendation = suspicious
        if match_score < 40 and "hire" in recommendation.lower():
            findings.append({
                "type": "inconsistency",
                "severity": "high",
                "description": f"Match score is low ({match_score}%) but recommendation is to hire. Check scoring logic.",
                "suggestion": "Verify skill extraction accuracy and scoring weights.",
            })

        # Check 3: Interview contradiction
        if interview_score is not None:
            if interview_score >= 80 and match_score < 40:
                findings.append({
                    "type": "flag",
                    "severity": "medium",
                    "description": f"Interview score ({interview_score}) is excellent but match score ({match_score}%) is poor.",
                    "suggestion": "Candidate may have skills not captured in CV. Consider updating profile.",
                })
            if interview_score < 30 and match_score >= 80:
                findings.append({
                    "type": "flag",
                    "severity": "medium",
                    "description": f"Match score ({match_score}%) is high but interview score ({interview_score}) is poor.",
                    "suggestion": "CV may overstate capabilities. Prioritize interview signals.",
                })

        # Check 4: Missing data
        if not recommendation:
            findings.append({
                "type": "suggestion",
                "severity": "low",
                "description": "No recommendation was provided. Pipeline may be incomplete.",
                "suggestion": "Ensure the full pipeline completes before making decisions.",
            })

        # Persist findings
        for finding in findings:
            self._save_reflection(workflow_id, finding)

        return {
            "workflow_id": workflow_id,
            "findings_count": len(findings),
            "findings": findings,
            "has_critical": any(f["severity"] == "high" for f in findings),
            "quality_score": max(0, 100 - len(findings) * 25),
        }

    def review_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Review an entire pipeline execution for quality issues."""
        stages = payload.get("stages", {})
        findings = []

        # Check stage completeness
        expected = ["cv_analysis", "matching", "hiring_rules"]
        missing = [s for s in expected if s not in stages]
        if missing:
            findings.append({
                "type": "inconsistency",
                "severity": "high",
                "description": f"Missing pipeline stages: {', '.join(missing)}.",
                "suggestion": "Ensure all required stages complete before finalizing.",
            })

        # Check latency
        for stage_name, stage_data in stages.items():
            latency = stage_data.get("latency_ms", 0)
            if latency > 5000:
                findings.append({
                    "type": "flag",
                    "severity": "medium",
                    "description": f"Stage '{stage_name}' took {latency}ms which exceeds threshold.",
                    "suggestion": "Investigate performance bottleneck in this stage.",
                })

        return {
            "pipeline_stages_reviewed": len(stages),
            "findings": findings,
            "pipeline_health": "healthy" if not findings else "degraded" if len(findings) <= 2 else "unhealthy",
        }

    def _save_reflection(self, workflow_id: str, finding: dict) -> None:
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO agent_reflections (id, workflow_id, agent_name, finding_type, description, severity, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (uuid.uuid4().hex, workflow_id, "reflection", finding["type"],
                     finding["description"], finding["severity"],
                     datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            logger.warning("Failed to save reflection: %s", e)


reflection_agent = ReflectionAgent()
