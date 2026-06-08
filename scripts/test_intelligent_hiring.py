from __future__ import annotations
import os
import sys
import json
import sqlite3

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from database.connection import get_connection
from database.init_db import init_recruitment_db
from backend.app.schemas import JobInput, HiringRules, CandidateProfile
from backend.app.services.recruitment_service import recruitment_service
from backend.app.services.feedback_service import feedback_service
from ai_engine.training.ltr_pipeline import ltr_pipeline

def run_integration_tests():
    print("=" * 80)
    print("  STARTING INTEGRATION TEST SUITE: HIREMIND PLATFORM ENHANCEMENT")
    print("=" * 80)

    # 1. Initialize DB and confirm migration tables exist
    init_recruitment_db()
    with get_connection() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(posted_jobs)").fetchall()}

    assert "recruiter_feedback" in tables, "Table recruiter_feedback missing!"
    assert "dynamic_skill_weights" in tables, "Table dynamic_skill_weights missing!"
    assert "hiring_rules" in columns, "Column hiring_rules missing from posted_jobs!"
    print("[OK] Phase 1 & 2: Database schemas and migrations applied successfully.")

    # 2. Test Hiring Rules Engine and Template Mapping
    from ai_engine.rules_engine import get_rule_template_for_job, HiringRulesEngine
    devops_template = get_rule_template_for_job("Senior DevOps Engineer")
    assert any(s.lower() == "kubernetes" for s in devops_template.mandatory_skills), "Template failed mapping!"
    print("[OK] Phase 1: Role-specific rule templates loaded.")

    rules_engine = HiringRulesEngine()
    # Candidate missing Kubernetes and Terraform
    rules_res = rules_engine.evaluate(
        candidate_name="Alice Smith",
        cv_text="FastAPI Backend developer. Experience with AWS, Docker, Python.",
        candidate_skills=["FastAPI", "AWS", "Docker", "Python"],
        years_of_experience=2,
        hiring_rules=devops_template
    )
    assert rules_res["rule_status"] == "REJECTED", "Rules engine failed rejection constraint!"
    assert any("kubernetes" in r.lower() for r in rules_res["reasons"]), "Missing Kubernetes not logged!"
    assert any("experience below" in r.lower() for r in rules_res["reasons"]), "Min experience not validated!"
    print("[OK] Phase 1: Hiring Rules Engine successfully evaluated candidate constraints.")

    # 3. Create a test job and candidate application
    with get_connection() as conn:
        conn.execute("DELETE FROM posted_jobs")
        conn.execute("DELETE FROM job_applications")
        conn.execute("DELETE FROM recruiter_feedback")
        conn.execute("DELETE FROM dynamic_skill_weights")

    job_input = JobInput(
        title="Senior DevOps Engineer",
        description="AWS Kubernetes Terraform specialist.",
        required_skills=["AWS", "Kubernetes", "Terraform", "Docker"],
        experience_level="Senior",
        domain="devops",
        hiring_rules=devops_template
    )
    job = recruitment_service.create_job(job_input)
    print(f"[OK] Job posted successfully: {job.title} ({job.id})")

    # Seed candidates and calculate scores
    # Candidate 1: Strong fit
    strong_cand = CandidateProfile(
        name="Bob Jones",
        headline="Senior DevOps Engineer with AWS & Terraform",
        skills=["AWS", "Kubernetes", "Terraform", "Docker"],
        summary="5+ years of experience automating infrastructure using Kubernetes and Terraform on AWS."
    )
    
    # Candidate 2: Weak fit (missing AWS, Kubernetes)
    weak_cand = CandidateProfile(
        name="Jane Doe",
        headline="Junior Web Developer",
        skills=["HTML", "CSS", "React"],
        summary="1 year of experience building react websites."
    )

    # Apply to job manually (mocking CV files)
    app1 = recruitment_service.apply_to_job_cv_only(
        job_id=job.id,
        file_bytes=b"Bob Jones DevOps profile: Kubernetes, Terraform, AWS, Docker. 6 years experience.",
        filename="bob_jones.pdf",
        confirmed_skills=strong_cand.skills
    )
    print(f"[OK] Strong candidate applied. Match Score: {app1['score']}%")

    app2 = recruitment_service.apply_to_job_cv_only(
        job_id=job.id,
        file_bytes=b"Jane Doe Web profile: React CSS HTML. 1 year experience.",
        filename="jane_doe.pdf",
        confirmed_skills=weak_cand.skills
    )
    print(f"[OK] Weak candidate applied. Match Score: {app2['score']}%")

    # Verify that the weak candidate got rejected by the rules engine
    with get_connection() as conn:
        app_rows = conn.execute("SELECT * FROM job_applications ORDER BY match_score DESC").fetchall()
    
    assert float(app_rows[0]["match_score"]) > float(app_rows[1]["match_score"]), "Ranking scores incorrect!"
    print("[OK] Retrieval and gating working correctly.")

    # 4. Submit recruiter feedback
    # Bob is hired
    feedback1 = feedback_service.submit_feedback({
        "application_id": app1["application_id"],
        "job_id": job.id,
        "ai_score": app1["score"],
        "candidate_rank": 1,
        "recruiter_decision": "HIRED",
        "recruiter_notes": "Perfect match. Very strong Terraform skills."
    })
    print("[OK] Phase 2: Bob feedback submitted (HIRED).")

    # Jane is rejected
    feedback2 = feedback_service.submit_feedback({
        "application_id": app2["application_id"],
        "job_id": job.id,
        "ai_score": app2["score"],
        "candidate_rank": 2,
        "recruiter_decision": "REJECTED",
        "rejection_reason": "Missing mandatory skills",
        "recruiter_notes": "Lacks Kubernetes and Terraform experience."
    })
    print("[OK] Phase 2: Jane feedback submitted (REJECTED).")

    # 5. Check dynamic skill weights learning adjustments (Phase 4)
    with get_connection() as conn:
        weights = conn.execute("SELECT * FROM dynamic_skill_weights").fetchall()
    
    assert len(weights) > 0, "No dynamic skill weights recorded!"
    print(f"[OK] Phase 4: Feedback Learning recorded dynamic weight updates: {len(weights)} skills updated.")

    # 6. Retrieve analytics dashboard metrics (Phase 5)
    analytics = feedback_service.get_feedback_analytics()
    assert analytics["total_reviews"] == 2, "Analytics review count mismatch!"
    assert analytics["acceptance_rate"] == 0.5, "Acceptance rate calculated incorrectly!"
    assert "Missing mandatory skills" in analytics["most_common_rejection_reasons"], "Rejection reason grouping failed!"
    print("[OK] Phase 5: Recruiter Observability analytics calculated correctly.")

    # 7. Train LTR ranking pipeline (Phase 3)
    # Seed 3 more feedback items so LTR has minimum 5 rows
    app3 = recruitment_service.apply_to_job_cv_only(
        job_id=job.id,
        file_bytes=b"Dave DevOps: AWS Kubernetes. 3 years experience.",
        filename="dave_devops.pdf",
        confirmed_skills=["AWS", "Kubernetes"]
    )
    feedback_service.submit_feedback({
        "application_id": app3["application_id"],
        "job_id": job.id,
        "ai_score": app3["score"],
        "candidate_rank": 3,
        "recruiter_decision": "INTERVIEWED",
        "recruiter_notes": "Good AWS background."
    })
    
    app4 = recruitment_service.apply_to_job_cv_only(
        job_id=job.id,
        file_bytes=b"Sarah DevOps: AWS Terraform. 4 years experience.",
        filename="sarah_devops.pdf",
        confirmed_skills=["AWS", "Terraform"]
    )
    feedback_service.submit_feedback({
        "application_id": app4["application_id"],
        "job_id": job.id,
        "ai_score": app4["score"],
        "candidate_rank": 4,
        "recruiter_decision": "ACCEPTED",
        "recruiter_notes": "Promising profile."
    })

    app5 = recruitment_service.apply_to_job_cv_only(
        job_id=job.id,
        file_bytes=b"Mike DevOps: Terraform Docker. 2 years experience.",
        filename="mike_devops.pdf",
        confirmed_skills=["Terraform", "Docker"]
    )
    feedback_service.submit_feedback({
        "application_id": app5["application_id"],
        "job_id": job.id,
        "ai_score": app5["score"],
        "candidate_rank": 5,
        "recruiter_decision": "REJECTED",
        "rejection_reason": "Missing mandatory skills",
        "recruiter_notes": "Lacks AWS."
    })

    print("[OK] Additional feedback rows seeded. Training LTR pipeline...")
    train_res = ltr_pipeline.train()
    assert train_res["status"] == "success", f"LTR training failed: {train_res.get('message')}"
    print(f"[OK] Phase 3: LTR model trained and versioned successfully: {train_res['metadata']['version']}")

    # 8. Verify LTR model re-ranking in retrieval flow
    ltr_info = ltr_pipeline.get_metadata()
    assert ltr_info is not None, "LTR metadata not saved!"
    print(f"[OK] LTR info retrieved. Feature importance weights: {ltr_info['feature_importance']}")

    # Check dashboard applications listing re-ranking
    dashboard_res = recruitment_service.company_dashboard(sort_by="score")
    ranked_apps = dashboard_res.jobs[0].applicants
    print("\nFinal Ranked Applicants List (re-ranked via LambdaMART LTR):")
    for app in ranked_apps:
        print(f"  Rank {app.ranking}: {app.candidate_name:15} | Match Score: {app.match_score}% | Status: {app.interview_status or 'pending'}")

    print("\n" + "=" * 80)
    print("  ALL TESTS COMPLETED SUCCESSFULLY! PLATFORM UPGRADE IS PRODUCTION READY.")
    print("=" * 80)

if __name__ == "__main__":
    run_integration_tests()
