from __future__ import annotations
from pathlib import Path

BASE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FINETUNED_MODEL_DIR = Path(__file__).resolve().parent / "training" / "artifacts"

SEMANTIC_WEIGHT = 0.55
SKILL_WEIGHT = 0.25
TITLE_WEIGHT = 0.10
CONTEXT_WEIGHT = 0.10

ROLE_REQUIREMENT_MAP = {
    "DevOps Engineer": {
        "domain": "devops",
        "required_skills": ["kubernetes", "terraform", "ci/cd", "aws", "monitoring", "docker"],
    },
    "Backend AI Engineer": {
        "domain": "backend_ai",
        "required_skills": ["python", "fastapi", "rest api", "docker", "machine learning"],
    },
    "NLP Engineer": {
        "domain": "ai_nlp",
        "required_skills": ["nlp", "machine learning", "transformers", "sentence-transformers", "information retrieval"],
    },
    "Telecom Network Engineer": {
        "domain": "telecom_network",
        "required_skills": ["telecommunications", "fiber optics", "routing", "switching", "network integration"],
    },
}

DOMAIN_ROLES = {
    "backend_ai": ["Backend AI Engineer", "AI API Engineer", "Model Serving Engineer"],
    "devops": ["DevOps Engineer", "Infrastructure Automation Engineer", "Site Reliability Engineer"],
    "ai_nlp": ["NLP Engineer", "AI Engineer", "Machine Learning Engineer"],
    "telecom_network": ["Telecom Network Engineer", "Network Engineer", "Network Operations Engineer"],
}
