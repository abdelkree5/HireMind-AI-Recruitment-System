"""Diagnostic script: test the Apply Job scoring pipeline offline (no server needed)."""
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app.services.document_parser import extract_text_from_resume
from backend.app.services.skill_extractor import SkillExtractor
from backend.app.services.job_matcher import extract_candidate_skills, match_job_to_candidate, normalize_skills
from backend.app.services.matching_service import MatchingService

# ---- Test scenarios ----
# Each test: (CV file, job_title, job_description, required_skills, expected_quality)
TEST_CASES = [
    {
        "cv": "test_cvs/ahmed_backend.docx",
        "job_title": "Backend Python Developer",
        "job_description": "Build and maintain REST APIs using Python and FastAPI. Work with PostgreSQL and Docker.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Git"],
        "expected": "HIGH - Ahmed is a perfect backend match",
    },
    {
        "cv": "test_cvs/ahmed_backend.docx",
        "job_title": "Frontend React Developer",
        "job_description": "Build modern web interfaces using React, JavaScript, and CSS.",
        "required_skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"],
        "expected": "LOW - Ahmed is a backend dev, not frontend",
    },
    {
        "cv": "test_cvs/mahmoud_devops.docx",
        "job_title": "DevOps Engineer",
        "job_description": "Manage cloud infrastructure with AWS, Kubernetes, Terraform, and CI/CD pipelines.",
        "required_skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux"],
        "expected": "HIGH - Mahmoud is a perfect DevOps match",
    },
    {
        "cv": "test_cvs/mahmoud_devops.docx",
        "job_title": "Data Scientist",
        "job_description": "Analyze data and build ML models using Python, Pandas, and Scikit-Learn.",
        "required_skills": ["Python", "Machine Learning", "Pandas", "Scikit-Learn", "SQL"],
        "expected": "LOW - Mahmoud is DevOps, not Data Science",
    },
    {
        "cv": "test_cvs/sarah_frontend.docx",
        "job_title": "Frontend React Developer",
        "job_description": "Build responsive web applications using React and modern JavaScript.",
        "required_skills": ["React", "JavaScript", "HTML", "CSS", "Git"],
        "expected": "HIGH - Sarah is a perfect frontend match",
    },
    {
        "cv": "test_cvs/omar_data_scientist.docx",
        "job_title": "Machine Learning Engineer",
        "job_description": "Build ML models and NLP systems using Python, PyTorch, and Transformers.",
        "required_skills": ["Python", "Machine Learning", "PyTorch", "NLP", "Transformers", "Scikit-Learn"],
        "expected": "HIGH - Omar is a perfect ML match",
    },
    {
        "cv": "test_cvs/nour_mobile.docx",
        "job_title": "DevOps Engineer",
        "job_description": "Manage cloud infrastructure with AWS, Kubernetes, and Terraform.",
        "required_skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD"],
        "expected": "LOW - Nour is mobile dev, not DevOps",
    },
]


def run_diagnostics():
    extractor = SkillExtractor()
    service = MatchingService()
    
    print("=" * 80)
    print("  APPLY JOB SCORING DIAGNOSTIC")
    print("=" * 80)
    
    for i, tc in enumerate(TEST_CASES, 1):
        cv_path = tc["cv"]
        if not os.path.exists(cv_path):
            print(f"\n[SKIP] {cv_path} not found")
            continue
        
        with open(cv_path, "rb") as f:
            file_bytes = f.read()
        
        filename = os.path.basename(cv_path)
        text = extract_text_from_resume(file_bytes, filename)
        
        # Step 1: Extract skills from CV
        cv_skills = extractor.extract(text)
        
        # Step 2: What candidate_skills are fed to matcher
        candidate_skills = extract_candidate_skills(text, cv_skills)
        
        # Step 3: Normalize job skills
        job_skills_normalized = normalize_skills(tc["required_skills"])
        
        # Step 4: Run match
        result = match_job_to_candidate(
            job_skills=tc["required_skills"],
            candidate_skills=candidate_skills,
            candidate_level=service._infer_seniority(text),
            job_level=service._infer_seniority(f"{tc['job_title']} {tc['job_description']}"),
            candidate_domain=service._infer_domain(text),
            job_domain=service._infer_domain(f"{tc['job_title']} {tc['job_description']}"),
        )
        
        # Print results
        print(f"\n{'=' * 80}")
        print(f"  TEST {i}: {filename} -> {tc['job_title']}")
        print(f"  EXPECTED: {tc['expected']}")
        print(f"{'=' * 80}")
        print(f"  Raw CV text (first 200 chars): {text[:200].strip()}")
        print(f"  Extracted CV Skills: {cv_skills}")
        print(f"  Candidate Skills (normalized): {candidate_skills}")
        print(f"  Job Required Skills (normalized): {job_skills_normalized}")
        print(f"  ---")
        print(f"  Matched: {result.matched_skills}")
        print(f"  Missing: {result.missing_skills}")
        print(f"  Score: {result.score * 100:.1f}%")
        print(f"  Match Level: {result.match_level}")
        print(f"  Penalties: {result.penalties}")
        print(f"  Reason: {result.reason}")
        
        # Verdict
        is_good_match = "HIGH" in tc["expected"]
        score_pct = result.score * 100
        if is_good_match and score_pct < 60:
            print(f"  [FAIL] PROBLEM: Expected HIGH match but got {score_pct:.1f}%")
        elif not is_good_match and score_pct > 50:
            print(f"  [FAIL] PROBLEM: Expected LOW match but got {score_pct:.1f}%")
        else:
            print(f"  [OK] PASS")


if __name__ == "__main__":
    run_diagnostics()
