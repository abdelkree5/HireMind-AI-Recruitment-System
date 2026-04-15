from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from backend.app.services.skill_extractor import SkillExtractor


SYNONYMS: dict[str, str] = {
    "python3": "python",
    "fast api": "fastapi",
    "postgres": "postgresql",
}


def normalize_skill(skill: str) -> str:
    value = (skill or "").strip().lower()
    value = SYNONYMS.get(value, value)
    value = value.replace("/", "/")
    return value


def normalize_skills(skills: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        normalized = normalize_skill(skill)
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def build_reason(matched_skills: list[str], missing_skills: list[str]) -> str:
    matched_text = ", ".join(matched_skills)
    if matched_text:
        reason = f"You match {len(matched_skills)}/{len(matched_skills) + len(missing_skills)} required skills ({matched_text})"
    else:
        reason = f"You match 0/{len(missing_skills)} required skills"
    if missing_skills:
        reason += f". Missing: {', '.join(missing_skills)}"
    return reason


def build_recommendation(score: float) -> str:
    if score > 0.8:
        return "Strong Match"
    if score >= 0.5:
        return "متوسط"
    return "ضعيف"


@dataclass
class JobMatchResult:
    score: float
    match_level: str
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    reason: str = ""
    recommendation: str = ""


def match_job_to_candidate(
    job_skills: list[str],
    candidate_skills: list[str],
    candidate_level: str | None = None,
    job_level: str | None = None,
    candidate_domain: str | None = None,
    job_domain: str | None = None,
) -> JobMatchResult:
    normalized_job = normalize_skills(job_skills)
    normalized_candidate = normalize_skills(candidate_skills)

    matched_skills = [skill for skill in normalized_job if skill in normalized_candidate]
    missing_skills = [skill for skill in normalized_job if skill not in matched_skills]

    total_required = len(normalized_job)
    base_ratio = (len(matched_skills) / total_required) if total_required else 0.0

    # Weighted split (core 60%, secondary 30%, bonus 10%) using job skill order as priority.
    core_count = max(1, ceil(total_required * 0.6)) if total_required else 0
    secondary_count = ceil(total_required * 0.3) if total_required else 0
    if core_count + secondary_count > total_required:
        secondary_count = max(0, total_required - core_count)

    core_skills = normalized_job[:core_count]
    secondary_skills = normalized_job[core_count : core_count + secondary_count]
    bonus_skills = normalized_job[core_count + secondary_count :]

    def _ratio(bucket: list[str]) -> float:
        if not bucket:
            return 0.0
        hits = sum(1 for skill in bucket if skill in normalized_candidate)
        return hits / len(bucket)

    core_ratio = _ratio(core_skills)
    secondary_ratio = _ratio(secondary_skills)
    bonus_ratio = _ratio(bonus_skills)

    active_weight = 0.0
    if core_skills:
        active_weight += 0.6
    if secondary_skills:
        active_weight += 0.3
    if bonus_skills:
        active_weight += 0.1

    weighted_score = (
        (0.6 * core_ratio)
        + (0.3 * secondary_ratio)
        + (0.1 * bonus_ratio)
    )
    if active_weight > 0:
        weighted_score = weighted_score / active_weight

    # Keep score calculation strict with the required direct ratio.
    score = min(base_ratio, weighted_score)

    penalties: list[str] = []

    missing_core = [skill for skill in core_skills if skill not in normalized_candidate]
    if missing_core:
        score = min(score, 0.60)
        penalties.append("Missing core skill cap (max 60%)")

    if candidate_level and job_level and candidate_level.lower() != job_level.lower():
        score -= 0.20
        penalties.append("Seniority mismatch (-20%)")

    if (
        job_domain
        and candidate_domain
        and job_domain.lower() not in {"general", "unknown"}
        and candidate_domain.lower() not in {"general", "unknown"}
        and job_domain.lower() != candidate_domain.lower()
    ):
        score -= 0.15
        penalties.append("Domain mismatch (-15%)")

    # Prevent fake high scores for weak matches.
    if base_ratio < 0.70:
        score = min(score, 0.69)

    # Partial matches with missing required skills should stay realistic.
    if missing_skills and base_ratio < 0.80:
        score = min(score, 0.65)

    if score > 0.85 and len(matched_skills) < max(1, total_required - 1):
        score = 0.85

    score = max(0.0, min(1.0, score))
    match_level = "Strong Match" if score > 0.8 else "متوسط" if score >= 0.5 else "ضعيف"

    reason = build_reason(matched_skills, missing_skills)
    if penalties:
        reason += f". Penalties: {', '.join(penalties)}"

    return JobMatchResult(
        score=score,
        match_level=match_level,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        penalties=penalties,
        reason=reason,
        recommendation=build_recommendation(score),
    )


def extract_candidate_skills(text: str, skills: list[str] | None = None) -> list[str]:
    extractor = SkillExtractor()
    extracted = extractor.extract(text)
    if skills:
        extracted.extend(skills)
    return normalize_skills(extracted)