"""
Agent Memory Store — Four-Layer Memory Architecture

Short-Term Memory (STM):
  - Active workflow context, current candidate evaluation
  - Auto-expires based on TTL (default 1 hour)

Long-Term Memory (LTM):
  - Recruiter preferences, historical decisions, hiring outcomes
  - Persisted indefinitely until explicitly cleared

Semantic Memory:
  - Skills ontology (from skills.py category catalog)
  - Role knowledge (from role_requirements.py templates)
  - Domain relationships (domain → skill mappings)

Episodic Memory:
  - Previous recruiter interactions (what was decided and why)
  - Candidate evaluation history (per candidate across jobs)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any


class AgentMemoryStore:
    """
    SQLite-backed four-layer memory system for the HireMind agent platform.
    All reads/writes are best-effort and fail gracefully.
    """

    # ==================================================================
    # SHORT-TERM MEMORY (STM)
    # ==================================================================

    def write_stm(
        self,
        workflow_id: str,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> None:
        """Write a key-value pair to short-term memory with TTL."""
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        ).isoformat()
        value_json = json.dumps(value)
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_memory_stm (workflow_id, key, value, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(workflow_id, key)
                    DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
                    """,
                    (workflow_id, key, value_json, expires_at),
                )
        except Exception:
            pass

    def read_stm(self, workflow_id: str, key: str) -> Any | None:
        """Read a value from short-term memory, respecting TTL."""
        try:
            from database.connection import get_connection
            now = datetime.now(timezone.utc).isoformat()
            with get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT value FROM agent_memory_stm
                    WHERE workflow_id = ? AND key = ? AND expires_at > ?
                    """,
                    (workflow_id, key, now),
                ).fetchone()
            if row:
                return json.loads(row["value"])
        except Exception:
            pass
        return None

    def clear_stm(self, workflow_id: str) -> None:
        """Delete all STM entries for a workflow."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    "DELETE FROM agent_memory_stm WHERE workflow_id = ?",
                    (workflow_id,),
                )
        except Exception:
            pass

    def cleanup_expired_stm(self) -> int:
        """Purge expired STM entries. Returns count deleted."""
        try:
            from database.connection import get_connection
            now = datetime.now(timezone.utc).isoformat()
            with get_connection() as conn:
                result = conn.execute(
                    "DELETE FROM agent_memory_stm WHERE expires_at <= ?", (now,)
                )
                return result.rowcount
        except Exception:
            return 0

    # ==================================================================
    # LONG-TERM MEMORY (LTM)
    # ==================================================================

    def write_ltm(
        self,
        job_id: str,
        memory_type: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Write to long-term memory.
        memory_type: "recruiter_prefs" | "hiring_outcomes" | "historical_decisions"
        """
        value_json = json.dumps(value)
        updated_at = datetime.now(timezone.utc).isoformat()
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_memory_ltm (job_id, memory_type, key, value, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(job_id, memory_type, key)
                    DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                    """,
                    (job_id, memory_type, key, value_json, updated_at),
                )
        except Exception:
            pass

    def read_ltm(self, job_id: str, memory_type: str, key: str) -> Any | None:
        """Read from long-term memory."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT value FROM agent_memory_ltm
                    WHERE job_id = ? AND memory_type = ? AND key = ?
                    """,
                    (job_id, memory_type, key),
                ).fetchone()
            if row:
                return json.loads(row["value"])
        except Exception:
            pass
        return None

    def read_all_ltm(self, job_id: str, memory_type: str) -> dict[str, Any]:
        """Read all LTM entries of a given type for a job."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT key, value FROM agent_memory_ltm WHERE job_id = ? AND memory_type = ?",
                    (job_id, memory_type),
                ).fetchall()
            return {r["key"]: json.loads(r["value"]) for r in rows}
        except Exception:
            return {}

    # ==================================================================
    # SEMANTIC MEMORY
    # ==================================================================

    def get_skills_ontology(self) -> dict[str, list[str]]:
        """
        Returns the canonical skill ontology grouped by category.
        Sourced from ai_engine/skills.py SKILL_CATEGORIES.
        """
        try:
            from ai_engine.skills import SkillExtractor
            extractor = SkillExtractor()
            # Access the internal skill categories
            if hasattr(extractor, "SKILL_CATEGORIES"):
                return extractor.SKILL_CATEGORIES
            elif hasattr(extractor, "skill_categories"):
                return extractor.skill_categories
        except Exception:
            pass
        return {}

    def get_role_knowledge(self, role_name: str) -> dict[str, Any]:
        """Return structured knowledge about a role from role_requirements."""
        try:
            from ai_engine.role_requirements import build_role_requirements
            req = build_role_requirements(role_name, "")
            return {
                "role_name": req.role_name,
                "required_skills": req.required_skills,
                "advanced_skills": req.advanced_skills,
                "domain": req.domain,
            }
        except Exception:
            return {}

    def get_domain_relations(self) -> dict[str, list[str]]:
        """Return domain → canonical skills mapping."""
        return {
            "devops": [
                "kubernetes", "terraform", "aws", "docker", "ci/cd",
                "jenkins", "ansible", "monitoring", "prometheus", "grafana",
            ],
            "backend_ai": [
                "python", "fastapi", "django", "postgresql", "redis",
                "rest api", "microservices", "celery", "docker",
            ],
            "frontend": [
                "react", "typescript", "javascript", "css", "html",
                "next.js", "vue.js", "webpack", "tailwind",
            ],
            "ai_nlp": [
                "python", "pytorch", "transformers", "nlp", "rag",
                "llm", "sentence-transformers", "hugging face", "openai",
            ],
            "data_ml": [
                "python", "sql", "pandas", "numpy", "scikit-learn",
                "spark", "airflow", "dbt", "tableau", "power bi",
            ],
            "telecom_network": [
                "telecommunications", "networking", "routing", "switching",
                "fiber optics", "wimax", "noc", "bts", "gsm",
            ],
            "cloud_platform": [
                "aws", "azure", "gcp", "kubernetes", "terraform",
                "cloud architecture", "iam", "vpc", "lambda",
            ],
        }

    # ==================================================================
    # EPISODIC MEMORY
    # ==================================================================

    def record_episode(
        self,
        job_id: str,
        candidate_id: str,
        agent_name: str,
        event: str,
        outcome: Any,
    ) -> None:
        """
        Record a discrete evaluation event.
        Example: agent_name="hiring_rules", event="eligibility_check", outcome={"passed": True}
        """
        try:
            from database.connection import get_connection
            ep_id = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO agent_episodes
                        (id, job_id, candidate_id, agent_name, event, outcome, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ep_id, job_id, candidate_id, agent_name, event, json.dumps(outcome), created_at),
                )
        except Exception:
            pass

    def get_candidate_history(self, candidate_id: str) -> list[dict[str, Any]]:
        """Get all evaluation events for a candidate across jobs."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT job_id, agent_name, event, outcome, created_at
                    FROM agent_episodes
                    WHERE candidate_id = ?
                    ORDER BY created_at DESC
                    """,
                    (candidate_id,),
                ).fetchall()
            return [
                {
                    "job_id": r["job_id"],
                    "agent_name": r["agent_name"],
                    "event": r["event"],
                    "outcome": json.loads(r["outcome"] or "{}"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        except Exception:
            return []

    def get_recruiter_interactions(self, job_id: str) -> list[dict[str, Any]]:
        """Get all recruiter feedback interactions for a job."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT rf.application_id, rf.recruiter_decision, rf.is_accepted,
                           rf.rejection_reason, rf.recruiter_notes, rf.created_at,
                           ja.candidate_name, ja.match_score
                    FROM recruiter_feedback rf
                    JOIN job_applications ja ON rf.application_id = ja.id
                    WHERE rf.job_id = ?
                    ORDER BY rf.created_at DESC
                    """,
                    (job_id,),
                ).fetchall()
            return [
                {
                    "application_id": r["application_id"],
                    "candidate_name": r["candidate_name"],
                    "recruiter_decision": r["recruiter_decision"],
                    "is_accepted": bool(r["is_accepted"]),
                    "rejection_reason": r["rejection_reason"],
                    "ai_match_score": float(r["match_score"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        except Exception:
            return []


# Singleton
memory_store = AgentMemoryStore()
