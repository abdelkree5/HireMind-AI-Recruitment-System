import json
import os
import random
import threading
from typing import Any

from locust import HttpUser, between, task
from locust.exception import StopUser

PERF_TEST_EMAIL = os.getenv("PERF_TEST_EMAIL", "perf+recruiter@hiremind.test")
PERF_TEST_PASSWORD = os.getenv("PERF_TEST_PASSWORD", "PerfTest123!")
PERF_TEST_FULL_NAME = os.getenv("PERF_TEST_FULL_NAME", "HireMind Performance Recruiter")
PERF_TEST_COMPANY_NAME = os.getenv("PERF_TEST_COMPANY_NAME", "HireMind Performance")
PERF_TEST_BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
RESUME_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_resume.txt")

JOB_CREATION_LOCK = threading.Lock()
SHARED_JOB_ID: str | None = None


def load_sample_resume() -> bytes:
    with open(RESUME_PATH, "rb") as f:
        return f.read()


def random_job_payload() -> dict[str, Any]:
    role = random.choice(["Backend Engineer", "Data Scientist", "DevOps Lead", "Product Analyst"])
    return {
        "title": f"Senior {role}",
        "description": (
            "We are hiring a proven technical leader with experience building scalable enterprise systems. "
            "Strong skills in Python, cloud infrastructure, and data-driven decision-making are required."
        ),
        "required_skills": ["python", "fastapi", "sql", "docker"],
        "responsibilities": [
            "Design, build, and maintain backend services.",
            "Collaborate with cross-functional teams.",
            "Drive data-informed product decisions.",
        ],
        "preferred_skills": ["postgresql", "rabbitmq", "cloud architecture"],
        "tools": ["git", "docker", "kubernetes"],
        "experience_level": "Senior",
        "domain": "software_engineering",
        "hiring_rules": {
            "mandatory_skills": ["python", "sql"],
            "preferred_skills": ["docker", "cloud"],
            "min_experience_years": 5,
        },
    }


def random_candidate_profile() -> dict[str, Any]:
    return {
        "name": random.choice(["Amina Ahmed", "Omar El-Sayed", "Nour Hassan", "Sara Youssef"]),
        "headline": "Experienced software engineer with full-stack and AI pipeline expertise.",
        "skills": ["python", "fastapi", "sql", "docker", "postgresql"],
        "summary": (
            "Delivered enterprise SaaS and hiring workflow automation using Python, cloud-native services, and intelligent hiring workflows."
        ),
        "experience_years": random.randint(5, 12),
        "education": "Bachelor of Science in Computer Engineering",
        "location": random.choice(["Cairo, Egypt", "Dubai, UAE", "Riyadh, KSA", "Amman, Jordan"]),
        "certifications": ["AWS Certified Developer", "Certified Scrum Master"],
    }


def get_auth_token(user: HttpUser) -> str | None:
    payload = {"email": PERF_TEST_EMAIL, "password": PERF_TEST_PASSWORD}
    res = user.client.post("/api/auth/login", json=payload)
    if res.status_code == 200:
        return res.json().get("session_token")
    return None


def register_test_user(user: HttpUser) -> str | None:
    payload = {
        "email": PERF_TEST_EMAIL,
        "password": PERF_TEST_PASSWORD,
        "full_name": PERF_TEST_FULL_NAME,
        "role": "company",
        "company_name": PERF_TEST_COMPANY_NAME,
    }
    res = user.client.post("/api/auth/register", json=payload)
    if res.status_code in (200, 201):
        return get_auth_token(user)
    return None


class BasePerfUser(HttpUser):
    abstract = True
    host = PERF_TEST_BASE_URL
    wait_time = between(1, 3)

    def on_start(self):
        import uuid
        self.email = f"perf_{uuid.uuid4().hex[:8]}@hiremind.test"
        
        token = self._register_and_login()
        if token is None:
            raise StopUser("Unable to authenticate performance test user.")

        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.resume_data = load_sample_resume()
        self.job_id = self._ensure_job_exists()

    def _register_and_login(self) -> str | None:
        payload = {
            "email": self.email,
            "password": PERF_TEST_PASSWORD,
            "full_name": PERF_TEST_FULL_NAME,
            "role": "company",
            "company_name": PERF_TEST_COMPANY_NAME,
        }
        res = self.client.post("/api/auth/register", json=payload)
        if res.status_code in (200, 201):
            login_res = self.client.post("/api/auth/login", json={"email": self.email, "password": PERF_TEST_PASSWORD})
            if login_res.status_code == 200:
                return login_res.json().get("access_token")
        return None

    def _ensure_job_exists(self) -> str:
        global SHARED_JOB_ID
        with JOB_CREATION_LOCK:
            if SHARED_JOB_ID is not None:
                return SHARED_JOB_ID

            payload = random_job_payload()
            res = self.client.post("/api/jobs/posted", json=payload, headers=self.headers)
            if res.status_code in (200, 201):
                SHARED_JOB_ID = res.json().get("id")
            else:
                raise StopUser(f"Failed to create shared job: {res.status_code} {res.text}")

            if not SHARED_JOB_ID:
                raise StopUser("Shared job ID could not be retrieved.")

        return SHARED_JOB_ID

    def _upload_resume(self):
        files = {"file": ("resume.txt", self.resume_data, "text/plain")}
        data = {
            "job_title": "Backend Engineer",
            "job_description": "Enterprise resume upload test for performance validation.",
            "required_skills": json.dumps(["python", "sql", "fastapi"]),
        }
        with self.client.post("/api/cv/analyze", headers=self.headers, files=files, data=data, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Resume analysis failed: {response.status_code} {response.text}")

    def _top_matches_from_cv(self):
        files = {"file": ("resume.txt", self.resume_data, "text/plain")}
        with self.client.post("/api/jobs/top-matches/general-from-cv", headers=self.headers, files=files, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Top matches failed: {response.status_code} {response.text}")

    def _run_supervisor_workflow(self):
        payload = {
            "job_id": self.job_id,
            "cv_text": "Experienced backend engineer with deployment and performance experience.",
        }
        with self.client.post("/api/agents/pipeline/run", headers={**self.headers, "Content-Type": "application/json"}, json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Workflow execution failed: {response.status_code} {response.text}")


class CandidateUploadUser(BasePerfUser):
    @task
    def candidate_resume_upload(self):
        self._upload_resume()


class CandidateMatchingUser(BasePerfUser):
    @task
    def candidate_matching(self):
        self._top_matches_from_cv()


class RecruiterWorkflowUser(BasePerfUser):
    @task
    def recruiter_workflow(self):
        self._upload_resume()
        self._top_matches_from_cv()


class MultiAgentWorkflowUser(BasePerfUser):
    @task
    def multi_agent_workflow(self):
        self._run_supervisor_workflow()
