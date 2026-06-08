"""
Job Analysis Agent

Responsibilities:
  - Job description parsing and structuring
  - Mandatory vs. preferred skill detection
  - Role classification (DevOps, Backend, Frontend, ML, etc.)
  - Seniority requirements extraction (Junior / Mid / Senior)
  - Hiring rules template generation per role

Wraps: ai_engine/role_requirements.py, ai_engine/rules_engine.py
"""
from __future__ import annotations

import re
from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class JobAnalysisAgent(BaseAgent):
    """Parses and deeply analyzes job descriptions."""

    def __init__(self) -> None:
        super().__init__(name="job_analysis")

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "analyze_job":
            result = self.analyze_job(payload)
        elif task == "extract_mandatory_skills":
            result = {
                "mandatory_skills": self.extract_mandatory_skills(
                    payload.get("title", ""),
                    payload.get("description", ""),
                    payload.get("required_skills", []),
                )
            }
        elif task == "classify_role":
            result = {"role_class": self.classify_role(payload.get("title", ""), payload.get("domain", ""))}
        elif task == "classify_seniority":
            result = {"seniority": self.classify_seniority(payload.get("title", ""), payload.get("description", ""))}
        elif task == "get_hiring_rules_template":
            result = self.get_hiring_rules_template(payload.get("title", ""))
        else:
            raise ValueError(f"JobAnalysisAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def analyze_job(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Full job analysis pipeline.

        Input keys: title, description, required_skills, preferred_skills,
                    tools, experience_level, domain, hiring_rules
        """
        title = job_data.get("title", "")
        description = job_data.get("description", "")
        required_skills = job_data.get("required_skills", [])
        preferred_skills = job_data.get("preferred_skills", [])

        role_class = self.classify_role(title, job_data.get("domain", ""))
        seniority = self.classify_seniority(title, description)
        mandatory_skills = self.extract_mandatory_skills(title, description, required_skills)
        min_experience = self._extract_min_experience(description)
        hiring_rules_template = self.get_hiring_rules_template(title)

        return {
            "title": title,
            "role_class": role_class,
            "required_seniority": seniority,
            "mandatory_skills": mandatory_skills,
            "preferred_skills": preferred_skills,
            "min_experience_years": min_experience,
            "hiring_rules_template": hiring_rules_template,
            "skill_count": len(required_skills),
            "domain": job_data.get("domain", self._infer_domain(title, required_skills)),
        }

    def extract_mandatory_skills(
        self, title: str, description: str, required_skills: list[str]
    ) -> list[str]:
        """
        Determine which skills are effectively mandatory.
        Uses both explicit required_skills list and role-based templates.
        """
        from ai_engine.rules_engine import get_rule_template_for_job
        template = get_rule_template_for_job(title)

        # Start with template mandatory skills
        mandatory = set(s.lower() for s in template.mandatory_skills)

        # Add the first 40% of provided required_skills as mandatory
        if required_skills:
            core_count = max(1, len(required_skills) // 2)
            for skill in required_skills[:core_count]:
                mandatory.add(skill.lower().strip())

        # Look for "must have" / "required" language in description
        must_have_pattern = re.compile(
            r"(?:must\s+have|required|mandatory|essential)[:\s]+([^\.\n]+)",
            re.IGNORECASE,
        )
        for match in must_have_pattern.finditer(description):
            phrase = match.group(1).lower()
            # Extract recognized skills from the phrase
            for skill in required_skills:
                if skill.lower().strip() in phrase:
                    mandatory.add(skill.lower().strip())

        return sorted(mandatory)

    def classify_role(self, title: str, domain: str = "") -> str:
        """
        Classify job into a canonical role category.
        Returns one of: DevOps, Backend, Frontend, ML/AI, Data, Mobile, Other
        """
        title_lower = title.lower()
        domain_lower = domain.lower()

        if any(k in title_lower for k in ["devops", "sre", "platform", "infrastructure", "cloud"]):
            return "DevOps"
        if any(k in title_lower for k in ["machine learning", "ml", "ai ", "nlp", "data scientist"]):
            return "ML/AI"
        if any(k in title_lower for k in ["data engineer", "data analyst", "analytics", "bi "]):
            return "Data"
        if any(k in title_lower for k in ["frontend", "front-end", "react", "vue", "angular", "ui "]):
            return "Frontend"
        if any(k in title_lower for k in ["mobile", "ios", "android", "flutter", "swift"]):
            return "Mobile"
        if any(k in title_lower for k in ["backend", "back-end", "python", "java", "go ", "api ", "fastapi"]):
            return "Backend"
        if "devops" in domain_lower:
            return "DevOps"
        return "Backend"

    def classify_seniority(self, title: str, description: str) -> str:
        """Extract required seniority from job title and description."""
        text = (title + " " + description).lower()
        if any(t in text for t in ["principal", "staff", "lead ", "senior ", "sr."]):
            return "Senior"
        if any(t in text for t in ["junior", "entry level", "entry-level", "intern"]):
            return "Junior"
        # Check years of experience as a secondary signal
        exp = self._extract_min_experience(description)
        if exp >= 7:
            return "Senior"
        if exp <= 2:
            return "Junior"
        return "Mid"

    def get_hiring_rules_template(self, job_title: str) -> dict[str, Any]:
        """Return a HiringRules template for the given job title as a dict."""
        from ai_engine.rules_engine import get_rule_template_for_job
        template = get_rule_template_for_job(job_title)
        return template.model_dump()

    def _extract_min_experience(self, description: str) -> int:
        """Extract the minimum years of experience from description text."""
        patterns = [
            r"(\d+)\+?\s*years?\s+of\s+experience",
            r"minimum\s+of\s+(\d+)\s+years?",
            r"at\s+least\s+(\d+)\s+years?",
            r"(\d+)\s*(?:\+|-)\s*years?\s+experience",
        ]
        values = []
        for pat in patterns:
            for m in re.finditer(pat, description.lower()):
                try:
                    values.append(int(m.group(1)))
                except ValueError:
                    pass
        return min(values) if values else 0

    def _infer_domain(self, title: str, required_skills: list[str]) -> str:
        """Infer domain from title and skills."""
        role_class = self.classify_role(title)
        mapping = {
            "DevOps": "devops",
            "Backend": "backend_ai",
            "ML/AI": "ai_nlp",
            "Data": "data_ml",
            "Frontend": "frontend",
            "Mobile": "mobile",
        }
        return mapping.get(role_class, "general")


job_analysis_agent = JobAnalysisAgent()
