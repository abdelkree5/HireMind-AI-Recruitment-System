from __future__ import annotations

from datetime import datetime
import json
import re
import uuid
from collections import Counter

from backend.app.schemas import (
    InterviewAnswerResponse,
    InterviewReportResponse,
    InterviewStartResponse,
    InterviewTurn,
)
from backend.app.services.recruitment_db import get_connection, init_recruitment_db
from backend.app.services.skill_extractor import SkillExtractor


MAX_INTERVIEW_TURNS = 6
TECHNICAL_TARGETS = {
    "rest api": [
        "How did you handle performance, scaling, and error handling in that API?",
        "What did you do to keep the API stable under higher traffic?",
    ],
    "postgresql": [
        "How did you design indexes, queries, and transactions for that data model?",
        "What bottlenecks did you see and how did you fix them?",
    ],
    "python": [
        "Which Python patterns, testing approach, or architecture choices did you use?",
        "How did you keep the implementation maintainable as the project grew?",
    ],
    "fastapi": [
        "How did you structure dependencies, validation, and background tasks in FastAPI?",
        "How did you handle request lifecycle and error handling?",
    ],
    "kubernetes": [
        "How did you manage deployments, rollouts, and observability in Kubernetes?",
        "What was your strategy for configuration, scaling, and recovery?",
    ],
    "monitoring": [
        "Which metrics, dashboards, and alerts did you define?",
        "How did monitoring influence your incident response decisions?",
    ],
    "aws": [
        "Which AWS services did you use and how did you think about reliability and cost?",
        "How did you design for availability and operational safety in AWS?",
    ],
    "docker": [
        "How did you package and deploy the service with Docker?",
        "What issues did containers help you solve in the project?",
    ],
}


init_recruitment_db()


def start_job_linked_interview(application_id: str) -> InterviewStartResponse:
    application, job = _get_application_and_job(application_id)
    required_skills = _safe_load_json(job["required_skills"])
    missing_skills = _safe_load_json(application["missing_skills"])

    first_question = _build_initial_question(job["title"], required_skills, missing_skills)
    profile = _empty_candidate_profile()
    memory = {
        "profile": profile,
        "difficulty_level": "medium",
        "asked_questions": [first_question],
    }

    session_id = uuid.uuid4().hex
    started_at = datetime.utcnow().isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO interview_sessions (
                id,
                application_id,
                job_id,
                candidate_name,
                status,
                total_questions,
                current_question_index,
                questions_json,
                candidate_profile_json,
                answer_history_json,
                difficulty_level,
                started_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                application_id,
                job["id"],
                application["candidate_name"],
                "in_progress",
                1,
                0,
                json.dumps([first_question]),
                json.dumps(profile),
                json.dumps([]),
                "medium",
                started_at,
            ),
        )

    return InterviewStartResponse(
        session_id=session_id,
        application_id=application_id,
        job_title=job["title"],
        candidate_name=application["candidate_name"],
        status="in_progress",
        total_questions=1,
        current_question_index=0,
        current_question=first_question,
    )


