from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class RoleMatchResult:
    role_name: str
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    missing_skills_by_group: dict[str, list[str]] = field(default_factory=dict)
    confidence: float = 0.0
    composite: float = 0.0
    match_level: str = "Low"
    priority_score: float = 0.0
    reason: str = ""


_SYNONYM_GROUPS: dict[str, set[str]] = {
    "aws": {"aws", "amazon web services", "amazon web service"},
    "azure": {"azure", "microsoft azure"},
    "gcp": {"gcp", "google cloud platform", "google cloud"},
    "ci/cd": {"ci/cd", "ci cd", "continuous integration", "continuous deployment"},
    "docker": {"docker"},
    "kubernetes": {"kubernetes", "k8s"},
    "terraform": {"terraform"},
    "rest api": {"rest api", "restful api", "api"},
    "python": {"python", "python programming"},
    "fastapi": {"fastapi"},
    "nlp": {"nlp", "natural language processing"},
    "llm": {"llm", "large language model", "large language models"},
    "rag": {"rag", "retrieval augmented generation"},
    "transformers": {"transformers", "transformer"},
    "sentence-transformers": {"sentence-transformers", "sentence transformers"},
    "telecommunications": {"telecommunications", "telecom"},
    "network operations": {"network operations", "noc"},
    "microwave links": {"microwave links", "microwave"},
    "monitoring": {"monitoring", "observability"},
    "observability": {"observability", "monitoring"},
    "infrastructure automation": {"infrastructure automation", "automation of infrastructure"},
    "cloud architecture": {"cloud architecture", "multi-account architecture", "multi account architecture", "multi-account infrastructure"},
    "wan/lan": {"wan/lan", "wan", "lan"},
    "tcp/ip": {"tcp/ip", "tcpip"},
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def normalize_skill(skill: str) -> str:
    return normalize_text(skill).replace("-", " ")


def skill_variants(skill: str) -> set[str]:
    normalized = normalize_skill(skill)
    variants = {normalized}
    for canonical, alias_set in _SYNONYM_GROUPS.items():
        if normalized == canonical or normalized in alias_set:
            variants |= {normalize_skill(value) for value in alias_set}
            variants.add(canonical)
    return variants


def is_skill_covered(required_skill: str, candidate_set: set[str], normalized_text: str) -> bool:
    normalized_required = normalize_skill(required_skill)
    variants = skill_variants(normalized_required)
    if any(variant in candidate_set for variant in variants):
        return True
    if any(" " in variant and variant in normalized_text for variant in variants):
        return True
    if normalized_required == "monitoring" and "observability" in normalized_text:
        return True
    if normalized_required == "observability" and "monitoring" in normalized_text:
        return True
    if normalized_required in {"cloud architecture", "infrastructure automation"}:
        infrastructure_terms = ["multi-account", "multi account", "aws", "kubernetes", "terraform", "production"]
        action_terms = ["designed", "architected", "managed", "built", "owned", "deployed"]
        if any(term in normalized_text for term in infrastructure_terms) and any(term in normalized_text for term in action_terms):
            return True
    if "/" in normalized_required:
        parts = [normalize_skill(part) for part in normalized_required.split("/")]
        if any(part and part in normalized_text for part in parts):
            return True
    return False


def _depth_score(years_of_experience: int, project_depth_score: float, leadership_score: float) -> float:
    return min(
        1.0,
        (years_of_experience / 8.0) * 0.45
        + (project_depth_score * 0.4)
        + (leadership_score * 0.15),
    )


def compare_role_match(
    candidate_skills: list[str],
    required_skills: list[str],
    normalized_text: str,
    evidence_by_skill: dict[str, str] | None = None,
    skill_depths: dict[str, str] | None = None,
    years_of_experience: int = 0,
    leadership_score: float = 0.0,
    project_depth_score: float = 0.0,
    role_name: str = "",
) -> RoleMatchResult:
    candidate_set = {normalize_skill(skill) for skill in candidate_skills}
    ordered_required: list[str] = []
    seen_required: set[str] = set()
    for skill in required_skills:
        normalized = normalize_skill(skill)
        if normalized in seen_required:
            continue
        seen_required.add(normalized)
        ordered_required.append(skill)

    matched = [skill for skill in ordered_required if is_skill_covered(skill, candidate_set, normalized_text)]
    missing = [skill for skill in ordered_required if skill not in matched]

    confidence = (len(matched) / len(ordered_required)) if ordered_required else 0.0
    depth = _depth_score(years_of_experience, project_depth_score, leadership_score)
    composite = (0.85 * confidence) + (0.15 * depth)

    if confidence >= 0.7 and depth >= 0.35:
        match_level = "High"
    elif confidence >= 0.6 and depth >= 0.55 and years_of_experience >= 8 and leadership_score >= 0.35:
        match_level = "High"
    elif confidence >= 0.5 and depth >= 0.75 and level == "Senior":
        match_level = "High"
    elif confidence >= 0.4:
        match_level = "Medium"
    else:
        match_level = "Low"

    evidence_parts: list[str] = []
    if evidence_by_skill:
        for skill in matched[:3]:
            for extracted_skill, snippet in evidence_by_skill.items():
                if normalize_skill(extracted_skill) in skill_variants(skill) and snippet:
                    depth_label = skill_depths.get(extracted_skill, "Basic") if skill_depths else "Basic"
                    evidence_parts.append(f"{skill} [{depth_label}]: {snippet[:110]}")
                    break

    reason_parts = [f"{role_name} is a {match_level.lower()} fit"] if role_name else [f"Match level: {match_level}"]
    if matched:
        reason_parts.append(f"matched skills: {', '.join(matched[:5])}")
    if evidence_parts:
        reason_parts.append(f"evidence: {' | '.join(evidence_parts)}")
    if missing:
        reason_parts.append(f"missing: {', '.join(missing[:3])}")

    priority_score = (
        (0.50 * confidence)
        + (0.20 * depth)
        + (0.20 * min(1.0, years_of_experience / 10.0))
        + (0.10 * min(1.0, leadership_score))
    )

    if skill_depths:
        depth_bonus = sum(1.0 if value == "Advanced" else 0.6 if value == "Intermediate" else 0.25 for value in skill_depths.values())
        priority_score = min(1.0, priority_score + (depth_bonus / max(1, len(skill_depths))) * 0.1)

    return RoleMatchResult(
        role_name=role_name,
        required_skills=ordered_required,
        matched_skills=matched,
        missing_skills=missing,
        confidence=round(confidence, 4),
        composite=round(composite, 4),
        match_level=match_level,
        priority_score=round(priority_score, 4),
        reason=". ".join(reason_parts) + ".",
    )
