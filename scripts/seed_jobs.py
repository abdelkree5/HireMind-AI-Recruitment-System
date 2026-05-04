import json
import sqlite3
import uuid
from datetime import datetime

SAMPLE_JOBS = [
    {
        "title": "AI Engineer",
        "description": "Build NLP models and matching pipelines using embeddings and ranking.",
        "required_skills": ["python", "nlp", "sentence-transformers", "pytorch", "scikit-learn"],
    },
    {
        "title": "DevOps Engineer",
        "description": "Manage CI/CD, infrastructure automation, and system reliability.",
        "required_skills": ["docker", "kubernetes", "terraform", "ci/cd", "linux"],
    },
    # ... Add more if needed
]

def seed():
    conn = sqlite3.connect("recruitment.db")
    cursor = conn.cursor()
    
    for job in SAMPLE_JOBS:
        job_id = uuid.uuid4().hex
        cursor.execute(
            """
            INSERT OR IGNORE INTO posted_jobs (id, title, description, required_skills, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, job["title"], job["description"], json.dumps(job["required_skills"]), datetime.utcnow().isoformat())
        )
    
    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
