from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoleRequirements:
    role_name: str
    domain: str
    required_skills: list[str] = field(default_factory=list)
    advanced_skills: list[str] = field(default_factory=list)


ROLE_REQUIREMENT_MAP: dict[str, RoleRequirements] = {
    "DevOps Engineer": RoleRequirements(
        role_name="DevOps Engineer",
        domain="devops",
        required_skills=["kubernetes", "terraform", "ci/cd", "aws", "monitoring", "docker"],
        advanced_skills=["aws", "monitoring", "terraform"],
    ),
    "Infrastructure Automation Engineer": RoleRequirements(
        role_name="Infrastructure Automation Engineer",
        domain="devops",
        required_skills=["terraform", "ansible", "kubernetes", "ci/cd", "infrastructure automation"],
        advanced_skills=["terraform", "ansible", "infrastructure automation"],
    ),
    "Site Reliability Engineer": RoleRequirements(
        role_name="Site Reliability Engineer",
        domain="devops",
        required_skills=["monitoring", "observability", "incident response", "ci/cd", "kubernetes"],
        advanced_skills=["observability", "incident response", "monitoring"],
    ),
    "Cloud Operations Engineer": RoleRequirements(
        role_name="Cloud Operations Engineer",
        domain="cloud_platform",
        required_skills=["aws", "cloud architecture", "multi-account architecture", "monitoring", "kubernetes"],
        advanced_skills=["aws", "cloud architecture", "multi-account architecture"],
    ),
    "Platform Engineer": RoleRequirements(
        role_name="Platform Engineer",
        domain="cloud_platform",
        required_skills=["system design", "kubernetes", "docker", "observability", "cloud architecture"],
        advanced_skills=["system design", "observability", "cloud architecture"],
    ),
    "Cloud DevOps Engineer": RoleRequirements(
        role_name="Cloud DevOps Engineer",
        domain="cloud_platform",
        required_skills=["aws", "kubernetes", "terraform", "ci/cd", "monitoring"],
        advanced_skills=["aws", "terraform", "cloud architecture"],
    ),
    "Backend AI Engineer": RoleRequirements(
        role_name="Backend AI Engineer",
        domain="backend_ai",
        required_skills=["python", "fastapi", "rest api", "docker", "machine learning"],
        advanced_skills=["fastapi", "rest api", "machine learning"],
    ),
    "AI API Engineer": RoleRequirements(
        role_name="AI API Engineer",
        domain="backend_ai",
        required_skills=["python", "fastapi", "rest api", "docker", "model deployment"],
        advanced_skills=["fastapi", "model deployment", "rest api"],
    ),
    "Model Serving Engineer": RoleRequirements(
        role_name="Model Serving Engineer",
        domain="backend_ai",
        required_skills=["python", "fastapi", "model deployment", "docker", "cloud architecture"],
        advanced_skills=["model deployment", "cloud architecture"],
    ),
    "Intelligent Backend Engineer": RoleRequirements(
        role_name="Intelligent Backend Engineer",
        domain="backend_ai",
        required_skills=["python", "fastapi", "machine learning", "docker", "rest api"],
        advanced_skills=["machine learning", "rest api"],
    ),
    "Applied ML Backend Engineer": RoleRequirements(
        role_name="Applied ML Backend Engineer",
        domain="backend_ai",
        required_skills=["python", "machine learning", "model deployment", "fastapi", "docker"],
        advanced_skills=["machine learning", "model deployment"],
    ),
    "NLP Engineer": RoleRequirements(
        role_name="NLP Engineer",
        domain="ai_nlp",
        required_skills=["nlp", "machine learning", "transformers", "sentence-transformers", "information retrieval"],
        advanced_skills=["information retrieval", "sentence-transformers", "nlp"],
    ),
    "AI Engineer": RoleRequirements(
        role_name="AI Engineer",
        domain="ai_nlp",
        required_skills=["machine learning", "python", "model deployment", "model evaluation", "cloud architecture"],
        advanced_skills=["model deployment", "cloud architecture", "machine learning"],
    ),
    "Machine Learning Engineer": RoleRequirements(
        role_name="Machine Learning Engineer",
        domain="ai_nlp",
        required_skills=["machine learning", "python", "feature engineering", "model evaluation", "statistics"],
        advanced_skills=["feature engineering", "model evaluation", "statistics"],
    ),
    "Applied LLM Engineer": RoleRequirements(
        role_name="Applied LLM Engineer",
        domain="ai_nlp",
        required_skills=["llm", "rag", "prompt engineering", "transformers", "model deployment"],
        advanced_skills=["llm", "rag", "prompt engineering"],
    ),
    "Language AI Engineer": RoleRequirements(
        role_name="Language AI Engineer",
        domain="ai_nlp",
        required_skills=["nlp", "sentence-transformers", "information retrieval", "model evaluation", "prompt engineering"],
        advanced_skills=["sentence-transformers", "information retrieval", "prompt engineering"],
    ),
    "Telecom Network Engineer": RoleRequirements(
        role_name="Telecom Network Engineer",
        domain="telecom_network",
        required_skills=["telecommunications", "fiber optics", "routing", "switching", "network integration"],
        advanced_skills=["telecommunications", "fiber optics", "network integration"],
    ),
    "Network Engineer": RoleRequirements(
        role_name="Network Engineer",
        domain="telecom_network",
        required_skills=["routing", "switching", "tcp/ip", "network troubleshooting", "cisco"],
        advanced_skills=["network troubleshooting", "tcp/ip"],
    ),
    "Network Operations Engineer": RoleRequirements(
        role_name="Network Operations Engineer",
        domain="telecom_network",
        required_skills=["network operations", "noc", "monitoring", "network troubleshooting", "routing"],
        advanced_skills=["network operations", "noc", "monitoring"],
    ),
    "Wireless Network Engineer": RoleRequirements(
        role_name="Wireless Network Engineer",
        domain="telecom_network",
        required_skills=["wireless networking", "wimax", "microwave links", "site survey", "network integration"],
        advanced_skills=["wireless networking", "network integration"],
    ),
    "Infrastructure Support Engineer": RoleRequirements(
        role_name="Infrastructure Support Engineer",
        domain="telecom_network",
        required_skills=["network operations", "monitoring", "linux", "incident response", "cloud architecture"],
        advanced_skills=["incident response", "cloud architecture"],
    ),
    "Cloud Infrastructure Engineer": RoleRequirements(
        role_name="Cloud Infrastructure Engineer",
        domain="cloud_platform",
        required_skills=["aws", "azure", "terraform", "kubernetes", "monitoring"],
        advanced_skills=["aws", "terraform", "cloud architecture"],
    ),
    "Cloud Reliability Engineer": RoleRequirements(
        role_name="Cloud Reliability Engineer",
        domain="cloud_platform",
        required_skills=["monitoring", "observability", "incident response", "aws", "kubernetes"],
        advanced_skills=["observability", "incident response", "aws"],
    ),
    "Infrastructure Engineer": RoleRequirements(
        role_name="Infrastructure Engineer",
        domain="cloud_platform",
        required_skills=["kubernetes", "docker", "aws", "monitoring", "system design"],
        advanced_skills=["system design", "aws"],
    ),
}


