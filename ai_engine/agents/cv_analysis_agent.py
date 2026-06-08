"""
CV Analysis Agent

Responsibilities:
  - Resume parsing (PDF / DOCX)
  - Skill extraction with category grouping and evidence
  - Years of experience extraction
  - Seniority level detection (Junior / Mid / Senior)
  - Domain classification (devops, backend_ai, telecom_network, etc.)

Wraps: ai_engine/parser.py, ai_engine/reasoning.py, ai_engine/skills.py
"""
from __future__ import annotations

from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class CVAnalysisAgent(BaseAgent):
    """Parses and deeply analyzes candidate resumes."""

    def __init__(self) -> None:
        super().__init__(name="cv_analysis")
        self._parser = None
        self._skill_extractor = None

    @property
    def parser(self):
        if self._parser is None:
            from ai_engine.parser import ResumeParser
            self._parser = ResumeParser()
        return self._parser

    @property
    def skill_extractor(self):
        if self._skill_extractor is None:
            from ai_engine.skills import SkillExtractor
            self._skill_extractor = SkillExtractor()
        return self._skill_extractor

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "analyze_cv":
            result = self.analyze_cv(
                file_bytes=payload.get("file_bytes"),
                filename=payload.get("filename", "resume.pdf"),
                text=payload.get("text"),  # Provide pre-parsed text to skip parsing
            )
        elif task == "extract_skills":
            result = self.extract_skills(payload.get("text", ""))
        elif task == "infer_seniority":
            result = {"seniority": self.infer_seniority(payload.get("text", ""))}
        elif task == "classify_domain":
            result = {
                "domain": self.classify_domain(
                    payload.get("skills", []), payload.get("text", "")
                )
            }
        else:
            raise ValueError(f"CVAnalysisAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def analyze_cv(
        self,
        file_bytes: bytes | None = None,
        filename: str = "resume.pdf",
        text: str | None = None,
    ) -> dict[str, Any]:
        """
        Full CV analysis pipeline.

        Returns a rich dict with:
            text, skills, grouped_skills, skill_levels, skill_evidence,
            years_of_experience, seniority, primary_domain, secondary_domains,
            inferred_headline, leadership_score, project_depth_score
        """
        from ai_engine.reasoning import build_candidate_insight

        # Step 1: parse raw text if bytes provided
        if text is None:
            if file_bytes is None:
                raise ValueError("CVAnalysisAgent: either file_bytes or text must be provided.")
            text = self.parser.parse(file_bytes, filename)

        # Step 2: deep reasoning insight
        try:
            insight = build_candidate_insight(text)
        except Exception:
            # Fallback to basic extraction
            skills = self.skill_extractor.extract(text)
            from ai_engine.skill_graph import skill_graph
            return {
                "text": text,
                "skills": skills,
                "expanded_skills": list(skill_graph.get_expanded_skills(skills)),
                "grouped_skills": {},
                "skill_levels": {},
                "skill_evidence": {},
                "years_of_experience": 0,
                "seniority": "Mid",
                "primary_domain": "general",
                "secondary_domains": [],
                "inferred_headline": "CV Profile",
                "leadership_score": 0.0,
                "project_depth_score": 0.0,
            }

        # Step 3: grouped skills with evidence
        grouped, evidence, skill_levels = self.skill_extractor.extract_grouped_with_metadata(text)
        from ai_engine.skill_graph import skill_graph

        return {
            "text": text,
            "skills": insight.skills,
            "expanded_skills": list(skill_graph.get_expanded_skills(insight.skills)),
            "grouped_skills": grouped,
            "skill_levels": skill_levels,
            "skill_evidence": evidence,
            "years_of_experience": insight.years_of_experience,
            "seniority": insight.level,
            "primary_domain": insight.primary_domain,
            "secondary_domains": insight.secondary_domains,
            "inferred_headline": insight.inferred_headline,
            "leadership_score": insight.leadership_score,
            "project_depth_score": insight.project_depth_score,
        }

    def extract_skills(self, text: str) -> dict[str, Any]:
        """Extract flat skill list and grouped skills from text."""
        skills = self.skill_extractor.extract(text)
        grouped, evidence, levels = self.skill_extractor.extract_grouped_with_metadata(text)
        return {
            "skills": skills,
            "grouped_skills": grouped,
            "skill_levels": levels,
            "skill_evidence": evidence,
        }

    def infer_seniority(self, text: str) -> str:
        """Return Junior / Mid / Senior based on text signals."""
        from ai_engine.reasoning import CandidateReasoningEngine
        engine = CandidateReasoningEngine()
        return engine.infer_seniority(text)

    def classify_domain(self, skills: list[str], text: str) -> str:
        """Return primary domain: devops, backend_ai, telecom_network, etc."""
        from ai_engine.reasoning import CandidateReasoningEngine
        engine = CandidateReasoningEngine()
        return engine.infer_domain(skills, text)


cv_analysis_agent = CVAnalysisAgent()
