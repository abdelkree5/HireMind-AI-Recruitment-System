"""
MCP Tool Registry — Phase 8

Provides a secure, RBAC-controlled tool registry for the HireMind
Multi-Agent platform. Agents and API consumers discover and execute
tools through this registry.

All internal platform capabilities are registered here.
Future external integrations (ATS, LinkedIn, Calendar) are registered
as architecture-ready stubs.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Role hierarchy — each role can access everything in lower roles
ROLE_HIERARCHY = {
    "admin":     {"admin", "recruiter", "candidate", "any"},
    "recruiter": {"recruiter", "candidate", "any"},
    "candidate": {"candidate", "any"},
    "any":       {"any"},
}


@dataclass
class ToolDefinition:
    """Metadata and handler for a registered tool."""
    name: str
    description: str
    handler: Callable[..., Any]
    required_role: str               # Minimum role required
    input_schema: dict[str, Any]     # JSON Schema dict for inputs
    tags: list[str] = field(default_factory=list)
    is_stub: bool = False            # True = architecture placeholder, not implemented


class ToolRegistry:
    """
    Singleton registry for all HireMind platform tools.

    Usage:
        registry.execute_tool("parse_cv", {"file_bytes": ..., "filename": ...},
                              caller_agent="supervisor", caller_role="recruiter")
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        required_role: str = "any",
        input_schema: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        is_stub: bool = False,
    ) -> None:
        """Register a new tool in the registry."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            required_role=required_role,
            input_schema=input_schema or {},
            tags=tags or [],
            is_stub=is_stub,
        )
        logger.debug(f"[ToolRegistry] Registered tool: '{name}' (role={required_role})")

    def execute_tool(
        self,
        name: str,
        params: dict[str, Any],
        caller_agent: str = "unknown",
        caller_role: str = "any",
    ) -> dict[str, Any]:
        """
        Execute a registered tool with RBAC enforcement.

        Raises:
            ValueError: If tool not found or role is unauthorized.
        Returns:
            dict with "result" key containing tool output.
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")

        tool = self._tools[name]

        # RBAC check
        allowed_roles = ROLE_HIERARCHY.get(caller_role, {"any"})
        if tool.required_role not in allowed_roles:
            raise PermissionError(
                f"Role '{caller_role}' is not authorized to execute tool '{name}' "
                f"(requires: '{tool.required_role}')"
            )

        if tool.is_stub:
            return {
                "result": None,
                "status": "stub",
                "message": f"Tool '{name}' is a future integration stub — not yet implemented.",
            }

        try:
            result = tool.handler(**params)
            logger.info(f"[ToolRegistry] {caller_agent} executed '{name}' successfully.")
            return {"result": result, "status": "success"}
        except Exception as exc:
            logger.error(f"[ToolRegistry] Tool '{name}' execution failed: {exc}")
            raise

    def list_tools(self, role: str = "any") -> list[dict[str, Any]]:
        """List all tools accessible by the given role."""
        allowed = ROLE_HIERARCHY.get(role, {"any"})
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_role": t.required_role,
                "tags": t.tags,
                "is_stub": t.is_stub,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
            if t.required_role in allowed
        ]

    def get_tool_info(self, name: str) -> dict[str, Any] | None:
        """Get metadata for a specific tool."""
        tool = self._tools.get(name)
        if not tool:
            return None
        return {
            "name": tool.name,
            "description": tool.description,
            "required_role": tool.required_role,
            "tags": tool.tags,
            "is_stub": tool.is_stub,
            "input_schema": tool.input_schema,
        }


# ---------------------------------------------------------------------------
# Tool Handlers (internal implementations)
# ---------------------------------------------------------------------------

def _tool_parse_cv(file_bytes: bytes, filename: str = "resume.pdf") -> dict:
    from ai_engine.parser import ResumeParser
    text = ResumeParser().parse(file_bytes, filename)
    return {"text": text, "char_count": len(text)}


def _tool_extract_skills(text: str) -> dict:
    from ai_engine.skills import SkillExtractor
    skills = SkillExtractor().extract(text)
    return {"skills": skills, "count": len(skills)}


def _tool_score_candidate(
    candidate_text: str,
    candidate_skills: list,
    job_title: str,
    job_description: str,
    required_skills: list,
    job_id: str = "",
) -> dict:
    from ai_engine.matcher import RecruitmentMatcher
    report = RecruitmentMatcher().score(
        candidate_text, candidate_skills, job_title, job_description, required_skills, job_id=job_id
    )
    return {
        "match_percentage": report.match_percentage,
        "matched_skills": report.matched_skills,
        "missing_skills": report.missing_skills,
        "score_breakdown": report.score_breakdown,
        "recommendation": report.recommendation,
    }


