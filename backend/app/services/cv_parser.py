from __future__ import annotations

import re

from backend.app.services.document_parser import extract_text_from_resume
from backend.app.services.skill_extractor import SkillExtractor


def clean_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    return normalized.lower()


def extract_candidate_profile_text(file_bytes: bytes, filename: str) -> tuple[str, list[str], str]:
    raw_text = extract_text_from_resume(file_bytes, filename)
    cleaned = clean_text(raw_text)
    if not cleaned:
        return "", [], ""

    extractor = SkillExtractor()
    skills = extractor.extract(cleaned)

    # Lightweight extraction by section hints.
    experience_parts = _section_text(cleaned, ["experience", "employment", "work history"])
    projects_parts = _section_text(cleaned, ["projects", "project", "portfolio"])
    summary_parts = _section_text(cleaned, ["summary", "profile", "about", "objective"])

    candidate_profile_text = " ".join(
        [
            "skills: " + ", ".join(skills),
            "experience: " + experience_parts,
            "projects: " + projects_parts,
            "summary: " + summary_parts,
            "full_cv: " + cleaned,
        ]
    ).strip()

    return candidate_profile_text, skills, cleaned


def _section_text(text: str, section_hints: list[str]) -> str:
    lines = [line.strip() for line in text.split(".") if line.strip()]
    selected: list[str] = []
    for line in lines:
        if any(hint in line for hint in section_hints):
            selected.append(line)
    if not selected:
        # fallback to first few sentences for robustness
        selected = lines[:4]
    return ". ".join(selected[:8])
