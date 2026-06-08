"""
Hiring Rules Agent

Responsibilities:
  - Mandatory skill enforcement with hard gating
  - Experience requirement validation with nonlinear penalties
  - Education, seniority, language, location compliance checks
  - Salary, employment type, and work authorization eligibility
  - Comprehensive rejection reason logging

Wraps: ai_engine/rules_engine.HiringRulesEngine
"""
from __future__ import annotations

from typing import Any

from ai_engine.agents.base import AgentMessage, BaseAgent


class HiringRulesAgent(BaseAgent):
    """Enforces business compliance rules against candidates."""

    def __init__(self) -> None:
        super().__init__(name="hiring_rules")
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            from ai_engine.rules_engine import HiringRulesEngine
            self._engine = HiringRulesEngine()
        return self._engine

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def run(self, message: AgentMessage) -> AgentMessage:
        task = message.task_type
        payload = message.payload

        if task == "evaluate_eligibility":
            result = self.evaluate_eligibility(payload)
        elif task == "enforce_mandatory_skills":
            result = self.enforce_mandatory_skills(
                payload.get("candidate_skills", []),
                payload.get("mandatory_skills", []),
            )
        elif task == "check_experience":
            result = self.check_experience(
                int(payload.get("candidate_years", 0)),
                int(payload.get("required_years", 0)),
            )
        elif task == "get_template":
            result = self.get_template(payload.get("job_title", ""))
        else:
            raise ValueError(f"HiringRulesAgent: unknown task_type '{task}'")

        return self.reply(message, result)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    def evaluate_eligibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Full eligibility evaluation against hiring rules.

        Required payload keys:
            candidate_name, cv_text, candidate_skills, years_of_experience
        Optional:
            hiring_rules (dict matching HiringRules schema), job_title (for template)
        """
        from backend.app.schemas import HiringRules
        from ai_engine.rules_engine import get_rule_template_for_job

        hiring_rules = None
        hr_data = payload.get("hiring_rules")
        if hr_data and isinstance(hr_data, dict):
            try:
                hiring_rules = HiringRules(**hr_data)
            except Exception:
                pass

        if hiring_rules is None:
            job_title = payload.get("job_title", "")
            if job_title:
                hiring_rules = get_rule_template_for_job(job_title)

        result = self.engine.evaluate(
            candidate_name=payload.get("candidate_name", "Candidate"),
            cv_text=payload.get("cv_text", ""),
            candidate_skills=payload.get("candidate_skills", []),
            years_of_experience=int(payload.get("years_of_experience", 0)),
            hiring_rules=hiring_rules,
        )

        # Enrich with eligibility summary
        result["is_eligible"] = result["rule_status"] == "PASSED"
        result["penalty_pct"] = round(result["penalty"] * 100, 1)
        result["summary"] = (
            f"ELIGIBLE — No blocking rules violated."
            if result["is_eligible"]
            else f"INELIGIBLE — {len(result['reasons'])} rule(s) failed: "
                 + "; ".join(result["reasons"][:3])
        )
        return result

    def enforce_mandatory_skills(
        self, candidate_skills: list[str], mandatory_skills: list[str]
    ) -> dict[str, Any]:
        """
        Check which mandatory skills are present and which are missing.
        Returns pass/fail + per-skill breakdown.
        """
        candidate_lower = {s.lower().strip() for s in candidate_skills}
        breakdown = {}
        for skill in mandatory_skills:
            skill_low = skill.lower().strip()
            breakdown[skill] = skill_low in candidate_lower

        missing = [s for s, present in breakdown.items() if not present]
        return {
            "passed": len(missing) == 0,
            "skill_breakdown": breakdown,
            "missing_mandatory": missing,
            "covered_mandatory": [s for s, present in breakdown.items() if present],
            "coverage_rate": round(
                (len(mandatory_skills) - len(missing)) / max(1, len(mandatory_skills)), 4
            ),
        }

    def check_experience(
        self, candidate_years: int, required_years: int
    ) -> dict[str, Any]:
        """
        Validate experience requirements with nonlinear penalties.
        Penalty table: 1yr→-40%, 3yr→-25%, 5yr→-10%, 8+yr→0%
        """
        if required_years == 0 or candidate_years >= required_years:
            return {
                "passed": True,
                "penalty": 0.0,
                "candidate_years": candidate_years,
                "required_years": required_years,
                "gap_years": 0,
            }

        gap = required_years - candidate_years
        ratio = candidate_years / required_years

        if ratio <= 0.125:
            penalty = 0.40
        elif ratio <= 0.375:
            penalty = 0.40 - (ratio - 0.125) * (0.15 / 0.25)
        elif ratio <= 0.625:
            penalty = 0.25 - (ratio - 0.375) * (0.15 / 0.25)
        else:
            penalty = 0.10 - (ratio - 0.625) * (0.10 / 0.375)

        penalty = round(max(0.0, penalty), 4)

        return {
            "passed": False,
            "penalty": penalty,
            "penalty_pct": round(penalty * 100, 1),
            "candidate_years": candidate_years,
            "required_years": required_years,
            "gap_years": gap,
            "reason": f"Experience below minimum: {candidate_years} yrs vs required {required_years} yrs (-{round(penalty * 100, 0):.0f}%)",
        }

    def get_template(self, job_title: str) -> dict[str, Any]:
        """Return a HiringRules template dict for the given job title."""
        from ai_engine.rules_engine import get_rule_template_for_job
        template = get_rule_template_for_job(job_title)
        return template.model_dump()


hiring_rules_agent = HiringRulesAgent()
