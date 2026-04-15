from __future__ import annotations

from typing import Iterable


DOMAIN_ROLE_TEMPLATES = {
    "backend_ai": [
        "Backend AI Engineer",
        "AI API Engineer",
        "Model Serving Engineer",
        "Intelligent Backend Engineer",
        "Applied ML Backend Engineer",
    ],
    "devops": [
        "DevOps Engineer",
        "Infrastructure Automation Engineer",
        "Site Reliability Engineer",
        "Cloud Operations Engineer",
        "Platform Engineer",
    ],
    "ai_nlp": [
        "NLP Engineer",
        "AI Engineer",
        "Machine Learning Engineer",
        "Applied LLM Engineer",
        "Language AI Engineer",
    ],
    "data_ml": [
        "Machine Learning Engineer",
        "Data Scientist",
        "Analytics Engineer",
        "Applied Data Engineer",
        "ML Systems Engineer",
    ],
    "telecom_network": [
        "Telecom Network Engineer",
        "Network Engineer",
        "Network Operations Engineer",
        "Wireless Network Engineer",
        "Infrastructure Support Engineer",
    ],
    "cloud_platform": [
        "Cloud Infrastructure Engineer",
        "Platform Engineer",
        "Cloud Reliability Engineer",
        "Cloud DevOps Engineer",
        "Infrastructure Engineer",
    ],
}

TAG_REQUIREMENTS = {
    "ai": {
        "technical": ["python", "machine learning"],
        "practical": ["model deployment"],
        "tools": ["scikit-learn", "pytorch"],
    },
    "nlp": {
        "technical": ["nlp", "machine learning"],
        "practical": ["model evaluation"],
        "tools": ["transformers", "sentence-transformers"],
    },
    "backend": {
        "technical": ["python", "rest api"],
        "practical": ["docker"],
        "tools": ["fastapi", "flask"],
    },
    "devops": {
        "technical": ["kubernetes", "terraform"],
        "practical": ["docker"],
        "tools": ["aws", "monitoring"],
    },
    "cloud": {
        "technical": ["aws", "azure"],
        "practical": ["kubernetes"],
        "tools": ["terraform", "monitoring"],
    },
    "data": {
        "technical": ["sql", "feature engineering"],
        "practical": ["machine learning"],
        "tools": ["pandas", "numpy"],
    },
    "network": {
        "technical": ["routing", "switching"],
        "practical": ["network troubleshooting"],
        "tools": ["cisco", "noc"],
    },
    "telecom": {
        "technical": ["telecommunications", "fiber optics"],
        "practical": ["site survey"],
        "tools": ["wimax", "microwave"],
    },
    "platform": {
        "technical": ["kubernetes", "docker"],
        "practical": ["monitoring"],
        "tools": ["prometheus", "linux"],
    },
}


def role_tags(role_name: str, primary_domain: str) -> set[str]:
    lowered = role_name.lower()
    tags = set()

    if any(token in lowered for token in ["ai", "ml", "machine learning"]):
        tags.add("ai")
    if any(token in lowered for token in ["nlp", "language", "llm"]):
        tags.add("nlp")
    if any(token in lowered for token in ["backend", "api", "serving"]):
        tags.add("backend")
    if any(token in lowered for token in ["devops", "reliability", "operations", "sre"]):
        tags.add("devops")
    if any(token in lowered for token in ["cloud", "infrastructure"]):
        tags.add("cloud")
    if any(token in lowered for token in ["data", "analytics"]):
        tags.add("data")
    if any(token in lowered for token in ["network", "noc", "wireless"]):
        tags.add("network")
    if "telecom" in lowered:
        tags.add("telecom")
    if "platform" in lowered:
        tags.add("platform")

    domain_tag_map = {
        "backend_ai": {"backend", "ai"},
        "devops": {"devops", "cloud"},
        "ai_nlp": {"ai", "nlp"},
        "data_ml": {"data", "ai"},
        "telecom_network": {"telecom", "network"},
        "cloud_platform": {"cloud", "platform", "devops"},
    }
    tags |= domain_tag_map.get(primary_domain, set())

    return tags


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = item.strip()
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        seen.add(lowered)
        result.append(cleaned)
    return result


