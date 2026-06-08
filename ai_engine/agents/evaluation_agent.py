"""
Evaluation Agent — Phase 4: Agentic Intelligence

Measures system quality, detects hallucinations, and scores agent performance.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class EvaluationAgent(BaseAgent):
    """Measures agent quality, consistency, and hallucination rates."""

    def __init__(self) -> None:
        super().__init__(name="evaluation")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "evaluate_quality":
            result = self.evaluate_quality(payload)
        elif task == "detect_hallucination":
            result = self.detect_hallucination(payload)
        elif task == "agent_performance_report":
            result = self.agent_performance_report()
        else:
            raise ValueError(f"EvaluationAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def evaluate_quality(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate decision quality based on feedback correlation."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                # Compare AI scores with recruiter decisions
                rows = conn.execute("""
                    SELECT ja.match_score, rf.is_accepted, rf.is_hired
                    FROM recruiter_feedback rf
                    JOIN job_applications ja ON rf.application_id = ja.id
                    ORDER BY rf.created_at DESC
                    LIMIT 100
                """).fetchall()

            if not rows:
                return {"message": "No feedback data available for evaluation."}

            true_positives = sum(1 for r in rows if r["match_score"] >= 60 and r["is_accepted"])
            false_positives = sum(1 for r in rows if r["match_score"] >= 60 and not r["is_accepted"])
            true_negatives = sum(1 for r in rows if r["match_score"] < 60 and not r["is_accepted"])
            false_negatives = sum(1 for r in rows if r["match_score"] < 60 and r["is_accepted"])

            precision = true_positives / max(1, true_positives + false_positives)
            recall = true_positives / max(1, true_positives + false_negatives)
            f1 = 2 * precision * recall / max(0.001, precision + recall)
            accuracy = (true_positives + true_negatives) / max(1, len(rows))

            return {
                "total_decisions_reviewed": len(rows),
                "accuracy": round(accuracy * 100, 1),
                "precision": round(precision * 100, 1),
                "recall": round(recall * 100, 1),
                "f1_score": round(f1 * 100, 1),
                "confusion_matrix": {
                    "true_positives": true_positives,
                    "false_positives": false_positives,
                    "true_negatives": true_negatives,
                    "false_negatives": false_negatives,
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def detect_hallucination(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Check if an agent's claims are supported by source evidence."""
        claims = payload.get("claims", [])  # list of claim strings
        evidence = payload.get("evidence", "")  # source text
        evidence_lower = evidence.lower()

        results = []
        hallucination_count = 0

        for claim in claims:
            claim_words = set(claim.lower().split())
            # Check if key words from the claim appear in evidence
            overlap = sum(1 for w in claim_words if w in evidence_lower and len(w) > 3)
            support_ratio = overlap / max(1, len([w for w in claim_words if len(w) > 3]))

            is_supported = support_ratio >= 0.4
            if not is_supported:
                hallucination_count += 1

            results.append({
                "claim": claim,
                "is_supported": is_supported,
                "support_ratio": round(support_ratio, 2),
            })

        return {
            "total_claims": len(claims),
            "supported": len(claims) - hallucination_count,
            "unsupported": hallucination_count,
            "hallucination_rate": round(hallucination_count / max(1, len(claims)) * 100, 1),
            "details": results,
        }

    def agent_performance_report(self) -> dict[str, Any]:
        """Aggregate agent performance from trace data."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute("""
                    SELECT agent_name, status,
                           AVG(latency_ms) as avg_latency,
                           COUNT(*) as total_tasks,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM agent_traces
                    GROUP BY agent_name
                    ORDER BY total_tasks DESC
                """).fetchall()

            agents = []
            for r in rows:
                total = r["total_tasks"]
                success_rate = r["completed"] / max(1, total) * 100
                agents.append({
                    "agent_name": r["agent_name"],
                    "total_tasks": total,
                    "completed": r["completed"],
                    "failed": r["failed"],
                    "success_rate": round(success_rate, 1),
                    "avg_latency_ms": round(r["avg_latency"], 1) if r["avg_latency"] else 0,
                })

            return {
                "agents": agents,
                "total_agents": len(agents),
                "system_success_rate": round(
                    sum(a["success_rate"] * a["total_tasks"] for a in agents)
                    / max(1, sum(a["total_tasks"] for a in agents)), 1
                ) if agents else 0,
            }
        except Exception as e:
            return {"error": str(e)}


evaluation_agent = EvaluationAgent()
