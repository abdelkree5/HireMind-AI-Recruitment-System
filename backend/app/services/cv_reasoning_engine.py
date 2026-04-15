from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.schemas import CandidateMatchResponse
from backend.app.services.role_requirements import build_role_requirements, generate_dynamic_roles
from backend.app.services.scoring_engine import RoleAnalysisResult, analyze_role_fit
from backend.app.services.skill_extractor import SkillExtractor
from backend.app.services.skill_mapper import CandidateSkillProfile, build_candidate_skill_profile


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _extract_years_of_experience(text: str) -> int:
    normalized = text.lower()
    explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", normalized)]
    if explicit:
        return max(explicit)

    spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", normalized)
    if spans:
        return min(10, len(spans) * 2)

    return 0


def _score_leadership(text: str) -> float:
    normalized = text.lower()
    keywords = ["lead", "led", "manager", "managed", "owner", "principal", "architect", "mentored"]
    hits = sum(normalized.count(token) for token in keywords)
    return min(1.0, hits / 4.0)


def _score_project_depth(text: str) -> float:
    normalized = text.lower()
    depth_terms = ["designed", "implemented", "built", "deployed", "integrated", "optimized", "maintained", "production", "architecture", "end-to-end"]
    hits = sum(normalized.count(token) for token in depth_terms)
    return min(1.0, hits / 8.0)


@dataclass
class CandidateInsight:
    inferred_headline: str
    level: str
    years_of_experience: int
    primary_domain: str
    secondary_domains: list[str]
    skills: list[str]
    skill_levels: dict[str, str]
    skill_evidence: dict[str, str]
    leadership_score: float
    project_depth_score: float
    normalized_text: str


@dataclass
class RecommendationResult:
    total_catalog: int
    matches: list[CandidateMatchResponse]


def _infer_headline(cv_text: str) -> str:
    lines = [line.strip(" -•\t") for line in cv_text.splitlines() if line.strip()]
    if not lines:
        return "CV Profile"

    blocked_labels = {"personal", "information", "curriculum vitae", "emailaddress", "telephone", "date", "position", "employer", "duties", "address", "idcardno"}

    def is_label_line(value: str) -> bool:
        lowered = re.sub(r"[^a-z0-9 ]", "", value.lower()).strip()
        return lowered in blocked_labels or len(lowered.split()) <= 1

    def clean_line(value: str) -> str:
        cleaned = re.sub(r"^[\s:\-–—|]+", "", value).strip()
        cleaned = re.sub(r"^(?:full\s*name(?:s)?|name|email\s*address|email|phone|telephone|mobile|position|title)\s*[:\-–—]*\s*", "", cleaned, flags=re.IGNORECASE)
        return re.sub(r"^[\s:\-–—|]+", "", cleaned).strip()

    role_hints = ("engineer", "developer", "scientist", "analyst", "architect", "specialist", "devops", "network", "telecom", "ai", "ml")

    for line in lines[:14]:
        if is_label_line(line):
            continue
        if any(hint in line.lower() for hint in role_hints):
            candidate = clean_line(line)
            if candidate:
                return candidate

    for line in lines[:20]:
        if is_label_line(line):
            continue
        candidate = clean_line(line)
        if candidate and 3 <= len(candidate.split()) <= 18:
            return candidate

    fallback = clean_line(lines[0])
    return fallback or "CV Profile"


def _domain_scores(skills: list[str], text: str) -> dict[str, float]:
    normalized_text = _normalize(text)
    skill_set = {skill.lower() for skill in skills}
    domain_signals = {
        "backend_ai": {"python", "fastapi", "docker", "machine learning", "rest api"},
        "devops": {"kubernetes", "terraform", "aws", "monitoring", "ci/cd", "infrastructure automation"},
        "ai_nlp": {"nlp", "transformers", "sentence-transformers", "llm", "rag", "machine learning"},
        "data_ml": {"python", "sql", "pandas", "numpy", "feature engineering", "statistics"},
        "telecom_network": {"telecommunications", "telecom", "networking", "routing", "switching", "fiber optics", "wimax", "noc"},
        "cloud_platform": {"aws", "azure", "gcp", "kubernetes", "terraform", "cloud architecture"},
    }
    domain_keywords = {
        "backend_ai": ["backend", "api", "inference", "serving", "fastapi", "model"],
        "devops": ["devops", "ci/cd", "deployment", "infrastructure", "automation", "sre"],
        "ai_nlp": ["nlp", "machine learning", "deep learning", "llm", "rag", "transformer"],
        "data_ml": ["data", "analytics", "dashboard", "feature", "statistics"],
        "telecom_network": ["telecom", "network", "wan", "lan", "fiber", "wimax", "microwave", "noc"],
        "cloud_platform": ["cloud", "aws", "azure", "gcp", "kubernetes", "terraform"],
    }
    scores: dict[str, float] = {}
    for domain, signals in domain_signals.items():
        signal_hits = sum(1 for signal in signals if signal in skill_set)
        keyword_hits = sum(1 for keyword in domain_keywords.get(domain, []) if keyword in normalized_text)
        scores[domain] = (signal_hits * 2.5) + keyword_hits

    if {"python", "fastapi"}.issubset(skill_set) and ("docker" in skill_set or "machine learning" in skill_set):
        scores["backend_ai"] = scores.get("backend_ai", 0.0) + 4.0
    if {"kubernetes", "terraform"}.issubset(skill_set) and ({"aws", "azure", "gcp"} & skill_set):
        scores["devops"] = scores.get("devops", 0.0) + 5.0
    if {"telecommunications", "fiber optics"} & skill_set and ({"networking", "routing", "switching"} & skill_set):
        scores["telecom_network"] = scores.get("telecom_network", 0.0) + 3.0
    return scores


