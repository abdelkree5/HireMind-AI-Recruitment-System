from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.services.skill_extractor import SkillExtractor
from backend.app.services.skill_normalizer import detect_skill_level, find_skill_sentence, normalize_skill, normalize_skills


@dataclass
class CandidateSkillProfile:
    raw_skills: list[str] = field(default_factory=list)
    normalized_skills: list[str] = field(default_factory=list)
    skill_levels: dict[str, str] = field(default_factory=dict)
    skill_evidence: dict[str, str] = field(default_factory=dict)
    grouped_skills: dict[str, list[str]] = field(default_factory=dict)
    normalized_text: str = ""


_LEVEL_RANK = {"Basic": 1, "Intermediate": 2, "Advanced": 3}


def build_candidate_skill_profile(text: str, extractor: SkillExtractor | None = None) -> CandidateSkillProfile:
    extractor = extractor or SkillExtractor()
    grouped, evidence = extractor.extract_grouped_with_evidence(text)

    raw_skills: list[str] = []
    for group_name in grouped:
        raw_skills.extend(grouped[group_name])

    normalized_skill_values = normalize_skills(raw_skills)
    normalized_grouped: dict[str, list[str]] = {key: [] for key in grouped}
    skill_levels: dict[str, str] = {}
    skill_evidence: dict[str, str] = {}

    for group_name, skills in grouped.items():
        for raw_skill in skills:
            canonical_skill = normalize_skill(raw_skill)
            if not canonical_skill:
                continue

            level = detect_skill_level(text, raw_skill)
            sentence = evidence.get(raw_skill) or evidence.get(canonical_skill) or find_skill_sentence(text, raw_skill)

            existing_level = skill_levels.get(canonical_skill)
            if existing_level is None or _LEVEL_RANK[level] >= _LEVEL_RANK.get(existing_level, 1):
                skill_levels[canonical_skill] = level
                if sentence:
                    skill_evidence[canonical_skill] = sentence

            if canonical_skill not in normalized_grouped[group_name]:
                normalized_grouped[group_name].append(canonical_skill)

    for canonical_skill in normalized_skill_values:
        if canonical_skill not in skill_levels:
            skill_levels[canonical_skill] = detect_skill_level(text, canonical_skill)
        if canonical_skill not in skill_evidence:
            sentence = find_skill_sentence(text, canonical_skill)
            if sentence:
                skill_evidence[canonical_skill] = sentence

    return CandidateSkillProfile(
        raw_skills=raw_skills,
        normalized_skills=normalized_skill_values,
        skill_levels=skill_levels,
        skill_evidence=skill_evidence,
        grouped_skills=normalized_grouped,
        normalized_text=" ".join((text or "").split()).lower(),
    )
