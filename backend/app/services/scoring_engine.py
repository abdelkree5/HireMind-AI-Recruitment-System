from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from backend.app.services.role_requirements import RoleRequirements
from backend.app.services.skill_mapper import CandidateSkillProfile
from backend.app.services.skill_normalizer import normalize_skill


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


def analyze_role_fit(
    candidate: CandidateSkillProfile,
    requirements: RoleRequirements,
    years_of_experience: int,
    leadership_score: float,
) -> RoleAnalysisResult:
    normalized_candidate = {normalize_skill(skill) for skill in candidate.normalized_skills}

    required_skills: list[str] = []
    seen_required: set[str] = set()
    for skill in requirements.required_skills:
        normalized_skill = normalize_skill(skill)
        if normalized_skill not in seen_required:
            seen_required.add(normalized_skill)
            required_skills.append(normalized_skill)

    advanced_skills: list[str] = []
    seen_advanced: set[str] = set()
    for skill in requirements.advanced_skills:
        normalized_skill = normalize_skill(skill)
        if normalized_skill not in seen_advanced:
            seen_advanced.add(normalized_skill)
            advanced_skills.append(normalized_skill)

    matched_skills = [skill for skill in required_skills if skill in normalized_candidate]
    missing_skills = [skill for skill in required_skills if skill not in matched_skills]

    confidence = (len(matched_skills) / len(required_skills)) if required_skills else 0.0
    advanced_overlap = _advanced_coverage(matched_skills, advanced_skills)

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

    # Strict base score requested: matched / required, then bounded by weighted quality.
    final_score = min(confidence, weighted_score)
    penalties: list[str] = []

    missing_core = [skill for skill in core_skills if skill not in normalized_candidate]
    if missing_core:
        final_score = min(final_score, 0.60)
        penalties.append("Missing core skill cap (max 60%)")

    candidate_level = _infer_candidate_seniority(years_of_experience)
    role_level = _infer_role_seniority(requirements.role_name)
    if candidate_level != role_level:
        final_score -= 0.20
        penalties.append("Seniority mismatch (-20%)")

    candidate_domain = _infer_candidate_domain(normalized_candidate)
    if requirements.domain and candidate_domain != "general" and candidate_domain != requirements.domain:
        final_score -= 0.15
        penalties.append("Domain mismatch (-15%)")

    # Weak matches should never look high.
    if confidence < 0.70:
        final_score = min(final_score, 0.69)

    if missing_skills and confidence < 0.80:
        final_score = min(final_score, 0.65)

    final_score = max(0.0, min(1.0, final_score))
    
    # Calculate depth score based on skill levels
    depth_score = 0.0
    advanced_count = 0
    intermediate_count = 0
    if candidate.skill_levels:
        for value in candidate.skill_levels.values():
            if value == "Advanced":
                advanced_count += 1
            elif value == "Intermediate":
                intermediate_count += 1
        depth_score = (advanced_count * 1.0 + intermediate_count * 0.6) / max(1, len(candidate.skill_levels))
    
    composite_score = final_score
    priority_score = min(1.0, composite_score + min(1.0, years_of_experience / 12.0) * 0.05 + min(1.0, leadership_score) * 0.05)
    
    # Smart match level determination:
    # High: strong confidence + advanced skills OR experienced + good match
    # Medium: moderate confidence OR junior level
    # Low: poor fit
    if composite_score >= 0.8 and confidence >= 0.85 and not missing_core:
        match_level = "High"
    elif composite_score >= 0.5:
        match_level = "Medium"
    else:
        match_level = "Low"

    evidence: dict[str, str] = {}
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

    print(f"[DEBUG][{requirements.role_name}] normalized_skills: {', '.join(candidate.normalized_skills) if candidate.normalized_skills else 'none'}")
    print(f"[DEBUG][{requirements.role_name}] required_skills: {', '.join(required_skills) if required_skills else 'none'}")
    print(f"[DEBUG][{requirements.role_name}] matched_skills: {', '.join(matched_skills) if matched_skills else 'none'}")
    print(f"[DEBUG][{requirements.role_name}] missing_skills: {', '.join(missing_skills) if missing_skills else 'none'}")
    print(f"[DEBUG][{requirements.role_name}] skill_levels: {candidate.skill_levels if candidate.skill_levels else {}}")

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