def _tool_evaluate_hiring_rules(
    candidate_name: str,
    cv_text: str,
    candidate_skills: list,
    years_of_experience: int,
    hiring_rules: dict | None = None,
    job_title: str = "",
) -> dict:
    from ai_engine.rules_engine import HiringRulesEngine, get_rule_template_for_job
    from backend.app.schemas import HiringRules

    rules_obj = None
    if hiring_rules:
        try:
            rules_obj = HiringRules(**hiring_rules)
        except Exception:
            pass
    if not rules_obj and job_title:
        rules_obj = get_rule_template_for_job(job_title)

    result = HiringRulesEngine().evaluate(
        candidate_name=candidate_name,
        cv_text=cv_text,
        candidate_skills=candidate_skills,
        years_of_experience=years_of_experience,
        hiring_rules=rules_obj,
    )
    return result


def _tool_submit_feedback(payload: dict) -> dict:
    from backend.app.services.feedback_service import feedback_service
    return feedback_service.submit_feedback(payload)


def _tool_train_ltr_model() -> dict:
    from ai_engine.training.ltr_pipeline import ltr_pipeline
    return ltr_pipeline.train()


def _tool_get_analytics() -> dict:
    from backend.app.services.feedback_service import feedback_service
    return feedback_service.get_feedback_analytics()


# ---------------------------------------------------------------------------
# Stub handlers for future external integrations
# ---------------------------------------------------------------------------

def _stub(*args, **kwargs) -> None:
    return None


# ---------------------------------------------------------------------------
# Registry Bootstrap
# ---------------------------------------------------------------------------

def _build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    # Internal tools
    reg.register_tool(
        name="parse_cv",
        description="Parse a resume file (PDF/DOCX) into plain text.",
        handler=_tool_parse_cv,
        required_role="any",
        input_schema={"file_bytes": "bytes", "filename": "str"},
        tags=["cv", "parsing"],
    )
    reg.register_tool(
        name="extract_skills",
        description="Extract skills from CV text using the HireMind skill taxonomy.",
        handler=_tool_extract_skills,
        required_role="any",
        input_schema={"text": "str"},
        tags=["cv", "skills"],
    )
    reg.register_tool(
        name="score_candidate",
        description="Run the full 6-stage Hybrid RAG scoring pipeline for a candidate.",
        handler=_tool_score_candidate,
        required_role="recruiter",
        input_schema={
            "candidate_text": "str", "candidate_skills": "list",
            "job_title": "str", "job_description": "str", "required_skills": "list",
        },
        tags=["matching", "scoring", "copilot"],
    )
    reg.register_tool(
        name="evaluate_hiring_rules",
        description="Evaluate a candidate against hiring rules for eligibility.",
        handler=_tool_evaluate_hiring_rules,
        required_role="recruiter",
        input_schema={
            "candidate_name": "str", "cv_text": "str",
            "candidate_skills": "list", "years_of_experience": "int",
        },
        tags=["compliance", "rules"],
    )
    reg.register_tool(
        name="submit_feedback",
        description="Record a recruiter decision (accept/reject) for a candidate.",
        handler=_tool_submit_feedback,
        required_role="recruiter",
        input_schema={"payload": "dict"},
        tags=["feedback", "learning"],
    )
    reg.register_tool(
        name="train_ltr_model",
        description="Retrain the LightGBM LambdaMART Learning-to-Rank model.",
        handler=_tool_train_ltr_model,
        required_role="admin",
        input_schema={},
        tags=["ltr", "training", "admin"],
    )
    reg.register_tool(
        name="get_analytics",
        description="Retrieve comprehensive recruiter feedback analytics.",
        handler=_tool_get_analytics,
        required_role="recruiter",
        input_schema={},
        tags=["analytics", "feedback"],
    )

    # Future stub integrations
    for name, desc, tags in [
        ("ats_push_candidate", "Push candidate data to an ATS system (e.g., Greenhouse, Lever).", ["ats", "integration"]),
        ("linkedin_profile_fetch", "Fetch a candidate's LinkedIn profile data.", ["linkedin", "integration"]),
        ("calendar_schedule_interview", "Schedule an interview via connected calendar system.", ["calendar", "interview"]),
        ("email_send_notification", "Send an automated email notification to a candidate.", ["email", "notification"]),
        ("hr_platform_sync", "Sync hiring data with an HR platform (e.g., Workday, BambooHR).", ["hr", "integration"]),
    ]:
        reg.register_tool(
            name=name,
            description=desc,
            handler=_stub,
            required_role="admin",
            input_schema={},
            tags=tags,
            is_stub=True,
        )

    return reg


# Singleton
tool_registry = _build_registry()
