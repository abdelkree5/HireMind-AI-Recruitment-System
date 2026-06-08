"""Diagnostic script: test the Apply Job scoring pipeline offline and evaluate retrieval metrics."""
from __future__ import annotations
import os
import sys
import io
import json
from math import log2

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ai_engine.parser import ResumeParser
from ai_engine.skills import SkillExtractor
from ai_engine.matcher import RecruitmentMatcher

# ---- Test scenarios ----
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

# Ground Truth for Retrieval Scenarios (relevance binary labels)
RETRIEVAL_SCENARIOS = [
    {
        "query_title": "DevOps Engineer",
        "query_desc": "Manage cloud infrastructure with AWS, Kubernetes, Terraform, and CI/CD pipelines.",
        "required_skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux"],
        "ground_truth": {
            "mahmoud_devops.docx": 1,
            "ahmed_backend.docx": 0,
            "sarah_frontend.docx": 0,
            "omar_data_scientist.docx": 0,
            "nour_mobile.docx": 0
        }
    },
    {
        "query_title": "Backend Python Developer",
        "query_desc": "Build and maintain REST APIs using Python and FastAPI. Work with PostgreSQL and Docker.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Git"],
        "ground_truth": {
            "ahmed_backend.docx": 1,
            "mahmoud_devops.docx": 0,
            "sarah_frontend.docx": 0,
            "omar_data_scientist.docx": 0,
            "nour_mobile.docx": 0
        }
    },
    {
        "query_title": "Frontend React Developer",
        "query_desc": "Build modern web interfaces using React, JavaScript, and CSS.",
        "required_skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"],
        "ground_truth": {
            "sarah_frontend.docx": 1,
            "ahmed_backend.docx": 0,
            "mahmoud_devops.docx": 0,
            "omar_data_scientist.docx": 0,
            "nour_mobile.docx": 0
        }
    }
]

def run_diagnostics():
    parser = ResumeParser()
    extractor = SkillExtractor()
    matcher = RecruitmentMatcher()
    
    print("=" * 80)
    print("  APPLY JOB SCORING DIAGNOSTIC (6-STAGE HYBRID RAG)")
    print("=" * 80)
    
    # Run test cases
    for i, tc in enumerate(TEST_CASES, 1):
        cv_path = tc["cv"]
        if not os.path.exists(cv_path):
            print(f"\n[SKIP] {cv_path} not found")
            continue
        
        with open(cv_path, "rb") as f:
            file_bytes = f.read()
        
        filename = os.path.basename(cv_path)
        text = parser.parse(file_bytes, filename)
        
        # Step 1: Extract skills from CV
        cv_skills = extractor.extract(text)
        
        # Step 2: Score CV against job
        report = matcher.score(
            candidate_text=text,
            candidate_skills=cv_skills,
            job_title=tc["job_title"],
            job_description=tc["job_description"],
            required_skills=tc["required_skills"],
        )
        
        # Print results
        print(f"\n{'=' * 80}")
        print(f"  TEST {i}: {filename} -> {tc['job_title']}")
        print(f"  EXPECTED: {tc['expected']}")
        print(f"{'=' * 80}")
        print(f"  Raw CV text (first 100 chars): {text[:100].strip()}...")
        print(f"  Extracted CV Skills: {cv_skills[:8]}...")
        print(f"  ---")
        print(f"  Matched: {report.matched_skills}")
        print(f"  Missing: {report.missing_skills}")
        print(f"  Final Confidence Score: {report.match_percentage:.1f}%")
        print(f"  Recommendation: {report.recommendation}")
        print(f"  Penalties: {report.penalties}")
        print(f"  Score Breakdown: {report.score_breakdown}")
        print(f"  Explainable justification: {report.reason}")
        
        # Verdict
        is_good_match = "HIGH" in tc["expected"]
        score_pct = report.match_percentage
        if is_good_match and score_pct < 60:
            print(f"  [FAIL] PROBLEM: Expected HIGH match but got {score_pct:.1f}%")
        elif not is_good_match and score_pct > 50:
            print(f"  [FAIL] PROBLEM: Expected LOW match but got {score_pct:.1f}%")
        else:
            print(f"  [OK] PASS")
            
    # Run Retrieval Metrics Evaluation
    print("\n" + "=" * 80)
    print("  RETRIEVAL METRICS EVALUATION")
    print("=" * 80)
    
    all_cvs = []
    cv_filenames = ["ahmed_backend.docx", "mahmoud_devops.docx", "sarah_frontend.docx", "omar_data_scientist.docx", "nour_mobile.docx"]
    for cv_name in cv_filenames:
        cv_path = f"test_cvs/{cv_name}"
        if os.path.exists(cv_path):
            with open(cv_path, "rb") as f:
                file_bytes = f.read()
            text = parser.parse(file_bytes, cv_name)
            skills = extractor.extract(text)
            all_cvs.append({
                "id": cv_name,
                "name": cv_name.split("_")[0].title(),
                "text": text,
                "skills": skills
            })
            
    if len(all_cvs) < 5:
        print("[SKIP] Not enough resumes parsed to run retrieval metrics evaluation.")
        return
        
    for scenario in RETRIEVAL_SCENARIOS:
        print(f"\nQuerying: {scenario['query_title']}")
        # Format ground truth keys to candidate names
        gt = {}
        for filename, rel in scenario["ground_truth"].items():
            name = filename.split("_")[0].title()
            gt[name] = rel
            
        ranked_reports = matcher.retrieve_and_rank(
            candidates=all_cvs,
            job_title=scenario["query_title"],
            job_description=scenario["query_desc"],
            required_skills=scenario["required_skills"],
            experience_level="",
            domain="",
            ground_truth=gt
        )
        
        print("Rankings:")
        for idx, r in enumerate(ranked_reports, 1):
            name = r.reason.split(" is ")[0]
            print(f"  {idx}. {name:15} | Match Score: {r.match_percentage:.1f}% | Reranker: {r.reranker_score:.3f}")
            
    # Read metrics history
    if os.path.exists("database/metrics_history.json"):
        with open("database/metrics_history.json", "r") as f:
            history = json.load(f)
            
        if history:
            latest = history[-1]
            print("\n" + "=" * 80)
            print("  LATEST RETRIEVAL METRICS LOGGED")
            print("=" * 80)
            print(f"  Precision@5:  {latest['precision_at_5']:.2f}")
            print(f"  Precision@10: {latest['precision_at_10']:.2f}")
            print(f"  Recall@5:     {latest['recall_at_5']:.2f}")
            print(f"  Recall@10:    {latest['recall_at_10']:.2f}")
            print(f"  MRR:          {latest['mrr']:.2f}")
            print(f"  NDCG@10:      {latest['ndcg_at_10']:.2f}")


if __name__ == "__main__":
    run_diagnostics()