def submit_interview_answer(session_id: str, answer: str) -> InterviewAnswerResponse:
    session = _get_session(session_id)
    if session["status"] == "completed":
        report = get_interview_report(session_id)
        return InterviewAnswerResponse(
            session_id=session_id,
            status="completed",
            current_question_index=int(session["current_question_index"]),
            next_question=None,
            answer_score=0.0,
            answer_feedback="Interview already completed.",
            is_completed=True,
            final_score=report.overall_score,
            final_recommendation=report.hire_recommendation,
        )

    questions = _safe_load_json(session["questions_json"])
    current_index = int(session["current_question_index"])
    if current_index >= len(questions):
        report = _finalize_session(session_id)
        return InterviewAnswerResponse(
            session_id=session_id,
            status="completed",
            current_question_index=current_index,
            next_question=None,
            answer_score=0.0,
            answer_feedback="Interview completed.",
            is_completed=True,
            final_score=report.overall_score,
            final_recommendation=report.hire_recommendation,
        )

    question_text = str(questions[current_index])
    profile = _load_profile(session["candidate_profile_json"])
    history = _safe_load_json(session["answer_history_json"])
    difficulty_level = str(session["difficulty_level"] or "medium")

    answer_analysis = _analyze_answer(question_text, answer, profile)
    score = answer_analysis["total_score"]
    feedback = answer_analysis["feedback"]

    profile = _update_candidate_profile(profile, question_text, answer, answer_analysis)
    history.append(
        {
            "question": question_text,
            "answer": answer,
            "score": score,
            "dimensions": answer_analysis["dimensions"],
            "feedback": feedback,
            "detected_skills": answer_analysis["detected_skills"],
            "project": answer_analysis["project"],
        }
    )

    next_difficulty = _adjust_difficulty(difficulty_level, score)
    used_questions = set(questions)
    next_question = None
    completed = current_index + 1 >= MAX_INTERVIEW_TURNS
    if not completed:
        next_question = _generate_next_question(
            question_text=question_text,
            answer=answer,
            profile=profile,
            difficulty=next_difficulty,
            job_title=session["job_title"],
            required_skills=_safe_load_json(session["required_skills_json"]),
            missing_skills=_safe_load_json(session["missing_skills_json"]),
            used_questions=used_questions,
        )
        if next_question is None:
            completed = True
        else:
            questions.append(next_question)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO interview_turns (
                session_id,
                question_index,
                question_text,
                candidate_answer,
                answer_score,
                feedback,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                current_index,
                question_text,
                answer,
                score,
                feedback,
                datetime.utcnow().isoformat(),
            ),
        )

        if completed:
            connection.execute(
                """
                UPDATE interview_sessions
                SET status = ?, current_question_index = ?, total_questions = ?, completed_at = ?,
                    candidate_profile_json = ?, answer_history_json = ?, difficulty_level = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    current_index + 1,
                    max(len(questions), current_index + 1),
                    datetime.utcnow().isoformat(),
                    json.dumps(profile),
                    json.dumps(history),
                    next_difficulty,
                    session_id,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE interview_sessions
                SET current_question_index = ?, total_questions = ?, questions_json = ?,
                    candidate_profile_json = ?, answer_history_json = ?, difficulty_level = ?
                WHERE id = ?
                """,
                (
                    current_index + 1,
                    len(questions),
                    json.dumps(questions),
                    json.dumps(profile),
                    json.dumps(history),
                    next_difficulty,
                    session_id,
                ),
            )

    if completed:
        report = _finalize_session(session_id)
        return InterviewAnswerResponse(
            session_id=session_id,
            status="completed",
            current_question_index=current_index + 1,
            next_question=None,
            answer_score=score,
            answer_feedback=feedback,
            is_completed=True,
            final_score=report.overall_score,
            final_recommendation=report.hire_recommendation,
        )

    return InterviewAnswerResponse(
        session_id=session_id,
        status="in_progress",
        current_question_index=current_index + 1,
        next_question=next_question,
        answer_score=score,
        answer_feedback=feedback,
        is_completed=False,
    )


