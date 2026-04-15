from __future__ import annotations


def build_feedback(missing_skills: list[str]) -> str:
    if not missing_skills:
        return "Candidate is a strong fit with no major skill gaps."
    skills_text = ", ".join(missing_skills)
    return f"Recommended focus areas: {skills_text}."
