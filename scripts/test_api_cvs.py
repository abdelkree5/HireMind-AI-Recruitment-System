"""Test all 5 CVs against the full-analysis endpoint."""
import os
import glob
import json
import time
import requests

BASE = "http://127.0.0.1:8000"

# Login first
login_resp = requests.post(f"{BASE}/api/auth/login", json={
    "email": "company@hiremind.ai",
    "password": "HireMind123!"
})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Logged in successfully!\n")

cv_files = sorted(glob.glob("test_cvs/*.docx"))
results = []

for cv_path in cv_files:
    filename = os.path.basename(cv_path)
    print(f"{'='*60}")
    print(f"  CV: {filename}")
    print(f"{'='*60}")
    
    with open(cv_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/api/cv/full-analysis",
            files={"file": (filename, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
    
    data = resp.json()
    task_id = data["task_id"]
    
    # Poll for result
    for _ in range(30):
        time.sleep(2)
        sr = requests.get(f"{BASE}/api/tasks/{task_id}", headers=headers)
        sd = sr.json()
        if sd["status"] in ("completed", "failed"):
            break
    
    if sd["status"] == "failed":
        print(f"  FAILED: {sd.get('error')}")
        continue
    
    result = sd["result"]
    
    # Extract key info
    skills = result.get("extracted_skills", [])
    level = "N/A"
    domain = "N/A"
    for log in result.get("analysis_logs", []):
        if "Inferred level:" in log:
            level = log.split("Inferred level:")[1].strip()
        if "Main domain:" in log:
            domain = log.split("Main domain:")[1].strip()
    
    print(f"  Skills: {', '.join(skills[:10])}")
    print(f"  Level: {level}")
    print(f"  Domain: {domain}")
    
    # Top job matches
    matches = result.get("top_role_matches", [])
    if matches:
        print(f"  Top Role Matches:")
        for m in matches[:3]:
            print(f"    - {m['role_name']}: {m['confidence_score']:.0f}% ({m['match_level']})")
            print(f"      Matched: {', '.join(m.get('matched_skills', []))}")
            print(f"      Missing: {', '.join(m.get('missing_skills', []))}")
    
    # Strengths & weaknesses
    sw = result.get("strengths_vs_weaknesses", {})
    if sw:
        print(f"  Strengths: {'; '.join(sw.get('strengths', []))}")
        print(f"  Weaknesses: {'; '.join(sw.get('weaknesses', [])[:3])}")
    
    # Career growth
    cgp = result.get("career_growth_plan", {})
    if cgp:
        print(f"  Next Learning: {', '.join(cgp.get('next_learning_priorities', [])[:4])}")
    
    results.append({"cv": filename, "skills": skills, "level": level, "domain": domain})
    print()

print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
for r in results:
    print(f"  {r['cv']:30s} | Level: {r['level']:6s} | Domain: {r['domain']:15s} | Skills: {len(r['skills'])}")
print(f"\nAll {len(results)} CVs tested successfully!")