def get_interview_report(session_id: str) -> InterviewReportResponse:
    with get_connection() as connection:
        session = connection.execute(
            """
            SELECT s.id, s.application_id, s.status, s.total_questions, s.current_question_index,
                   s.final_score, s.final_recommendation, s.started_at, s.completed_at,
                   s.candidate_profile_json, s.answer_history_json, s.job_id,
                   p.title AS job_title
            FROM interview_sessions s
            JOIN posted_jobs p ON p.id = s.job_id
            WHERE s.id = ?
            """,
            (session_id,),
        ).fetchone()

        if not session:
            raise ValueError("Interview session not found")

        candidate_row = connection.execute(
            "SELECT candidate_name FROM job_applications WHERE id = ?",
            (session["application_id"],),
        ).fetchone()

        turn_rows = connection.execute(
            """
            SELECT question_index, question_text, candidate_answer, answer_score, feedback
            FROM interview_turns
            WHERE session_id = ?
            ORDER BY question_index ASC
            """,
            (session_id,),
        ).fetchall()

        job_row = connection.execute(
            """
            SELECT required_skills, responsibilities, preferred_skills, tools, experience_level, domain
            FROM posted_jobs
            WHERE id = ?
            """,
            (session["job_id"],),
        ).fetchone()

    profile = _load_profile(session["candidate_profile_json"])
    turns = [
        InterviewTurn(
            question_index=int(row["question_index"]),
            question_text=row["question_text"],
            candidate_answer=row["candidate_answer"],
            answer_score=float(row["answer_score"]),
            feedback=row["feedback"],
        )
        for row in turn_rows
    ]

    overall_score = float(session["final_score"] or _calculate_overall_score(turns))
    level = _final_level(overall_score)
    strengths, weaknesses = _derive_strengths_and_weaknesses(profile, turns, job_row)
    hire_recommendation = _hire_recommendation(level)

    return InterviewReportResponse(
        session_id=session["id"],
        application_id=session["application_id"],
        job_title=session["job_title"],
        candidate_name=candidate_row["candidate_name"] if candidate_row else "Candidate",
        status=session["status"],
        total_questions=int(session["total_questions"]),
        answered_questions=len(turns),
        average_score=overall_score,
        recommendation=hire_recommendation,
        overall_score=overall_score,
        level=level,
        strengths=strengths,
        weaknesses=weaknesses,
        hire_recommendation=hire_recommendation,
        started_at=session["started_at"],
        completed_at=session["completed_at"],
        turns=turns,
    )


def get_latest_interview_for_application(application_id: str) -> InterviewReportResponse | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM interview_sessions
            WHERE application_id = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (application_id,),
        ).fetchone()

    if not row:
        return None
    return get_interview_report(row["id"])


def continue_interview(session_id: str, message: str) -> dict:
    response = submit_interview_answer(session_id, message)
    return {
        "session_id": response.session_id,
        "reply": response.next_question or "Interview completed.",
        "history": [
            {
                "role": "assistant",
                "message": response.next_question or f"Final score: {response.final_score or 0:.1f}%",
            }
        ],
        "status": response.status,
        "answer_score": response.answer_score,
        "answer_feedback": response.answer_feedback,
        "final_recommendation": response.final_recommendation,
    }


