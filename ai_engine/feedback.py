from __future__ import annotations
import json
import sqlite3
from database.connection import get_connection

def build_feedback(missing_skills: list[str]) -> str:
    if not missing_skills:
        return "Candidate is a strong fit with no major skill gaps."
    return f"Recommended focus areas: {', '.join(missing_skills)}."

def process_feedback_for_learning(
    job_id: str,
    application_id: str,
    decision: str,
    rejection_reason: str = "",
    notes: str = ""
) -> None:
    """
    Analyzes recruiter feedback and adjusts skill weights dynamically.
    - If rejected due to missing skills, increment rejection count and increase weight offset.
    - If hired/accepted with matched skills, increment hire count and boost skill weights.
    """
    # Fetch application details
    with get_connection() as connection:
        app_row = connection.execute(
            "SELECT candidate_skills, missing_skills FROM job_applications WHERE id = ?",
            (application_id,)
        ).fetchone()
        
    if not app_row:
        return

    try:
        candidate_skills = json.loads(app_row["candidate_skills"])
        missing_skills = json.loads(app_row["missing_skills"])
    except Exception:
        return

    decision = decision.upper()
    skills_to_penalize = []
    skills_to_boost = []

    # Parse feedback reasons
    text_to_search = (rejection_reason + " " + notes).lower()

    if decision == "REJECTED":
        # Penalize missing skills
        for s in missing_skills:
            skills_to_penalize.append(s.lower().strip())
        # Parse text for explicit skill mentions
        for s in candidate_skills + missing_skills:
            s_low = s.lower().strip()
            if s_low in text_to_search:
                skills_to_penalize.append(s_low)
    elif decision in ["ACCEPTED", "INTERVIEWED", "HIRED"]:
        # Boost matched skills
        for s in candidate_skills:
            if s not in missing_skills:
                skills_to_boost.append(s.lower().strip())
        # Parse text for explicit skill mentions
        for s in candidate_skills:
            s_low = s.lower().strip()
            if s_low in text_to_search:
                skills_to_boost.append(s_low)

    # Update dynamic_skill_weights in DB
    with get_connection() as connection:
        for s in set(skills_to_penalize):
            # Check if exists
            row = connection.execute(
                "SELECT * FROM dynamic_skill_weights WHERE job_id = ? AND skill_name = ?",
                (job_id, s)
            ).fetchone()
            if row:
                new_rej = row["rejection_count"] + 1
                new_offset = min(0.40, row["weight_offset"] + 0.05)
                connection.execute(
                    """
                    UPDATE dynamic_skill_weights 
                    SET rejection_count = ?, weight_offset = ?
                    WHERE job_id = ? AND skill_name = ?
                    """,
                    (new_rej, new_offset, job_id, s)
                )
            else:
                connection.execute(
                    """
                    INSERT INTO dynamic_skill_weights (job_id, skill_name, weight_offset, rejection_count, hire_count)
                    VALUES (?, ?, 0.05, 1, 0)
                    """,
                    (job_id, s)
                )

        for s in set(skills_to_boost):
            row = connection.execute(
                "SELECT * FROM dynamic_skill_weights WHERE job_id = ? AND skill_name = ?",
                (job_id, s)
            ).fetchone()
            if row:
                new_hire = row["hire_count"] + 1
                new_offset = min(0.30, row["weight_offset"] + 0.05)
                connection.execute(
                    """
                    UPDATE dynamic_skill_weights 
                    SET hire_count = ?, weight_offset = ?
                    WHERE job_id = ? AND skill_name = ?
                    """,
                    (new_hire, new_offset, job_id, s)
                )
            else:
                connection.execute(
                    """
                    INSERT INTO dynamic_skill_weights (job_id, skill_name, weight_offset, rejection_count, hire_count)
                    VALUES (?, ?, 0.05, 0, 1)
                    """,
                    (job_id, s)
                )

def get_dynamic_skill_weights(job_id: str) -> dict[str, float]:
    """Returns a dictionary of skill_name -> weight_offset for a given job."""
    weights = {}
    try:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT skill_name, weight_offset FROM dynamic_skill_weights WHERE job_id = ?",
                (job_id,)
            ).fetchall()
        for row in rows:
            weights[row["skill_name"].lower().strip()] = float(row["weight_offset"])
    except Exception:
        pass
    return weights


# ============================================================
# Phase 6: Advanced Recruiter Preference Learning
# ============================================================

