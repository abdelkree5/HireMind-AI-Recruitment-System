from __future__ import annotations
import re
import numpy as np
from dataclasses import dataclass, field
from math import ceil

from ai_engine.skills import SkillExtractor
from ai_engine.role_requirements import build_role_requirements, generate_dynamic_roles, RoleRequirements

# Attempt to import from backend schemas, fallback to dataclass for offline testing/validation
try:
    from backend.app.schemas import CandidateMatchResponse
except ImportError:
    @dataclass
    class CandidateMatchResponse:
        job_title: str
        match_percentage: float
        ranking: int | None = None
        similarity: float = 0.0
        skill_score: float = 0.0
        title_score: float = 0.0
        missing_skills: list[str] = field(default_factory=list)
        matched_skills: list[str] = field(default_factory=list)
        evidence: dict[str, str] = field(default_factory=dict)
        skill_levels: dict[str, str] = field(default_factory=dict)
        missing_skills_by_group: dict[str, list[str]] = field(default_factory=dict)
        reason: str = ""
        confidence_score: float = 0.0
        match_level: str = "Medium"
        feedback: str = ""
        recommendation: str = ""
        score_breakdown: dict[str, float] = field(default_factory=dict)
        logs: list[str] = field(default_factory=list)


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


@dataclass
class CandidateSkillProfile:
    raw_skills: list[str] = field(default_factory=list)
    normalized_skills: list[str] = field(default_factory=list)
    skill_levels: dict[str, str] = field(default_factory=dict)
    skill_evidence: dict[str, str] = field(default_factory=dict)
    grouped_skills: dict[str, list[str]] = field(default_factory=dict)
    normalized_text: str = ""


@dataclass
class RoleAnalysisResult:
    role_name: str
    required_skills: list[str]
    advanced_skills: list[str]
    normalized_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    penalties: list[str] = field(default_factory=list)
    skill_levels: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    match_level: str = "Low"
    composite_score: float = 0.0
    priority_score: float = 0.0
    reason: str = ""


class CandidateReasoningEngine:
    def infer_seniority(self, text: str) -> str:
        years = self.extract_years_of_experience(text)
        lowered = text.lower()
        if any(token in lowered for token in ["principal", "staff", "lead", "senior"]) or years >= 7:
            return "Senior"
        if any(token in lowered for token in ["junior", "intern", "entry"]) or years <= 2:
            return "Junior"
        return "Mid"

    def infer_domain(self, skills: list[str], text: str) -> str:
        skill_set = {s.lower() for s in skills}
        lowered = text.lower()
        if any(s in skill_set for s in ["kubernetes", "terraform", "aws", "monitoring"]):
            return "devops"
        if any(s in skill_set for s in ["python", "fastapi", "django", "rest api"]):
            return "backend_ai"
        if any(s in lowered for s in ["telecom", "network", "routing", "switching"]):
            return "telecom_network"
        return "general"

    def extract_years_of_experience(self, text: str) -> int:
        explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", text.lower())]
        if explicit: 
            return max(explicit)
        spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", text.lower())
        if spans:
            return min(10, len(spans) * 2)
        return 0


# Private Helper functions
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


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


def _advanced_coverage(matched: list[str], advanced_skills: list[str]) -> float:
    if not advanced_skills:
        return 0.0
    return len([skill for skill in advanced_skills if skill in matched]) / len(advanced_skills)


def _split_weighted_buckets(required_skills: list[str]) -> tuple[list[str], list[str], list[str]]:
    if not required_skills:
        return [], [], []
    core_count = max(1, ceil(len(required_skills) * 0.6))
    secondary_count = ceil(len(required_skills) * 0.3)
    if core_count + secondary_count > len(required_skills):
        secondary_count = max(0, len(required_skills) - core_count)
    core = required_skills[:core_count]
    secondary = required_skills[core_count : core_count + secondary_count]
    bonus = required_skills[core_count + secondary_count :]
    return core, secondary, bonus


def _ratio(bucket: list[str], candidate_set: set[str]) -> float:
    if not bucket:
        return 0.0
    hits = sum(1 for skill in bucket if skill in candidate_set)
    return hits / len(bucket)


def _infer_candidate_seniority(years_of_experience: int) -> str:
    if years_of_experience >= 7:
        return "senior"
    if years_of_experience <= 2:
        return "junior"
    return "mid"


def _infer_role_seniority(role_name: str) -> str:
    lowered = role_name.lower()
    if any(token in lowered for token in ["senior", "lead", "principal", "staff"]):
        return "senior"
    if any(token in lowered for token in ["junior", "intern", "entry"]):
        return "junior"
    return "mid"


def _infer_candidate_domain(skills: set[str]) -> str:
    if any(skill in skills for skill in ["kubernetes", "terraform", "aws", "monitoring", "ci/cd"]):
        return "devops"
    if any(skill in skills for skill in ["python", "fastapi", "rest api", "django", "flask"]):
        return "backend_ai"
    if any(skill in skills for skill in ["telecommunications", "networking", "routing", "switching"]):
        return "telecom_network"
    if any(skill in skills for skill in ["azure", "gcp", "cloud architecture"]):
        return "cloud_platform"
    return "general"


def build_candidate_skill_profile(text: str, extractor: SkillExtractor | None = None) -> CandidateSkillProfile:
    extractor = extractor or SkillExtractor()
    grouped, evidence, depth_by_skill = extractor.extract_grouped_with_metadata(text)

    raw_skills: list[str] = []
    for group_name in grouped:
        raw_skills.extend(grouped[group_name])

    # De-duplicate raw skills
    deduped = []
    seen = set()
    for s in raw_skills:
        low = s.lower().strip()
        if low not in seen:
            seen.add(low)
            deduped.append(s)

    return CandidateSkillProfile(
        raw_skills=deduped,
        normalized_skills=deduped,
        skill_levels=depth_by_skill,
        skill_evidence=evidence,
        grouped_skills=grouped,
        normalized_text=" ".join((text or "").split()).lower(),
    )


