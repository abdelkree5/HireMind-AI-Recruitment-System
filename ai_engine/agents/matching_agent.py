"""
Matching Agent

Responsibilities:
  - Stage 1: BM25 sparse retrieval
  - Stage 2: Dense vector retrieval (sentence-transformers)
  - Stage 3: Hybrid RRF fusion
  - Stage 4: Cross-Encoder re-ranking (MS-Marco)
  - Stage 5: Agentic reflection loop (query expansion)
  - Stage 6: Final candidate scoring with multi-factor confidence

Wraps: ai_engine/matcher.RecruitmentMatcher
"""
from __future__ import annotations

from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class MatchingAgent(BaseAgent):
    """
    Executes the 6-stage Hybrid Agentic RAG retrieval and scoring pipeline.
    """

    def __init__(self) -> None:
        super().__init__(name="matching")
        self._matcher = None

    @property
    def matcher(self):
        if self._matcher is None:
            from ai_engine.matcher import RecruitmentMatcher
            self._matcher = RecruitmentMatcher()
        return self._matcher

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "score_single":
            result = self.score_single_candidate(payload)
        elif task == "retrieve_and_rank":
            result = self.retrieve_and_rank(payload)
        else:
            raise ValueError(f"MatchingAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def score_single_candidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Score a single candidate against a job.

        Required payload keys:
            candidate_text, candidate_skills, job_title,
            job_description, required_skills
        Optional:
            candidate_level, job_level, hiring_rules, job_id
        """
        from backend.app.schemas import HiringRules

        hiring_rules = None
        hr_data = payload.get("hiring_rules")
        if hr_data and isinstance(hr_data, dict):
            try:
                hiring_rules = HiringRules(**hr_data)
            except Exception:
                pass

        # Merge expanded skills from the semantic graph
        candidate_skills = payload.get("candidate_skills", [])
        expanded = payload.get("expanded_skills", [])
        combined_skills = list(set(candidate_skills + expanded))

        report = self.matcher.score(
            candidate_text=payload["candidate_text"],
            candidate_skills=combined_skills,
            job_title=payload["job_title"],
            job_description=payload["job_description"],
            required_skills=payload.get("required_skills", []),
            candidate_level=payload.get("candidate_level"),
            job_level=payload.get("job_level"),
            hiring_rules=hiring_rules,
            job_id=payload.get("job_id", ""),
        )

        return {
            "match_percentage": report.match_percentage,
            "similarity": report.similarity,
            "skill_score": report.skill_score,
            "title_score": report.title_score,
            "experience_alignment_score": report.experience_alignment_score,
            "reranker_score": report.reranker_score,
            "matched_skills": report.matched_skills,
            "missing_skills": report.missing_skills,
            "penalties": report.penalties,
            "score_breakdown": report.score_breakdown,
            "recommendation": report.recommendation,
            "reason": report.reason,
            "rule_status": report.rule_status,
            "rule_reasons": report.rule_reasons,
            "logs": report.logs,
        }

    def retrieve_and_rank(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Rank multiple candidates for a job using the 6-stage pipeline.

        Required payload keys:
            candidates (list of {id, name, text, skills}),
            job_title, job_description, required_skills
        Optional:
            experience_level, domain, ground_truth, hiring_rules, job_id
        """
        from backend.app.schemas import HiringRules

        hiring_rules = None
        hr_data = payload.get("hiring_rules")
        if hr_data and isinstance(hr_data, dict):
            try:
                hiring_rules = HiringRules(**hr_data)
            except Exception:
                pass

        candidates = payload["candidates"]
        for cand in candidates:
            cand_skills = cand.get("skills", [])
            expanded = cand.get("expanded_skills", [])
            cand["skills"] = list(set(cand_skills + expanded))

        reports = self.matcher.retrieve_and_rank(
            candidates=candidates,
            job_title=payload["job_title"],
            job_description=payload["job_description"],
            required_skills=payload.get("required_skills", []),
            experience_level=payload.get("experience_level", ""),
            domain=payload.get("domain", ""),
            ground_truth=payload.get("ground_truth"),
            hiring_rules=hiring_rules,
            job_id=payload.get("job_id", ""),
        )

        ranked = []
        for i, r in enumerate(reports, 1):
            ranked.append({
                "rank": i,
                "match_percentage": r.match_percentage,
                "similarity": r.similarity,
                "skill_score": r.skill_score,
                "matched_skills": r.matched_skills,
                "missing_skills": r.missing_skills,
                "penalties": r.penalties,
                "score_breakdown": r.score_breakdown,
                "recommendation": r.recommendation,
                "reason": r.reason,
                "rule_status": r.rule_status,
                "rule_reasons": r.rule_reasons,
            })

        return {
            "ranked_candidates": ranked,
            "total": len(ranked),
            "pipeline_stages": [
                "BM25 Sparse Retrieval",
                "Dense Vector Retrieval",
                "RRF Fusion",
                "Cross-Encoder Re-ranking",
                "Agentic Reflection",
                "Final Ranking",
            ],
        }


matching_agent = MatchingAgent()