def _infer_domains(skills: list[str], text: str) -> tuple[str, list[str]]:
    scores = _domain_scores(skills, text)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ordered or ordered[0][1] <= 0:
        return "backend_ai", []
    primary = ordered[0][0]
    secondary = [domain for domain, score in ordered[1:] if score >= max(2.0, ordered[0][1] * 0.45)][:2]
    return primary, secondary


def _infer_level(years: int, leadership_score: float, project_depth_score: float, text: str) -> str:
    normalized = text.lower()
    if years >= 7 or leadership_score >= 0.65 or any(token in normalized for token in ["principal", "staff"]):
        return "Senior"
    if years >= 3 or leadership_score >= 0.3 or project_depth_score >= 0.45 or "senior" in normalized:
        return "Mid"
    return "Junior"


def build_candidate_insight(cv_text: str) -> CandidateInsight:
    cleaned = (cv_text or "").strip()
    if not cleaned:
        raise ValueError("Uploaded file is empty or unreadable.")

    extractor = SkillExtractor()
    profile = build_candidate_skill_profile(cleaned, extractor=extractor)

    years = _extract_years_of_experience(cleaned)
    leadership_score = _score_leadership(cleaned)
    project_depth_score = _score_project_depth(cleaned)
    if profile.skill_levels:
        skill_depth_score = sum(1.0 if value == "Advanced" else 0.6 if value == "Intermediate" else 0.25 for value in profile.skill_levels.values()) / max(1, len(profile.skill_levels))
        project_depth_score = min(1.0, (project_depth_score * 0.7) + (skill_depth_score * 0.3))
    level = _infer_level(years, leadership_score, project_depth_score, cleaned)
    primary_domain, secondary_domains = _infer_domains(profile.normalized_skills, cleaned)

    return CandidateInsight(
        inferred_headline=_infer_headline(cleaned),
        level=level,
        years_of_experience=years,
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        skills=profile.normalized_skills,
        skill_levels=profile.skill_levels,
        skill_evidence=profile.skill_evidence,
        leadership_score=leadership_score,
        project_depth_score=project_depth_score,
        normalized_text=profile.normalized_text,
    )


def recommend_job_titles_from_cv_text(cv_text: str, top_k: int = 5) -> RecommendationResult:
    insight = build_candidate_insight(cv_text)
    print(f"[VALIDATION] Extracted skills: {', '.join(insight.skills) if insight.skills else 'none'}")
    print(f"[VALIDATION] Domain detected: {insight.primary_domain} | secondary: {', '.join(insight.secondary_domains) if insight.secondary_domains else 'none'}")

    generated_roles = generate_dynamic_roles(insight.primary_domain, insight.secondary_domains, insight.skills, insight.level)
    selected_roles = generated_roles[: max(1, min(top_k, len(generated_roles)))]

    analyses: list[RoleAnalysisResult] = []
    for role_name in selected_roles:
        requirements = build_role_requirements(role_name, insight.primary_domain)
        candidate_profile = CandidateSkillProfile(
            raw_skills=insight.skills,
            normalized_skills=insight.skills,
            skill_levels=insight.skill_levels,
            skill_evidence=insight.skill_evidence,
            grouped_skills={},
            normalized_text=insight.normalized_text,
        )
        analysis = analyze_role_fit(
            candidate=candidate_profile,
            requirements=requirements,
            years_of_experience=insight.years_of_experience,
            leadership_score=insight.leadership_score,
        )
        analyses.append(analysis)

    analyses.sort(key=lambda item: (item.priority_score, item.composite_score, item.confidence), reverse=True)

    matches: list[CandidateMatchResponse] = []
    for rank, analysis in enumerate(analyses, start=1):
        matches.append(
            CandidateMatchResponse(
                job_title=analysis.role_name,
                match_percentage=round(analysis.composite_score, 2),
                ranking=rank,
                similarity=round(analysis.composite_score, 2),
                skill_score=round(analysis.confidence, 2),
                title_score=round(insight.project_depth_score * 100, 2),
                missing_skills=analysis.missing_skills,
                matched_skills=analysis.matched_skills,
                evidence=analysis.evidence,
                skill_levels=analysis.skill_levels,
                missing_skills_by_group={"required": analysis.missing_skills},
                reason=analysis.reason,
                confidence_score=round(analysis.confidence, 2),
                match_level=analysis.match_level,
                feedback=analysis.reason,
                score_breakdown={
                    "confidence": round(analysis.confidence, 2),
                    "composite": round(analysis.composite_score, 2),
                    "priority": round(analysis.priority_score, 2),
                    "leadership": round(insight.leadership_score, 4),
                    "depth": round(insight.project_depth_score, 4),
                },
                logs=[
                    "Mode: context-aware evidence-based CV analysis",
                    f"Inferred level: {insight.level}",
                    f"Primary domain: {insight.primary_domain}",
                    f"Normalized skills: {', '.join(insight.skills) if insight.skills else 'none'}",
                    f"Skill levels: {insight.skill_levels if insight.skill_levels else {}}",
                    f"Match level: {analysis.match_level}",
                ],
            )
        )

    return RecommendationResult(total_catalog=len(matches), matches=matches)
