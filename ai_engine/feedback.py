from __future__ import annotations


def build_feedback(missing_skills: list[str]) -> str:
    if not missing_skills:
        return "المرشح جاهز تقريبًا للوظيفة دي من ناحية المهارات الأساسية."
    return f"المهارات اللي محتاجة تقوية: {', '.join(missing_skills)}"
