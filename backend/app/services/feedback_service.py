from __future__ import annotations
import uuid
import json
from datetime import datetime
from typing import Any
from database.connection import get_connection

class FeedbackService:
    def submit_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        feedback_id = uuid.uuid4().hex
        created_at = datetime.utcnow().isoformat()
        
        # Calculate flags
        decision = payload.get("recruiter_decision", "PENDING").upper()
        is_accepted = 1 if decision in ["ACCEPTED", "INTERVIEWED", "HIRED"] else 0
        is_hired = 1 if decision == "HIRED" else 0
        
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO recruiter_feedback (
                    id, application_id, candidate_id, job_id, ai_score, candidate_rank,
                    recruiter_decision, is_accepted, is_hired, recruiter_notes, rejection_reason, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    payload["application_id"],
                    payload.get("candidate_id", payload["application_id"]),
                    payload["job_id"],
                    payload["ai_score"],
                    payload.get("candidate_rank"),
                    decision,
                    is_accepted,
                    is_hired,
                    payload.get("recruiter_notes", ""),
                    payload.get("rejection_reason", ""),
                    created_at
                )
            )
        
        # Trigger continuous feedback learning loop
        from ai_engine.feedback import process_feedback_for_learning
        process_feedback_for_learning(
            job_id=payload["job_id"],
            application_id=payload["application_id"],
            decision=decision,
            rejection_reason=payload.get("rejection_reason", ""),
            notes=payload.get("recruiter_notes", "")
        )

        return {
            "id": feedback_id,
            "application_id": payload["application_id"],
            "recruiter_decision": decision,
            "is_accepted": bool(is_accepted),
            "is_hired": bool(is_hired),
            "created_at": created_at
        }

    def update_feedback(self, feedback_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        decision = payload.get("recruiter_decision", "PENDING").upper()
        is_accepted = 1 if decision in ["ACCEPTED", "INTERVIEWED", "HIRED"] else 0
        is_hired = 1 if decision == "HIRED" else 0
        
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE recruiter_feedback
                SET
                    recruiter_decision = ?,
                    is_accepted = ?,
                    is_hired = ?,
                    recruiter_notes = ?,
                    rejection_reason = ?
                WHERE id = ?
                """,
                (
                    decision,
                    is_accepted,
                    is_hired,
                    payload.get("recruiter_notes", ""),
                    payload.get("rejection_reason", ""),
                    feedback_id
                )
            )
        return {
            "id": feedback_id,
            "recruiter_decision": decision,
            "is_accepted": bool(is_accepted),
            "is_hired": bool(is_hired)
        }

    def get_feedback(self, application_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM recruiter_feedback WHERE application_id = ?",
                (application_id,)
            ).fetchone()
        if not row:
            return None
        return dict(row)

    def get_feedback_by_job(self, job_id: str) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM recruiter_feedback WHERE job_id = ? ORDER BY created_at DESC",
                (job_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_feedback_analytics(self) -> dict[str, Any]:
        """Generates comprehensive recruiter agreement and accuracy analytics."""
        with get_connection() as connection:
            feedback_rows = connection.execute("SELECT * FROM recruiter_feedback").fetchall()
            app_rows = connection.execute("SELECT * FROM job_applications").fetchall()

        total_decisions = len(feedback_rows)
        if total_decisions == 0:
            return {
                "total_reviews": 0,
                "acceptance_rate": 0.0,
                "hiring_conversion_rate": 0.0,
                "recruiter_ai_agreement_rate": 0.0,
                "false_positives_count": 0,
                "false_negatives_count": 0,
                "false_positives": [],
                "false_negatives": [],
                "most_common_rejection_reasons": {},
                "most_common_hiring_reasons": {}
            }

        accepted_count = sum(1 for r in feedback_rows if r["is_accepted"] > 0)
        hired_count = sum(1 for r in feedback_rows if r["is_hired"] > 0)
        
        acceptance_rate = round(accepted_count / total_decisions, 4)
        hiring_conversion = round(hired_count / total_decisions, 4)

        # Rejection Reasons breakdown
        reasons_counter: dict[str, int] = {}
        hiring_reasons_counter: dict[str, int] = {}
        for r in feedback_rows:
            rej = r["rejection_reason"]
            if rej and r["is_accepted"] == 0:
                reasons_counter[rej] = reasons_counter.get(rej, 0) + 1
            notes = r["recruiter_notes"]
            if notes and r["is_hired"] > 0:
                # Extract first few words or match common tags
                words = notes.strip().split(".")
                reason_phrase = words[0][:50] if words else "Strong profile match"
                hiring_reasons_counter[reason_phrase] = hiring_reasons_counter.get(reason_phrase, 0) + 1

        # Calculate False Positives (AI Score >= 75%, Recruiter rejected)
        # Calculate False Negatives (AI Score < 50%, Recruiter accepted/hired)
        false_positives = []
        false_negatives = []
        agreement_count = 0

        # Create mapping of application_id to details
        apps_map = {app["id"]: dict(app) for app in app_rows}

        for r in feedback_rows:
            ai_score = r["ai_score"]
            is_accepted = r["is_accepted"]
            app_id = r["application_id"]
            app_details = apps_map.get(app_id, {})
            cand_name = app_details.get("candidate_name", "Unknown Candidate")

            # AI decision boundary is considered 70.0%
            ai_recommends = 1 if ai_score >= 70.0 else 0
            if ai_recommends == is_accepted:
                agreement_count += 1

            if ai_score >= 75.0 and is_accepted == 0:
                false_positives.append({
                    "application_id": app_id,
                    "candidate_name": cand_name,
                    "ai_score": ai_score,
                    "rejection_reason": r["rejection_reason"],
                    "notes": r["recruiter_notes"]
                })
            elif ai_score < 50.0 and is_accepted == 1:
                false_negatives.append({
                    "application_id": app_id,
                    "candidate_name": cand_name,
                    "ai_score": ai_score,
                    "notes": r["recruiter_notes"]
                })

        agreement_rate = round(agreement_count / total_decisions, 4)

        return {
            "total_reviews": total_decisions,
            "acceptance_rate": acceptance_rate,
            "hiring_conversion_rate": hiring_conversion,
            "recruiter_ai_agreement_rate": agreement_rate,
            "false_positives_count": len(false_positives),
            "false_negatives_count": len(false_negatives),
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "most_common_rejection_reasons": dict(sorted(reasons_counter.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_common_hiring_reasons": dict(sorted(hiring_reasons_counter.items(), key=lambda x: x[1], reverse=True)[:5])
        }

feedback_service = FeedbackService()
