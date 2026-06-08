from __future__ import annotations

from collections import Counter

from backend.app.schemas import (
    CareerGrowthPlan,
    FullCvAnalysisResponse,
    ProfileSummary,
    RoleAnalysisItem,
    StrengthWeaknessReport,
)
from ai_engine.parser import ResumeParser
from ai_engine.reasoning import CandidateReasoningEngine
# Using bridge for recommendation if it's not fully moved yet
from ai_engine.reasoning import recommend_job_titles_from_cv_text, build_candidate_insight


def _domain_label(domain: str) -> str:
    mapping = {
        "backend_ai": "Backend AI Engineering",
        "devops": "DevOps / Platform Engineering",
        "ai_nlp": "NLP / Language AI",
        "data_ml": "Data & ML Engineering",
        "telecom_network": "Telecom Engineering",
        "cloud_platform": "Cloud Infrastructure",
    }
    return mapping.get(domain, domain.title())


def _profile_description(level: str, domain: str, skills: list[str]) -> str:
    spotlight = ", ".join(skills[:5]) if skills else "core engineering skills"
    return (
        f"{level} candidate focused on {_domain_label(domain)} with practical evidence in {spotlight}. "
        "Profile indicates implementation readiness for production-oriented technical roles."
    )


def _build_growth_plan(level: str, roles: list[RoleAnalysisItem]) -> CareerGrowthPlan:
    gap_counter: Counter[str] = Counter()
    for role in roles:
        for skill in role.missing_skills:
            gap_counter[skill] += 1

    priorities = [skill for skill, _ in gap_counter.most_common(6)]
    if not priorities:
        priorities = ["advanced system design", "production reliability", "model evaluation"]

    if level == "Junior":
        roadmap = [
            "Build one solid end-to-end project for each target role area.",
            "Strengthen core technical foundations and role-specific tools.",
            "Deploy at least one real service and document architecture decisions.",
            "Add evaluation metrics and production monitoring to your projects.",
            "Iterate portfolio quality with measurable improvements.",
        ]
    elif level == "Senior":
        roadmap = [
            "Lead architecture decisions across model + backend boundaries.",
            "Standardize evaluation and deployment quality gates for teams.",
            "Mentor delivery practices for production AI systems.",
            "Drive reliability/cost optimization initiatives.",
            "Expand into strategic ownership for high-impact AI capabilities.",
        ]
    else:
        roadmap = [
            "Close the highest-frequency skill gaps from target roles.",
            "Upgrade one existing project into production-grade quality.",
            "Add CI/CD, testing, and observability to AI services.",
            "Build a reusable architecture pattern for future projects.",
            "Publish concise case studies showing measurable outcomes.",
        ]

    return CareerGrowthPlan(
        next_learning_priorities=priorities,
        roadmap_steps=roadmap,
    )


def _build_strengths_and_weaknesses(skills: list[str], roles: list[RoleAnalysisItem]) -> StrengthWeaknessReport:
    strengths: list[str] = []
    weaknesses: list[str] = []
    normalized = {skill.lower() for skill in skills}

    if any(skill in normalized for skill in ["routing", "switching", "tcp/ip", "networking"]):
        strengths.append("Strong networking fundamentals with practical operations exposure")
    if any(skill in normalized for skill in ["telecommunications", "fiber optics", "wimax", "microwave links", "microwave"]):
        strengths.append("Hands-on telecom field and integration signal is clearly present")
    if any(skill in normalized for skill in ["linux", "windows server", "active directory"]):
        strengths.append("Good system administration baseline for infrastructure roles")

    if any(skill in normalized for skill in ["python", "fastapi"]):
        strengths.append("Strong Python + API implementation baseline for AI/backend integration")
    if any(skill in normalized for skill in ["nlp", "transformers", "sentence-transformers"]):
        strengths.append("Clear NLP-oriented profile with modern language-model ecosystem exposure")
    if any(skill in normalized for skill in ["scikit-learn", "machine learning"]):
        strengths.append("Applied ML problem-solving signal in model-driven workflows")

    if not strengths:
        strengths.append("Foundational technical signal present with room for specialization depth")

    gap_counter: Counter[str] = Counter()
    for role in roles:
        for skill in role.missing_skills:
            gap_counter[skill] += 1

    for skill, _ in gap_counter.most_common(5):
        weaknesses.append(f"Needs deeper proficiency in {skill}")

    if not weaknesses:
        weaknesses.append("No critical recurring gap detected across the generated top roles")

    return StrengthWeaknessReport(strengths=strengths, weaknesses=weaknesses)


def analyze_full_cv_report(file_bytes: bytes, filename: str) -> FullCvAnalysisResponse:
    parser = ResumeParser()
    text = parser.parse(file_bytes, filename)
    if not text.strip():
        raise ValueError("Uploaded file is empty or unreadable.")

    insight = build_candidate_insight(text)
    recommendation = recommend_job_titles_from_cv_text(text, top_k=5)

    top_roles: list[RoleAnalysisItem] = []
    for match in recommendation.matches:
        top_roles.append(
            RoleAnalysisItem(
                role_name=match.job_title,
                match_level=match.match_level,
                confidence_score=round(match.confidence_score, 4),
                reason=match.reason or match.feedback,
                matched_skills=getattr(match, "matched_skills", []),
                evidence=getattr(match, "evidence", {}),
                skill_levels=getattr(match, "skill_levels", {}),
                missing_skills=match.missing_skills,
                missing_skills_by_group=match.missing_skills_by_group,
            )
        )

    profile = ProfileSummary(
        candidate_level=insight.level,
        main_domain=_domain_label(insight.primary_domain),
        inferred_headline=insight.inferred_headline,
        short_description=_profile_description(insight.level, insight.primary_domain, insight.skills),
        key_skills=insight.skills[:12],
        years_of_experience=insight.years_of_experience,
    )

    growth_plan = _build_growth_plan(insight.level, top_roles)
    strength_weakness = _build_strengths_and_weaknesses(insight.skills, top_roles)

    logs = [
        "Mode: full reasoning-based CV analysis report",
        "No posted jobs used",
        "No cosine similarity ranking against fixed catalog",
        f"Inferred level: {insight.level}",
        f"Main domain: {insight.primary_domain}",
    ]

    return FullCvAnalysisResponse(
        profile_summary=profile,
        top_roles=top_roles,
        career_growth_plan=growth_plan,
        strengths_vs_weaknesses=strength_weakness,
        analysis_logs=logs,
    )