def build_role_requirements(role_name: str, domain: str) -> RoleRequirements:
    requirement = ROLE_REQUIREMENT_MAP.get(role_name)
    if requirement:
        return requirement

    fallback = {
        "backend_ai": RoleRequirements(role_name=role_name, domain=domain, required_skills=["python", "fastapi", "docker", "rest api"], advanced_skills=["fastapi", "rest api"]),
        "devops": RoleRequirements(role_name=role_name, domain=domain, required_skills=["kubernetes", "terraform", "aws", "monitoring"], advanced_skills=["aws", "monitoring"]),
        "ai_nlp": RoleRequirements(role_name=role_name, domain=domain, required_skills=["machine learning", "nlp", "transformers", "model evaluation"], advanced_skills=["machine learning", "model evaluation"]),
        "telecom_network": RoleRequirements(role_name=role_name, domain=domain, required_skills=["routing", "switching", "network operations", "monitoring"], advanced_skills=["network operations", "monitoring"]),
        "cloud_platform": RoleRequirements(role_name=role_name, domain=domain, required_skills=["aws", "kubernetes", "terraform", "monitoring"], advanced_skills=["aws", "terraform"]),
    }
    return fallback.get(domain, RoleRequirements(role_name=role_name, domain=domain, required_skills=["system design", "problem solving", "git"], advanced_skills=["system design"]))


def generate_dynamic_roles(primary_domain: str, secondary_domains: list[str], skills: list[str], level: str) -> list[str]:
    domain_roles = {
        "backend_ai": ["Backend AI Engineer", "AI API Engineer", "Model Serving Engineer", "Intelligent Backend Engineer", "Applied ML Backend Engineer"],
        "devops": ["DevOps Engineer", "Infrastructure Automation Engineer", "Site Reliability Engineer", "Cloud Operations Engineer", "Platform Engineer"],
        "ai_nlp": ["NLP Engineer", "AI Engineer", "Machine Learning Engineer", "Applied LLM Engineer", "Language AI Engineer"],
        "data_ml": ["Machine Learning Engineer", "Data Scientist", "Analytics Engineer", "Applied Data Engineer", "ML Systems Engineer"],
        "telecom_network": ["Telecom Network Engineer", "Network Engineer", "Network Operations Engineer", "Wireless Network Engineer", "Infrastructure Support Engineer"],
        "cloud_platform": ["Cloud Infrastructure Engineer", "Platform Engineer", "Cloud Reliability Engineer", "Cloud DevOps Engineer", "Infrastructure Engineer"],
    }

    role_pool: list[str] = []
    for domain in [primary_domain, *secondary_domains]:
        role_pool.extend(domain_roles.get(domain, []))

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

    ordered: list[str] = []
    seen: set[str] = set()
    for role in role_pool:
        lowered = role.lower()
        if lowered not in seen:
            seen.add(lowered)
            ordered.append(role)
    return ordered[:5]