def analyze_role_fit(
    candidate: CandidateSkillProfile,
    requirements: RoleRequirements,
    years_of_experience: int,
    leadership_score: float,
) -> RoleAnalysisResult:
    normalized_candidate = {s.lower() for s in candidate.normalized_skills}

    required_skills = [s.lower() for s in requirements.required_skills]
    advanced_skills = [s.lower() for s in requirements.advanced_skills]

    matched_skills = [skill for skill in required_skills if skill in normalized_candidate]
    missing_skills = [skill for skill in required_skills if skill not in matched_skills]

    confidence = (len(matched_skills) / len(required_skills)) if required_skills else 0.0

    core_skills, secondary_skills, bonus_skills = _split_weighted_buckets(required_skills)
    core_ratio = _ratio(core_skills, normalized_candidate)
    secondary_ratio = _ratio(secondary_skills, normalized_candidate)
    bonus_ratio = _ratio(bonus_skills, normalized_candidate)

    active_weight = 0.0
    if core_skills:
        active_weight += 0.6
    if secondary_skills:
        active_weight += 0.3
    if bonus_skills:
        active_weight += 0.1

    weighted_score = (0.6 * core_ratio) + (0.3 * secondary_ratio) + (0.1 * bonus_ratio)
    if active_weight > 0:
        weighted_score = weighted_score / active_weight

    final_score = min(confidence, weighted_score)
    penalties = []

    missing_core = [skill for skill in core_skills if skill not in normalized_candidate]
    if missing_core:
        core_miss_ratio = len(missing_core) / max(1, len(core_skills))
        if core_miss_ratio > 0.5:
            final_score = min(final_score, 0.55)
            penalties.append(f"Missing {len(missing_core)}/{len(core_skills)} core skills (max 55%)")
        elif core_miss_ratio > 0.25:
            final_score = min(final_score, 0.75)
            penalties.append(f"Missing {len(missing_core)}/{len(core_skills)} core skills (max 75%)")

    candidate_level = _infer_candidate_seniority(years_of_experience)
    role_level = _infer_role_seniority(requirements.role_name)
    if candidate_level != role_level:
        final_score -= 0.05
        penalties.append("Seniority mismatch (-5%)")

    candidate_domain = _infer_candidate_domain(normalized_candidate)
    if requirements.domain and candidate_domain != "general" and candidate_domain != requirements.domain:
        final_score -= 0.05
        penalties.append("Domain mismatch (-5%)")

    if confidence < 0.40:
        final_score = min(final_score, 0.55)
    if missing_skills and confidence < 0.50:
        final_score = min(final_score, 0.60)

    final_score = max(0.0, min(1.0, final_score))
    composite_score = final_score
    priority_score = min(1.0, composite_score + min(1.0, years_of_experience / 12.0) * 0.05 + min(1.0, leadership_score) * 0.05)

    if composite_score >= 0.75 and confidence >= 0.70:
        match_level = "High"
    elif composite_score >= 0.50:
        match_level = "Medium"
    else:
        match_level = "Low"

    evidence = {}
    for skill in matched_skills:
        sentence = candidate.skill_evidence.get(skill)
        if sentence:
            evidence[skill] = sentence

    reason_parts = [f"{requirements.role_name} is a {match_level.lower()} fit"]
    if matched_skills:
        reason_parts.append(f"matched skills: {', '.join(matched_skills[:5])}")
    if evidence:
        snippets = [f"{skill}: {sentence[:110]}" for skill, sentence in list(evidence.items())[:3]]
        reason_parts.append(f"evidence: {' | '.join(snippets)}")
    if missing_skills:
        reason_parts.append(f"missing: {', '.join(missing_skills[:3])}")
    if penalties:
        reason_parts.append(f"penalties: {', '.join(penalties)}")

    return RoleAnalysisResult(
        role_name=requirements.role_name,
        required_skills=required_skills,
        advanced_skills=advanced_skills,
        normalized_skills=candidate.normalized_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        penalties=penalties,
        skill_levels=candidate.skill_levels,
        evidence=evidence,
        confidence=round(confidence * 100, 2),
        match_level=match_level,
        composite_score=round(composite_score * 100, 2),
        priority_score=round(priority_score * 100, 2),
        reason=". ".join(reason_parts) + ".",
    )


def build_candidate_insight(cv_text: str) -> CandidateInsight:
    cleaned = (cv_text or "").strip()
    if not cleaned:
        raise ValueError("Uploaded file is empty or unreadable.")

    extractor = SkillExtractor()
    profile = build_candidate_skill_profile(cleaned, extractor=extractor)

    engine = CandidateReasoningEngine()
    years = engine.extract_years_of_experience(cleaned)
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

    generated_roles = generate_dynamic_roles(insight.primary_domain, insight.secondary_domains, insight.skills, insight.level)
    selected_roles = generated_roles[: max(1, min(top_k, len(generated_roles)))]

    analyses = []
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

    matches = []
    for rank, analysis in enumerate(analyses, start=1):
        matches.append(
            CandidateMatchResponse(
                job_title=analysis.role_name,
                match_percentage=round(analysis.composite_score, 2),
                ranking=rank,
                similarity=round(analysis.composite_score / 100.0, 4),
                skill_score=round(analysis.confidence / 100.0, 4),
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
                    "confidence": round(analysis.confidence / 100.0, 4),
                    "composite": round(analysis.composite_score / 100.0, 4),
                    "priority": round(analysis.priority_score / 100.0, 4),
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
