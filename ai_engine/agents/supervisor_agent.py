"""
Supervisor Agent — Orchestration Brain

Responsibilities:
  - Task orchestration across all specialized agents
  - Workflow routing (which agent handles which task)
  - Agent coordination with structured message passing
  - Final decision aggregation
  - Retry mechanisms (max 3 per agent)
  - Reflection loops (self-correction on low confidence)
  - Human-in-the-loop checkpoint support

Workflow:
    Recruiter Request
        ↓ Job Analysis Agent
        ↓ CV Analysis Agent
        ↓ Matching Agent
        ↓ Hiring Rules Agent
        ↓ [Optional] Interview Agent
        ↓ [Optional] Recruiter Feedback Agent
        → Final Decision
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent, AgentStatus
from ai_engine.agents.events import DomainEvent, EventType

logger = logging.getLogger(__name__)

# Confidence threshold below which the supervisor triggers a reflection loop
REFLECTION_THRESHOLD = 50.0


class SupervisorAgent(BaseAgent):
    """
    Orchestrates the full multi-agent hiring pipeline.
    Coordinates specialized agents via the AgentMessageBus and aggregates
    their outputs into a final hiring decision.
    """

    def __init__(self) -> None:
        super().__init__(name="supervisor", max_retries=1)
        # Lazy-loaded agent registry
        self._agents: dict[str, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Agent Registry (lazy loading)
    # ------------------------------------------------------------------

    def _get_agent(self, agent_name: str) -> BaseAgent:
        if agent_name not in self._agents:
            if agent_name == "cv_analysis":
                from ai_engine.agents.cv_analysis_agent import CVAnalysisAgent
                self._agents[agent_name] = CVAnalysisAgent()
            elif agent_name == "job_analysis":
                from ai_engine.agents.job_analysis_agent import JobAnalysisAgent
                self._agents[agent_name] = JobAnalysisAgent()
            elif agent_name == "matching":
                from ai_engine.agents.matching_agent import MatchingAgent
                self._agents[agent_name] = MatchingAgent()
            elif agent_name == "hiring_rules":
                from ai_engine.agents.hiring_rules_agent import HiringRulesAgent
                self._agents[agent_name] = HiringRulesAgent()
            elif agent_name == "recruiter_feedback":
                from ai_engine.agents.recruiter_feedback_agent import RecruiterFeedbackAgent
                self._agents[agent_name] = RecruiterFeedbackAgent()
            elif agent_name == "interview":
                from ai_engine.agents.interview_agent import InterviewAgent
                self._agents[agent_name] = InterviewAgent()
            else:
                raise ValueError(f"SupervisorAgent: unknown agent '{agent_name}'")
        return self._agents[agent_name]

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "full_pipeline":
            result = self.run_full_pipeline(
                job_id=payload["job_id"],
                cv_text=payload.get("cv_text"),
                file_bytes=payload.get("file_bytes"),
                filename=payload.get("filename", "resume.pdf"),
                confirmed_skills=payload.get("confirmed_skills"),
                workflow_id=message.workflow_id,
                trace_id=message.trace_id,
            )
        elif task == "route":
            result = self.route_task(
                task_type=payload["target_task"],
                target_agent=payload["target_agent"],
                agent_payload=payload["payload"],
                workflow_id=message.workflow_id,
                trace_id=message.trace_id,
            )
        elif task == "aggregate":
            result = self.aggregate_decisions(payload.get("agent_results", {}))
        else:
            raise ValueError(f"SupervisorAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Full Pipeline Orchestration
    # ------------------------------------------------------------------

    def run_full_pipeline(
        self,
        job_id: str,
        cv_text: str | None = None,
        file_bytes: bytes | None = None,
        filename: str = "resume.pdf",
        confirmed_skills: list[str] | None = None,
        workflow_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the full multi-agent hiring pipeline for one candidate.

        Steps:
          1. Job Analysis Agent — analyzes the job
          2. CV Analysis Agent — parses and profiles the candidate
          3. Matching Agent — scores candidate against the job
          4. Hiring Rules Agent — checks eligibility compliance
          5. Reflection loop — re-queries if confidence < threshold
          6. Decision Aggregation — builds final structured decision
        """
        workflow_id = workflow_id or uuid.uuid4().hex
        trace_id = trace_id or uuid.uuid4().hex

        pipeline_log: list[str] = []
        step_results: dict[str, Any] = {
            "workflow_id": workflow_id,
            "job_id": job_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Emit durable workflow start event
        self.bus.publish_event(
            DomainEvent(
                event_type=EventType.CandidateUploaded,
                aggregate_id=workflow_id,
                workflow_id=workflow_id,
                payload={
                    "job_id": job_id,
                    "filename": filename,
                    "source": "workflow_start",
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        )

        # ── Step 1: Fetch job from DB ────────────────────────────────
        job_data = self._fetch_job(job_id)
        if not job_data:
            return {"error": f"Job '{job_id}' not found.", "workflow_id": workflow_id}
        pipeline_log.append(f"[Step 1] Job fetched: {job_data.get('title', '')}")

        # ── Step 2: Job Analysis Agent ───────────────────────────────
        job_analysis_result = self.route_task(
            task_type="analyze_job",
            target_agent="job_analysis",
            agent_payload=job_data,
            workflow_id=workflow_id,
            trace_id=trace_id,
        )
        step_results["job_analysis"] = job_analysis_result
        pipeline_log.append(
            f"[Step 2] Job analyzed: role={job_analysis_result.get('role_class')}, "
            f"seniority={job_analysis_result.get('required_seniority')}"
        )

        # ── Step 3: CV Analysis Agent ────────────────────────────────
        cv_payload: dict[str, Any] = {"filename": filename}
        if cv_text:
            cv_payload["text"] = cv_text
        elif file_bytes:
            cv_payload["file_bytes"] = file_bytes

        cv_analysis_result = self.route_task(
            task_type="analyze_cv",
            target_agent="cv_analysis",
            agent_payload=cv_payload,
            workflow_id=workflow_id,
            trace_id=trace_id,
        )
        step_results["cv_analysis"] = cv_analysis_result
        candidate_skills = cv_analysis_result.get("skills", confirmed_skills or [])
        candidate_text = cv_analysis_result.get("text", cv_text or "")
        self.bus.publish_event(
            DomainEvent(
                event_type=EventType.ResumeParsed,
                aggregate_id=workflow_id,
                workflow_id=workflow_id,
                payload={
                    "skills": candidate_skills,
                    "resume_text": candidate_text[:200],
                    "seniority": cv_analysis_result.get("seniority", ""),
                    "domain": cv_analysis_result.get("primary_domain", ""),
                    "summary": cv_analysis_result.get("summary", ""),
                },
            )
        )
        pipeline_log.append(
            f"[Step 3] CV analyzed: {len(candidate_skills)} skills, "
            f"seniority={cv_analysis_result.get('seniority')}, "
            f"domain={cv_analysis_result.get('primary_domain')}"
        )

        # ── Step 4: Matching Agent ───────────────────────────────────
        matching_payload = {
            "candidate_text": candidate_text,
            "candidate_skills": candidate_skills,
            "job_title": job_data.get("title", ""),
            "job_description": job_data.get("description", ""),
            "required_skills": job_data.get("required_skills", []),
            "experience_level": job_data.get("experience_level", ""),
            "domain": job_data.get("domain", ""),
            "hiring_rules": job_data.get("hiring_rules"),
            "job_id": job_id,
        }

        matching_result = self.route_task(
            task_type="score_single",
            target_agent="matching",
            agent_payload=matching_payload,
            workflow_id=workflow_id,
            trace_id=trace_id,
        )
        step_results["matching"] = matching_result
        match_score = matching_result.get("match_percentage", 0.0)
        self.bus.publish_event(
            DomainEvent(
                event_type=EventType.CandidateMatched,
                aggregate_id=workflow_id,
                workflow_id=workflow_id,
                payload={
                    "candidate_id": workflow_id,
                    "job_id": job_id,
                    "match_score": match_score,
                    "matched_skills": matching_result.get("matched_skills", []),
                    "missing_skills": matching_result.get("missing_skills", []),
                    "recommendation": matching_result.get("recommendation", ""),
                },
            )
        )
        pipeline_log.append(f"[Step 4] Matching complete: score={match_score:.1f}%")

        # ── Step 5: Reflection Loop ──────────────────────────────────
        reflection_triggered = False
        if match_score < REFLECTION_THRESHOLD:
            pipeline_log.append(
                f"[Step 5] Reflection loop triggered (score {match_score:.1f}% < {REFLECTION_THRESHOLD}%)"
            )
            reflection_triggered = True
            # Re-score with expanded candidate text using reasoning context
            expanded_text = candidate_text + " " + " ".join(candidate_skills)
            matching_payload["candidate_text"] = expanded_text
            reflected_result = self.route_task(
                task_type="score_single",
                target_agent="matching",
                agent_payload=matching_payload,
                workflow_id=workflow_id,
                trace_id=trace_id,
            )
            if reflected_result.get("match_percentage", 0.0) > match_score:
                matching_result = reflected_result
                match_score = matching_result.get("match_percentage", 0.0)
                step_results["matching_reflected"] = matching_result
                pipeline_log.append(f"[Step 5] Reflection improved score to {match_score:.1f}%")

        # ── Step 6: Hiring Rules Agent ───────────────────────────────
        rules_payload = {
            "candidate_name": cv_analysis_result.get("inferred_headline", "Candidate"),
            "cv_text": candidate_text,
            "candidate_skills": candidate_skills,
            "years_of_experience": cv_analysis_result.get("years_of_experience", 0),
            "hiring_rules": job_data.get("hiring_rules"),
            "job_title": job_data.get("title", ""),
        }
        rules_result = self.route_task(
            task_type="evaluate_eligibility",
            target_agent="hiring_rules",
            agent_payload=rules_payload,
            workflow_id=workflow_id,
            trace_id=trace_id,
        )
        step_results["hiring_rules"] = rules_result
        pipeline_log.append(
            f"[Step 6] Rules check: {rules_result.get('rule_status')} — "
            f"{rules_result.get('summary', '')[:80]}"
        )

        # ── Step 7: Final Aggregation ────────────────────────────────
        final_decision = self.aggregate_decisions({
            "job_analysis": job_analysis_result,
            "cv_analysis": cv_analysis_result,
            "matching": matching_result,
            "hiring_rules": rules_result,
        })
        step_results["final_decision"] = final_decision
        step_results["pipeline_log"] = pipeline_log
        step_results["reflection_triggered"] = reflection_triggered
        step_results["completed_at"] = datetime.now(timezone.utc).isoformat()

        outcome_event = EventType.CandidateRejected
        if final_decision.get("final_score", 0.0) >= 80.0 and final_decision.get("is_eligible", False):
            outcome_event = EventType.CandidateHired

        self.bus.publish_event(
            DomainEvent(
                event_type=outcome_event,
                aggregate_id=workflow_id,
                workflow_id=workflow_id,
                payload={
                    "candidate_id": workflow_id,
                    "job_id": job_id,
                    "reason": final_decision.get("recommendation", ""),
                    "offer_details": {
                        "recommendation": final_decision.get("recommendation", ""),
                        "final_score": final_decision.get("final_score", 0.0),
                    },
                },
            )
        )

        pipeline_log.append(
            f"[Step 7] Final Decision: {final_decision.get('recommendation')} "
            f"(score={final_decision.get('final_score', 0):.1f}%)"
        )

        return step_results

    # ------------------------------------------------------------------
    # Task Routing
    # ------------------------------------------------------------------

    def route_task(
        self,
        task_type: str,
        target_agent: str,
        agent_payload: dict[str, Any],
        workflow_id: str = "",
        trace_id: str = "",
    ) -> dict[str, Any]:
        """
        Route a task to the specified agent and return the result.
        Handles retries via the agent's own execute() wrapper.
        """
        message = AgentMessage(
            sender_agent=self.name,
            receiver_agent=target_agent,
            task_type=task_type,
            payload=agent_payload,
            workflow_id=workflow_id or uuid.uuid4().hex,
            trace_id=trace_id or uuid.uuid4().hex,
        )
        self.bus.publish(message)

        result_msg = self.bus.wait_for_response(
            receiver_agent=self.name,
            trace_id=message.trace_id,
            workflow_id=message.workflow_id,
            timeout_seconds=30,
        )

        if result_msg is None:
            logger.warning("[Supervisor] timeout waiting for %s.%s result", target_agent, task_type)
            return {"error": "timeout waiting for agent response", "agent": target_agent, "task": task_type}

        if result_msg.status == "failed":
            logger.warning(
                f"[Supervisor] {target_agent}.{task_type} failed: {result_msg.error}"
            )
            return {"error": result_msg.error, "agent": target_agent, "task": task_type}

        return result_msg.result or {}

    # ------------------------------------------------------------------
    # Decision Aggregation
    # ------------------------------------------------------------------

    def aggregate_decisions(self, agent_results: dict[str, Any]) -> dict[str, Any]:
        """
        Combine outputs from all agents into a single hiring decision.

        Scoring weights:
          - Matching score: 60%
          - Rules compliance: 20% (hard gate if rejected)
          - CV quality signals (leadership + project depth): 20%
        """
        matching = agent_results.get("matching", {})
        rules = agent_results.get("hiring_rules", {})
        cv = agent_results.get("cv_analysis", {})
        job = agent_results.get("job_analysis", {})

        match_score = float(matching.get("match_percentage", 0.0))
        is_eligible = rules.get("is_eligible", True)
        rules_penalty = float(rules.get("penalty", 0.0))
        leadership = float(cv.get("leadership_score", 0.0))
        depth = float(cv.get("project_depth_score", 0.0))

        # Weighted score
        cv_quality_score = (leadership * 0.5 + depth * 0.5) * 100.0
        final_score = (
            match_score * 0.60
            + (100.0 if is_eligible else max(0.0, 100.0 - rules_penalty * 100)) * 0.20
            + cv_quality_score * 0.20
        )
        final_score = round(max(0.0, final_score), 2)

        # Hard gate: ineligible candidates cannot appear in Top 3
        if not is_eligible:
            final_score = min(final_score, 45.0)  # Force below typical passing threshold

        # Recommendation
        if final_score >= 80.0 and is_eligible:
            recommendation = "Strong Match — Proceed to Interview"
        elif final_score >= 65.0 and is_eligible:
            recommendation = "Good Fit — Consider for Interview"
        elif final_score >= 50.0:
            recommendation = "Partial Match — Review Manually"
        elif not is_eligible:
            recommendation = f"Ineligible — {'; '.join(rules.get('reasons', ['Rule violation'])[:2])}"
        else:
            recommendation = "Weak Match — Not Recommended"

        return {
            "final_score": final_score,
            "match_score": match_score,
            "is_eligible": is_eligible,
            "recommendation": recommendation,
            "matched_skills": matching.get("matched_skills", []),
            "missing_skills": matching.get("missing_skills", []),
            "rule_status": rules.get("rule_status", "PASSED"),
            "rule_reasons": rules.get("reasons", []),
            "candidate_seniority": cv.get("seniority", ""),
            "candidate_domain": cv.get("primary_domain", ""),
            "required_seniority": job.get("required_seniority", ""),
            "role_class": job.get("role_class", ""),
            "penalties": matching.get("penalties", []) + rules.get("reasons", []),
            "score_breakdown": {
                "matching_contribution": round(match_score * 0.60, 2),
                "rules_contribution": round((100.0 if is_eligible else 0.0) * 0.20, 2),
                "cv_quality_contribution": round(cv_quality_score * 0.20, 2),
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_job(self, job_id: str) -> dict[str, Any] | None:
        """Fetch job record from the database."""
        try:
            import json
            from database.connection import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM posted_jobs WHERE id = ?", (job_id,)
                ).fetchone()
            if not row:
                return None
            job = dict(row)
            for field in ["required_skills", "responsibilities", "preferred_skills", "tools"]:
                if isinstance(job.get(field), str):
                    try:
                        job[field] = json.loads(job[field])
                    except Exception:
                        job[field] = []
            if isinstance(job.get("hiring_rules"), str):
                try:
                    job["hiring_rules"] = json.loads(job["hiring_rules"])
                except Exception:
                    job["hiring_rules"] = {}
            return job
        except Exception as exc:
            logger.error(f"[Supervisor] fetch_job failed: {exc}")
            return None

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get the current status of a workflow from agent messages."""
        from ai_engine.agents.message_bus import agent_message_bus
        messages = agent_message_bus.get_conversation(workflow_id)
        agents_involved = list({m["sender_agent"] for m in messages} | {m["receiver_agent"] for m in messages})
        return {
            "workflow_id": workflow_id,
            "message_count": len(messages),
            "agents_involved": agents_involved,
            "messages": messages,
        }


supervisor_agent = SupervisorAgent()