def build_role_requirements(role_name: str, primary_domain: str) -> dict[str, list[str]]:
    tags = role_tags(role_name, primary_domain)
    grouped = {"technical": [], "practical": [], "tools": []}

    primary_tag_map = {
        "backend_ai": "backend",
        "devops": "devops",
        "ai_nlp": "nlp",
        "data_ml": "data",
        "telecom_network": "telecom",
        "cloud_platform": "cloud",
    }
    primary_tag = primary_tag_map.get(primary_domain)

    if primary_tag and primary_tag in tags:
        requirement = TAG_REQUIREMENTS.get(primary_tag)
    else:
        requirement = None

    if requirement:
        limits = {
            "technical": 3,
            "practical": 1,
            "tools": 1,
        }
        for group in grouped:
            grouped[group].extend(requirement[group][: limits[group]])

    for tag in sorted(tags - ({primary_tag} if primary_tag else set())):
        requirement = TAG_REQUIREMENTS.get(tag)
        if not requirement:
            continue

        limits = {
            "technical": 0,
            "practical": 0,
            "tools": 0,
        }
        for group in grouped:
            grouped[group].extend(requirement[group][: limits[group]])

    if "llm" in role_name.lower():
        grouped["technical"].extend(["llm", "rag"])
        grouped["tools"].append("transformers")
    if "nlp" in role_name.lower() or "language" in role_name.lower():
        grouped["technical"].extend(["nlp", "information retrieval"])
        grouped["practical"].append("model evaluation")
    if "language ai engineer" in role_name.lower():
        grouped["technical"].extend(["sentence-transformers", "information retrieval"])
        grouped["practical"].append("prompt engineering")
    if "applied llm" in role_name.lower():
        grouped["technical"].extend(["llm", "rag", "prompt engineering"])
        grouped["practical"].extend(["model deployment", "evaluation metrics"])
        grouped["tools"].append("transformers")
    if "machine learning engineer" in role_name.lower():
        grouped["technical"].extend(["machine learning", "feature engineering", "statistics"])
        grouped["practical"].append("model evaluation")
    if "ai engineer" in role_name.lower() and "machine learning engineer" not in role_name.lower():
        grouped["technical"].extend(["machine learning", "model deployment"])
        grouped["practical"].append("cloud architecture")
    if "backend" in role_name.lower() or "api" in role_name.lower():
        grouped["technical"].extend(["python", "fastapi", "rest api"])
        grouped["practical"].append("docker")
    if "devops" in role_name.lower() or "sre" in role_name.lower() or "reliability" in role_name.lower():
        grouped["technical"].extend(["kubernetes", "terraform", "infrastructure automation"])
        grouped["practical"].extend(["observability", "ci/cd"])
        grouped["tools"].append("prometheus")
    if "site reliability engineer" in role_name.lower():
        grouped["technical"].extend(["ci/cd", "monitoring"])
        grouped["practical"].append("incident response")
    if "cloud operations engineer" in role_name.lower():
        grouped["technical"].extend(["cloud architecture", "multi-account architecture"])
        grouped["practical"].append("observability")
    if "infrastructure automation engineer" in role_name.lower():
        grouped["technical"].extend(["terraform", "ansible"])
        grouped["practical"].append("infrastructure automation")
    if "cloud" in role_name.lower():
        grouped["technical"].extend(["aws", "azure", "cloud architecture"])
        grouped["practical"].append("multi-account architecture")
    if "telecom" in role_name.lower() or "network" in role_name.lower():
        grouped["technical"].extend(["routing", "switching", "network operations"])
        grouped["practical"].append("network integration")
    if "platform" in role_name.lower():
        grouped["technical"].extend(["system design", "cloud architecture"])
        grouped["practical"].extend(["monitoring", "observability"])

    grouped = {key: _dedupe(values)[:4] for key, values in grouped.items()}
    if not any(grouped.values()):
        grouped = {
            "technical": ["system design", "problem solving"],
            "practical": ["implementation experience", "production support"],
            "tools": ["git", "linux"],
        }
    return grouped


def generate_dynamic_roles(primary_domain: str, secondary_domains: list[str], skills: list[str], level: str) -> list[str]:
    domains = [primary_domain, *secondary_domains]
    role_pool: list[str] = []
    for domain in domains:
        role_pool.extend(DOMAIN_ROLE_TEMPLATES.get(domain, []))

    normalized_skills = {skill.lower().strip() for skill in skills}
    if "rag" in normalized_skills or "llm" in normalized_skills:
        role_pool.append("LLM Application Engineer")
    if "fastapi" in normalized_skills and "docker" in normalized_skills:
        role_pool.append("Backend Platform Engineer")
    if "kubernetes" in normalized_skills and ({"aws", "azure", "gcp"} & normalized_skills):
        role_pool.append("Cloud DevOps Engineer")
    if "fiber optics" in normalized_skills and "wimax" in normalized_skills:
        role_pool.append("Wireless Access Engineer")

    if level == "Senior":
        role_pool.extend(["Technical Lead Engineer", "Principal Engineer"])
    elif level == "Junior":
        role_pool.append("Associate Engineer")

    return _dedupe(role_pool)[:5]