def _finalize_session(session_id: str) -> InterviewReportResponse:
    with get_connection() as connection:
        score_row = connection.execute(
            "SELECT AVG(answer_score) AS avg_score FROM interview_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()

        avg_score = float(score_row["avg_score"] or 0.0)
        recommendation = _hire_recommendation(_final_level(avg_score))

        connection.execute(
            """
            UPDATE interview_sessions
            SET final_score = ?, final_recommendation = ?, status = ?, completed_at = COALESCE(completed_at, ?)
            WHERE id = ?
            """,
            (avg_score, recommendation, "completed", datetime.utcnow().isoformat(), session_id),
        )

    return get_interview_report(session_id)


def _build_initial_question(job_title: str, required_skills: list[str], missing_skills: list[str]) -> str:
    if required_skills:
        first_skill = required_skills[0]
        return (
            f"Walk me through a real project that makes you a fit for the {job_title} role, "
            f"then describe your hands-on experience with {first_skill}."
        )
    if missing_skills:
        return (
            f"What is your strongest project experience for the {job_title} role, and how would you close "
            f"your gap in {missing_skills[0]}?"
        )
    return f"Walk me through a real project that makes you a fit for the {job_title} role."


def _analyze_answer(question: str, answer: str, profile: dict) -> dict:
    answer_text = answer.strip()
    answer_lower = answer_text.lower()
    skill_extractor = SkillExtractor()
    detected_skills = skill_extractor.extract(answer_text)

    technical_depth = _score_technical_depth(answer_text, question, detected_skills)
    clarity = _score_clarity(answer_text)
    real_experience = _score_real_experience(answer_text)
    impact = _score_impact(answer_text)

    total_score = round(
        (0.4 * technical_depth)
        + (0.2 * clarity)
        + (0.2 * real_experience)
        + (0.2 * impact),
        2,
    )

    feedback_parts = []
    if technical_depth < 55:
        feedback_parts.append("You need more technical depth and implementation detail.")
    if clarity < 55:
        feedback_parts.append("The explanation is a bit scattered; structure it more clearly.")
    if real_experience < 55:
        feedback_parts.append("Mention your exact role, actions, and ownership in the work.")
    if impact < 55:
        feedback_parts.append("Add measurable impact, metrics, or scale to make the answer stronger.")

    if not feedback_parts:
        feedback_parts.append(
            "Strong answer. You showed good technical depth, clear explanation, and practical impact."
        )

    project = _extract_project(answer_text)
    if project:
        feedback_parts.append(
            "You mentioned a project, but be ready to explain the challenge, metrics improved, and your exact role."
        )

    return {
        "total_score": total_score,
        "dimensions": {
            "technical_depth": round(technical_depth, 2),
            "clarity": round(clarity, 2),
            "real_experience": round(real_experience, 2),
            "impact": round(impact, 2),
        },
        "feedback": " ".join(feedback_parts),
        "detected_skills": detected_skills,
        "project": project,
        "answer_lower": answer_lower,
    }


def _score_technical_depth(answer_text: str, question: str, detected_skills: list[str]) -> float:
    answer_lower = answer_text.lower()
    depth_markers = [
        "architecture",
        "scaling",
        "latency",
        "throughput",
        "error handling",
        "optimization",
        "tradeoff",
        "design",
        "implemented",
        "built",
        "deployed",
        "refactored",
        "indexed",
        "observability",
    ]
    question_tokens = {token for token in re.findall(r"[a-z0-9\-/]+", question.lower()) if len(token) > 3}
    base = min(40.0, len(detected_skills) * 7.0)
    depth_hits = sum(1 for marker in depth_markers if marker in answer_lower)
    base += min(35.0, depth_hits * 5.0)
    base += min(20.0, len(question_tokens & set(detected_skills)) * 4.0)
    return max(0.0, min(100.0, base + 20.0))


def _score_clarity(answer_text: str) -> float:
    length = len(answer_text.split())
    sentence_count = max(1, len([part for part in re.split(r"[\.!?]+", answer_text) if part.strip()]))
    connectors = sum(1 for token in ["first", "then", "because", "so", "therefore", "however", "for example"] if token in answer_text.lower())
    score = 30.0
    if 40 <= length <= 180:
        score += 35.0
    elif length < 20:
        score += 5.0
    else:
        score += 20.0
    if sentence_count >= 2:
        score += 20.0
    score += min(15.0, connectors * 5.0)
    return max(0.0, min(100.0, score))


def _score_real_experience(answer_text: str) -> float:
    answer_lower = answer_text.lower()
    evidence_terms = [
        "i built",
        "i implemented",
        "i led",
        "i owned",
        "my role",
        "our team",
        "project",
        "production",
        "worked on",
        "deployed",
    ]
    hits = sum(1 for term in evidence_terms if term in answer_lower)
    score = 20.0 + min(50.0, hits * 10.0)
    if any(token in answer_lower for token in ["years", "months", "week", "month"]):
        score += 10.0
    if any(token in answer_lower for token in ["client", "customer", "team", "stakeholder"]):
        score += 10.0
    return max(0.0, min(100.0, score))


def _score_impact(answer_text: str) -> float:
    answer_lower = answer_text.lower()
    impact_terms = [
        "%",
        "percent",
        "latency",
        "throughput",
        "users",
        "requests",
        "revenue",
        "cost",
        "faster",
        "reduced",
        "improved",
        "increased",
        "uptime",
        "scale",
    ]
    hits = sum(1 for term in impact_terms if term in answer_lower)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\b", answer_text))
    score = 20.0 + min(40.0, hits * 8.0) + min(25.0, numbers * 6.0)
    if any(token in answer_lower for token in ["before", "after", "result", "outcome"]):
        score += 10.0
    return max(0.0, min(100.0, score))


def _generate_next_question(
    question_text: str,
    answer: str,
    profile: dict,
    difficulty: str,
    job_title: str,
    required_skills: list[str],
    missing_skills: list[str],
    used_questions: set[str],
) -> str | None:
    answer_lower = answer.lower()
    skill_extractor = SkillExtractor()
    detected_skills = skill_extractor.extract(answer)
    profile_skills = set(profile.get("skills", []))
    combined_skills = list(dict.fromkeys([*profile_skills, *detected_skills]))

    if _extract_project(answer) is not None:
        followups = [
            "What was the main challenge, what metrics improved, and what was your exact role?",
            "How did you measure the impact of that project, and what tradeoffs did you make?",
            "If you could redo that project, what would you change to make it more scalable or reliable?",
        ]
        for question in followups:
            if question not in used_questions:
                return question

    if "rest api" in combined_skills or "rest api" in answer_lower:
        question = "How did you handle performance, scaling, and error handling in that API?"
        if question not in used_questions:
            return question

    if any(skill in combined_skills for skill in ["aws", "kubernetes", "monitoring", "terraform"]):
        question = "How did you design for reliability, scaling, and observability in that system?"
        if question not in used_questions:
            return question

    target_skill = _next_gap(required_skills, profile_skills, missing_skills)
    if target_skill:
        question = _skill_followup_question(target_skill, difficulty)
        if question not in used_questions:
            return question

    if difficulty == "hard":
        question = f"What is the hardest technical tradeoff you made in a {job_title} style project, and why?"
    elif difficulty == "easy":
        question = "Can you explain one project simply, step by step, and what you personally contributed?"
    else:
        question = "Tell me about one project, the problem you solved, and the result you achieved."

    if question in used_questions:
        return None
    return question


def _next_gap(required_skills: list[str], profile_skills: set[str], missing_skills: list[str]) -> str | None:
    for skill in required_skills:
        normalized = skill.lower().strip()
        if normalized not in profile_skills:
            return normalized
    if missing_skills:
        return missing_skills[0].lower().strip()
    return None


def _skill_followup_question(skill: str, difficulty: str) -> str:
    skill = skill.lower().strip()
    if skill in TECHNICAL_TARGETS:
        if difficulty == "hard":
            return TECHNICAL_TARGETS[skill][1]
        return TECHNICAL_TARGETS[skill][0]
    if difficulty == "hard":
        return f"How did you go deeper on {skill}, and what technical tradeoffs did you make?"
    return f"Tell me about a real example where you used {skill}."


def _adjust_difficulty(current: str, score: float) -> str:
    if score >= 80:
        return "hard"
    if score < 50:
        return "easy"
    return current if current in {"easy", "medium", "hard"} else "medium"


def _calculate_overall_score(turns: list[InterviewTurn]) -> float:
    if not turns:
        return 0.0
    return round(sum(turn.answer_score for turn in turns) / len(turns), 2)


def _final_level(score: float) -> str:
    if score >= 80:
        return "Strong Candidate"
    if score >= 60:
        return "Maybe"
    return "Weak Candidate"


def _hire_recommendation(level: str) -> str:
    if level == "Strong Candidate":
        return "Yes"
    if level == "Maybe":
        return "Maybe"
    return "No"


def _derive_strengths_and_weaknesses(profile: dict, turns: list[InterviewTurn], job_row) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    profile_skills = profile.get("skills", [])
    profile_projects = profile.get("projects", [])

    if profile_skills:
        strengths.append(f"Detected skills: {', '.join(profile_skills[:5])}")
    if profile_projects:
        strengths.append(f"Projects discussed: {len(profile_projects)}")

    strong_turns = [turn for turn in turns if turn.answer_score >= 75]
    weak_turns = [turn for turn in turns if turn.answer_score < 55]

    if strong_turns:
        strengths.append("Good technical depth in several answers")
    if any("metric" in turn.feedback.lower() or "impact" in turn.feedback.lower() for turn in turns):
        strengths.append("Shows awareness of business impact")

    if weak_turns:
        weaknesses.append("Some answers lacked measurable impact or technical detail")
    if not profile_projects:
        weaknesses.append("Could not clearly explain a real project end-to-end")

    required_skills = _safe_load_json(job_row["required_skills"]) if job_row else []
    missing = [skill for skill in required_skills if skill.lower() not in {s.lower() for s in profile_skills}]
    if missing:
        weaknesses.append(f"Uncovered job skills: {', '.join(missing[:4])}")

    if not strengths:
        strengths.append("Interview completed with basic participation")
    if not weaknesses:
        weaknesses.append("No major weaknesses detected")

    return strengths[:5], weaknesses[:5]


def _extract_project(answer_text: str) -> str | None:
    lowered = answer_text.lower()
    project_triggers = ["project", "built", "implemented", "worked on", "launched", "deployed"]
    if not any(trigger in lowered for trigger in project_triggers):
        return None

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", answer_text) if sentence.strip()]
    if sentences:
        return sentences[0][:240]
    return answer_text[:240]


def _empty_candidate_profile() -> dict:
    return {
        "skills": [],
        "projects": [],
        "strengths": [],
        "weaknesses": [],
    }


def _update_candidate_profile(profile: dict, question: str, answer: str, analysis: dict) -> dict:
    profile = _normalize_profile(profile)
    detected_skills = analysis["detected_skills"]
    project = analysis["project"]
    score = analysis["total_score"]

    profile["skills"] = _dedupe(profile["skills"] + detected_skills)
    if project:
        profile["projects"] = _dedupe(profile["projects"] + [project])

    if score >= 75:
        profile["strengths"].append(_summarize_strength(question, answer, analysis))
    if score < 55:
        profile["weaknesses"].append(_summarize_weakness(question, answer, analysis))

    profile["strengths"] = _dedupe(profile["strengths"])
    profile["weaknesses"] = _dedupe(profile["weaknesses"])
    return profile


def _summarize_strength(question: str, answer: str, analysis: dict) -> str:
    if analysis["project"]:
        return f"Explained a project well for: {question[:60]}"
    if analysis["detected_skills"]:
        return f"Demonstrated hands-on use of {', '.join(analysis['detected_skills'][:3])}"
    return f"Answered clearly about: {question[:60]}"


def _summarize_weakness(question: str, answer: str, analysis: dict) -> str:
    missing_parts = []
    dimensions = analysis["dimensions"]
    if dimensions["technical_depth"] < 55:
        missing_parts.append("more technical depth")
    if dimensions["impact"] < 55:
        missing_parts.append("measurable impact")
    if dimensions["real_experience"] < 55:
        missing_parts.append("clearer ownership")
    if not missing_parts:
        missing_parts.append("clearer structure")
    return f"Needs {' and '.join(missing_parts)} for: {question[:60]}"


def _normalize_profile(profile: dict) -> dict:
    base = _empty_candidate_profile()
    if isinstance(profile, dict):
        for key in base:
            value = profile.get(key, [])
            if isinstance(value, list):
                base[key] = [str(item) for item in value]
    return base


def _load_profile(value: str | dict | None) -> dict:
    if isinstance(value, dict):
        return _normalize_profile(value)
    if not value:
        return _empty_candidate_profile()
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return _normalize_profile(parsed)
    except Exception:
        pass
    return _empty_candidate_profile()


def _dedupe(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value.lower() not in seen:
            seen.add(value.lower())
            ordered.append(value)
    return ordered


def _get_application_and_job(application_id: str):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT a.id AS application_id, a.candidate_name, a.missing_skills,
                   j.id AS job_id, j.title, j.required_skills
            FROM job_applications a
            JOIN posted_jobs j ON j.id = a.job_id
            WHERE a.id = ?
            """,
            (application_id,),
        ).fetchone()

    if not row:
        raise ValueError("Application not found")

    return (
        {
            "id": row["application_id"],
            "candidate_name": row["candidate_name"],
            "missing_skills": row["missing_skills"],
        },
        {
            "id": row["job_id"],
            "title": row["title"],
            "required_skills": row["required_skills"],
        },
    )


def _get_session(session_id: str):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT s.id, s.application_id, s.status, s.total_questions, s.current_question_index, s.questions_json,
                   s.candidate_profile_json, s.answer_history_json, s.difficulty_level, s.job_id,
                   p.title AS job_title, p.required_skills AS required_skills_json,
                   a.missing_skills AS missing_skills_json
            FROM interview_sessions s
            JOIN posted_jobs p ON p.id = s.job_id
            JOIN job_applications a ON a.id = s.application_id
            WHERE s.id = ?
            """,
            (session_id,),
        ).fetchone()
    if not row:
        raise ValueError("Interview session not found")
    return row


def _safe_load_json(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        return []
    return []