def build_recruiter_preference_model(job_id: str) -> dict:
    """
    Build a recruiter preference profile from historical feedback for a job.
    Returns preferred_skills, avoided_skills, acceptance rates, and scores.
    """
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT rf.is_accepted, rf.rejection_reason,
                       rf.ai_score, ja.candidate_skills
                FROM recruiter_feedback rf
                JOIN job_applications ja ON rf.application_id = ja.id
                WHERE rf.job_id = ?
                """,
                (job_id,)
            ).fetchall()
    except Exception:
        return {}

    if not rows:
        return {"job_id": job_id, "status": "no_data"}

    accepted_skills: dict[str, int] = {}
    rejected_skills: dict[str, int] = {}
    accepted_scores: list[float] = []
    rejected_scores: list[float] = []
    rejection_reasons: list[str] = []

    for row in rows:
        skills = []
        try:
            skills = json.loads(row["candidate_skills"] or "[]")
        except Exception:
            pass
        ai_score = float(row["ai_score"] or 0)
        if row["is_accepted"]:
            accepted_scores.append(ai_score)
            for s in skills:
                key = s.lower().strip()
                accepted_skills[key] = accepted_skills.get(key, 0) + 1
        else:
            rejected_scores.append(ai_score)
            for s in skills:
                key = s.lower().strip()
                rejected_skills[key] = rejected_skills.get(key, 0) + 1
            if row["rejection_reason"]:
                rejection_reasons.append(row["rejection_reason"])

    total = len(rows)
    accepted_count = len(accepted_scores)
    preferred = sorted(
        [s for s in accepted_skills if accepted_skills[s] > rejected_skills.get(s, 0)],
        key=lambda s: accepted_skills[s], reverse=True,
    )[:10]
    avoided = sorted(
        [s for s in rejected_skills if rejected_skills[s] > accepted_skills.get(s, 0)],
        key=lambda s: rejected_skills[s], reverse=True,
    )[:10]

    return {
        "job_id": job_id,
        "total_reviewed": total,
        "accepted_count": accepted_count,
        "acceptance_rate": round(accepted_count / total, 4) if total else 0.0,
        "preferred_skills": preferred,
        "avoided_skills": avoided,
        "avg_accepted_score": round(sum(accepted_scores) / max(1, len(accepted_scores)), 2),
        "avg_rejected_score": round(sum(rejected_scores) / max(1, len(rejected_scores)), 2),
    }


def detect_rejection_patterns(job_id: str) -> dict:
    """Identify common patterns in rejected candidates for a job."""
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT rf.rejection_reason, ja.missing_skills, rf.ai_score
                FROM recruiter_feedback rf
                JOIN job_applications ja ON rf.application_id = ja.id
                WHERE rf.job_id = ? AND rf.is_accepted = 0
                """,
                (job_id,)
            ).fetchall()
    except Exception:
        return {}

    if not rows:
        return {"job_id": job_id, "status": "no_rejected_data"}

    missing_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    scores: list[float] = []

    for row in rows:
        scores.append(float(row["ai_score"] or 0))
        try:
            for skill in json.loads(row["missing_skills"] or "[]"):
                key = skill.lower().strip()
                missing_counts[key] = missing_counts.get(key, 0) + 1
        except Exception:
            pass
        if row["rejection_reason"]:
            reason = row["rejection_reason"].lower().strip()
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    top_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "job_id": job_id,
        "total_rejected": len(rows),
        "avg_rejected_score": round(sum(scores) / max(1, len(scores)), 2),
        "most_missing_skills": [s for s, _ in top_missing],
        "top_rejection_reasons": [r for r, _ in top_reasons],
    }


def compute_hiring_success_patterns(job_id: str) -> dict:
    """Top skills and profiles among accepted candidates."""
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT ja.candidate_skills, ja.match_score
                FROM recruiter_feedback rf
                JOIN job_applications ja ON rf.application_id = ja.id
                WHERE rf.job_id = ? AND rf.is_accepted = 1
                """,
                (job_id,)
            ).fetchall()
    except Exception:
        return {}

    if not rows:
        return {"job_id": job_id, "status": "no_hired_data"}

    skill_counts: dict[str, int] = {}
    scores: list[float] = []

    for row in rows:
        scores.append(float(row["match_score"] or 0))
        try:
            for skill in json.loads(row["candidate_skills"] or "[]"):
                key = skill.lower().strip()
                skill_counts[key] = skill_counts.get(key, 0) + 1
        except Exception:
            pass

    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    return {
        "job_id": job_id,
        "total_accepted": len(rows),
        "avg_accepted_score": round(sum(scores) / max(1, len(scores)), 2),
        "top_accepted_skills": [s for s, _ in top_skills],
    }


def generate_feedback_report(job_id: str) -> str:
    """Generate a human-readable markdown feedback insight report for a job."""
    pref = build_recruiter_preference_model(job_id)
    rejection = detect_rejection_patterns(job_id)
    success = compute_hiring_success_patterns(job_id)

    if pref.get("status") == "no_data":
        return f"# Feedback Report: Job {job_id}\n\nNo recruiter feedback data available yet."

    return "\n".join([
        f"# Recruiter Feedback Intelligence Report",
        f"**Job ID:** `{job_id}`\n",
        f"## Overview",
        f"- **Total Reviewed:** {pref.get('total_reviewed', 0)}",
        f"- **Accepted:** {pref.get('accepted_count', 0)}",
        f"- **Acceptance Rate:** {pref.get('acceptance_rate', 0):.1%}",
        f"- **Avg Accepted Score:** {pref.get('avg_accepted_score', 0):.1f}%",
        f"- **Avg Rejected Score:** {pref.get('avg_rejected_score', 0):.1f}%\n",
        f"## Recruiter Preferences",
        f"**Preferred Skills:** {', '.join(pref.get('preferred_skills', [])[:8]) or 'N/A'}",
        f"**Avoided Skills:** {', '.join(pref.get('avoided_skills', [])[:8]) or 'N/A'}\n",
        f"## Rejection Patterns",
        f"- **Most Missing Skills:** {', '.join(rejection.get('most_missing_skills', [])[:6]) or 'N/A'}",
        f"- **Top Reasons:** {', '.join(rejection.get('top_rejection_reasons', [])[:3]) or 'N/A'}\n",
        f"## Hiring Success Patterns",
        f"- **Top Accepted Skills:** {', '.join(success.get('top_accepted_skills', [])[:10]) or 'N/A'}",
    ])
