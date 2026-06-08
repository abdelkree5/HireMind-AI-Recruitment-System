"""
Multi-Agent Debate System — Phase 4: Agentic Intelligence

Structured deliberation protocol where multiple agents argue from their
perspectives about candidate quality and reach an explainable consensus.
"""
from __future__ import annotations

import json
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

from ai_engine.agents.base import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class DebateAgent(BaseAgent):
    """Orchestrates multi-agent debates about candidate quality."""

    def __init__(self) -> None:
        super().__init__(name="debate_orchestrator")

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "run_debate":
            result = self.run_debate(payload)
        else:
            raise ValueError(f"DebateAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    def run_debate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a full multi-agent debate.

        Required: candidate_data (dict with text, skills, etc.), job_data (dict with title, etc.)
        """
        candidate = payload.get("candidate_data", {})
        job = payload.get("job_data", {})
        debate_id = str(uuid.uuid4())

        participants = ["matching", "hiring_rules", "cv_analysis", "job_analysis"]
        rounds = []

        # Round 1: Each agent presents its assessment
        round1_arguments = []
        for agent_name in participants:
            argument = self._get_agent_argument(agent_name, candidate, job)
            round1_arguments.append({
                "agent": agent_name,
                "position": argument.get("position", "neutral"),
                "score": argument.get("score", 50),
                "reasoning": argument.get("reasoning", ""),
                "evidence": argument.get("evidence", []),
            })
        rounds.append({"round": 1, "type": "initial_arguments", "arguments": round1_arguments})

        # Round 2: Rebuttals — each agent responds to the weakest argument
        round2_rebuttals = []
        scores = [(a["agent"], a["score"]) for a in round1_arguments]
        scores.sort(key=lambda x: x[1])
        weakest = scores[0] if scores else None
        strongest = scores[-1] if scores else None

        if weakest and strongest and weakest[0] != strongest[0]:
            round2_rebuttals.append({
                "from_agent": strongest[0],
                "to_agent": weakest[0],
                "rebuttal": f"{strongest[0]} argues that despite {weakest[0]}'s concerns, the candidate shows strong signals in other areas.",
            })
        rounds.append({"round": 2, "type": "rebuttals", "rebuttals": round2_rebuttals})

        # Round 3: Consensus
        avg_score = sum(a["score"] for a in round1_arguments) / max(1, len(round1_arguments))
        votes = {"hire": 0, "pass": 0, "maybe": 0}
        for a in round1_arguments:
            if a["score"] >= 70:
                votes["hire"] += 1
            elif a["score"] >= 45:
                votes["maybe"] += 1
            else:
                votes["pass"] += 1

        majority = max(votes, key=votes.get)
        dissenting = [a["agent"] for a in round1_arguments if (a["score"] >= 70) != (majority == "hire")]

        consensus = {
            "decision": majority,
            "confidence": round(avg_score, 1),
            "votes": votes,
            "dissenting_agents": dissenting,
            "consensus_reasoning": f"The panel {'recommends hiring' if majority == 'hire' else 'recommends passing on' if majority == 'pass' else 'needs further evaluation of'} this candidate with {round(avg_score, 1)}% average confidence.",
        }
        rounds.append({"round": 3, "type": "consensus", "result": consensus})

        # Persist to database
        self._save_debate(debate_id, candidate, job, participants, rounds, consensus)

        return {
            "debate_id": debate_id,
            "participants": participants,
            "rounds": rounds,
            "consensus": consensus,
        }

    def _get_agent_argument(self, agent_name: str, candidate: dict, job: dict) -> dict:
        """Get each agent's perspective on the candidate."""
        if agent_name == "matching":
            skills = candidate.get("skills", [])
            required = job.get("required_skills", [])
            matched = set(s.lower() for s in skills) & set(s.lower() for s in required)
            coverage = len(matched) / max(1, len(required)) * 100
            return {
                "position": "hire" if coverage >= 60 else "pass",
                "score": round(coverage, 1),
                "reasoning": f"Skill coverage is {round(coverage, 1)}%. Matched {len(matched)}/{len(required)} required skills.",
                "evidence": list(matched)[:5],
            }

        elif agent_name == "hiring_rules":
            years = candidate.get("years_of_experience", 0)
            req_level = job.get("experience_level", "")
            meets_exp = years >= 5 if "senior" in req_level.lower() else years >= 2 if "mid" in req_level.lower() else True
            score = 80 if meets_exp else 30
            return {
                "position": "hire" if meets_exp else "pass",
                "score": score,
                "reasoning": f"Candidate has {years} years of experience. {'Meets' if meets_exp else 'Does not meet'} requirements.",
                "evidence": [f"{years} years experience"],
            }

        elif agent_name == "cv_analysis":
            text = candidate.get("text", "")
            depth_signals = sum(1 for kw in ["built", "deployed", "designed", "led", "optimized"] if kw in text.lower())
            score = min(100, 40 + depth_signals * 12)
            return {
                "position": "hire" if score >= 60 else "maybe",
                "score": score,
                "reasoning": f"CV shows {depth_signals} depth signals. Profile indicates {'strong' if score >= 70 else 'moderate'} project experience.",
                "evidence": [f"{depth_signals} depth signals detected"],
            }

        elif agent_name == "job_analysis":
            title = job.get("title", "")
            domain = job.get("domain", "")
            return {
                "position": "neutral",
                "score": 60,
                "reasoning": f"Job '{title}' in domain '{domain}' requires standard assessment.",
                "evidence": [title, domain],
            }

        return {"position": "neutral", "score": 50, "reasoning": "No data available.", "evidence": []}

    def _save_debate(self, debate_id, candidate, job, participants, rounds, consensus):
        """Persist debate to database."""
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO debate_sessions (id, candidate_id, job_id, participants_json, rounds_json, consensus_json, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (debate_id, candidate.get("id", ""), job.get("id", ""),
                     json.dumps(participants), json.dumps(rounds), json.dumps(consensus),
                     "completed", datetime.now(timezone.utc).isoformat()),
                )
        except Exception as e:
            logger.warning("Failed to save debate session: %s", e)


debate_agent = DebateAgent()
