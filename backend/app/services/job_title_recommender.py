from __future__ import annotations

from dataclasses import dataclass
import re

from backend.app.schemas import CandidateMatchResponse
from backend.app.services.matching_engine import build_role_requirements, generate_dynamic_roles
from backend.app.services.scoring_logic import compare_role_match
from backend.app.services.skill_extractor import DEFAULT_SKILL_VOCAB, SkillExtractor


EXTRA_SKILL_VOCAB = [
    "llm",
    "rag",
    "mlflow",
    "airflow",
    "terraform",
    "redis",
    "monitoring",
    "model deployment",
    "model evaluation",
    "information retrieval",
    "feature engineering",
    "data validation",
    "vector database",
    "langchain",
    "observability",
    "service reliability",
    "api design",
    "async backend",
    "network troubleshooting",
    "network integration",
    "site survey",
    "service decommissioning",
    "ticketing systems",
    "network monitoring",
    "cloud migration",
    "cost optimization",
]

DOMAIN_SKILL_GROUPS = {
    "backend_ai": {
        "python",
        "fastapi",
        "django",
        "flask",
        "docker",
        "machine learning",
        "model deployment",
        "api design",
        "rest api",
    },
    "devops": {
        "kubernetes",
        "docker",
        "terraform",
        "aws",
        "azure",
        "gcp",
        "ci/cd",
        "monitoring",
        "linux",
    },
    "ai_nlp": {
        "nlp",
        "transformers",
        "sentence-transformers",
        "llm",
        "rag",
        "machine learning",
        "scikit-learn",
        "pytorch",
        "tensorflow",
    },
    "data_ml": {
        "python",
        "sql",
        "pandas",
        "numpy",
        "statistics",
        "machine learning",
        "feature engineering",
    },
    "telecom_network": {
        "telecommunications",
        "telecom",
        "networking",
        "routing",
        "switching",
        "wan",
        "lan",
        "tcp/ip",
        "fiber optics",
        "wimax",
        "microwave",
        "cisco",
        "ccna",
        "network operations",
        "noc",
    },
    "cloud_platform": {
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "terraform",
        "prometheus",
        "grafana",
    },
}

DOMAIN_KEYWORDS = {
    "backend_ai": ["backend", "api", "inference", "serving", "fastapi", "model"],
    "devops": ["devops", "ci/cd", "deployment", "infrastructure", "automation", "sre"],
    "ai_nlp": ["nlp", "machine learning", "deep learning", "llm", "rag", "transformer"],
    "data_ml": ["data", "analytics", "dashboard", "feature", "statistics"],
    "telecom_network": ["telecom", "network", "wan", "lan", "fiber", "wimax", "microwave", "noc"],
    "cloud_platform": ["cloud", "aws", "azure", "gcp", "kubernetes", "terraform"],
}

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
        "technical": ["python", "machine learning", "deep learning"],
        "practical": ["model deployment", "model evaluation"],
        "tools": ["scikit-learn", "pytorch", "tensorflow"],
    },
    "nlp": {
        "technical": ["nlp", "information retrieval", "machine learning"],
        "practical": ["rag", "model evaluation"],
        "tools": ["transformers", "sentence-transformers"],
    },
    "backend": {
        "technical": ["python", "rest api", "sql"],
        "practical": ["docker", "microservices"],
        "tools": ["fastapi", "flask", "django"],
    },
    "devops": {
        "technical": ["ci/cd", "kubernetes", "terraform"],
        "practical": ["docker", "monitoring"],
        "tools": ["kubernetes", "terraform"],
    },
    "cloud": {
        "technical": ["aws", "azure", "gcp"],
        "practical": ["docker", "kubernetes"],
        "tools": ["aws", "azure", "gcp"],
    },
    "data": {
        "technical": ["sql", "statistics", "feature engineering"],
        "practical": ["machine learning", "model evaluation"],
        "tools": ["pandas", "numpy"],
    },
    "network": {
        "technical": ["routing", "switching", "tcp/ip"],
        "practical": ["network troubleshooting", "network operations"],
        "tools": ["cisco", "noc"],
    },
    "telecom": {
        "technical": ["telecommunications", "fiber optics", "wimax"],
        "practical": ["site survey", "network integration"],
        "tools": ["wimax", "microwave", "noc"],
    },
    "platform": {
        "technical": ["kubernetes", "docker", "microservices"],
        "practical": ["monitoring", "linux"],
        "tools": ["kubernetes", "prometheus"],
    },
}


@dataclass
class CandidateInsight:
    inferred_headline: str
    level: str
    years_of_experience: int
    primary_domain: str
    secondary_domains: list[str]
    skills: list[str]
    skill_evidence: dict[str, str]
    skill_depths: dict[str, str]
    leadership_score: float
    project_depth_score: float
    normalized_text: str


@dataclass
class RecommendationResult:
    total_catalog: int
    matches: list[CandidateMatchResponse]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _normalize_skill(skill: str) -> str:
    return _normalize(skill).replace("-", " ")


def _extract_years_of_experience(text: str) -> int:
    normalized = text.lower()
    explicit = [int(v) for v in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|year)", normalized)]
    if explicit:
        return max(explicit)

    spans = re.findall(r"(?:19|20)\d{2}\s*(?:-|to|–|—)\s*(?:present|current|(?:19|20)\d{2})", normalized)
    if spans:
        return min(10, len(spans) * 2)

    return 0


def _score_leadership(text: str) -> float:
    normalized = text.lower()
    keywords = ["lead", "led", "manager", "managed", "owner", "principal", "architect", "mentored"]
    hits = sum(normalized.count(token) for token in keywords)
    return min(1.0, hits / 4.0)


def _score_project_depth(text: str) -> float:
    normalized = text.lower()
    depth_terms = [
        "designed",
        "implemented",
        "built",
        "deployed",
        "integrated",
        "optimized",
        "maintained",
        "production",
        "architecture",
        "end-to-end",
    ]
    hits = sum(normalized.count(token) for token in depth_terms)
    return min(1.0, hits / 8.0)


def _score_skill_depths(skill_depths: dict[str, str]) -> float:
    if not skill_depths:
        return 0.0
    weights = {"Basic": 0.25, "Intermediate": 0.6, "Advanced": 1.0}
    values = [weights.get(depth, 0.25) for depth in skill_depths.values()]
    return round(sum(values) / len(values), 4)


def _infer_level(years: int, leadership_score: float, project_depth_score: float, text: str) -> str:
    normalized = text.lower()
    if years >= 7 or leadership_score >= 0.65 or any(token in normalized for token in ["principal", "staff"]):
        return "Senior"
    if years >= 3 or leadership_score >= 0.3 or project_depth_score >= 0.45 or "senior" in normalized:
        return "Mid"
    return "Junior"


def _match_level(confidence: float, depth_score: float, level: str) -> str:
    if confidence >= 0.7:
        return "High"
    if confidence >= 0.55 and depth_score >= 0.65:
        return "High"
    if confidence >= 0.45 and depth_score >= 0.8 and level == "Senior":
        return "High"
    if confidence >= 0.4 or depth_score >= 0.45:
        return "Medium"
    return "Low"


def _infer_headline(cv_text: str) -> str:
    lines = [line.strip(" -•\t") for line in cv_text.splitlines() if line.strip()]
    if not lines:
        return "CV Profile"

    blocked_labels = {
        "personal",
        "information",
        "curriculum vitae",
        "emailaddress",
        "telephone",
        "date",
        "position",
        "employer",
        "duties",
        "address",
        "idcardno",
    }

    def is_label_line(value: str) -> bool:
        lowered = re.sub(r"[^a-z0-9 ]", "", value.lower()).strip()
        return lowered in blocked_labels or len(lowered.split()) <= 1

    def clean_line(value: str) -> str:
        cleaned = re.sub(r"^[\s:\-–—|]+", "", value).strip()
        cleaned = re.sub(
            r"^(?:full\s*name(?:s)?|name|email\s*address|email|phone|telephone|mobile|position|title)\s*[:\-–—]*\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return re.sub(r"^[\s:\-–—|]+", "", cleaned).strip()

    role_hints = (
        "engineer",
        "developer",
        "scientist",
        "analyst",
        "architect",
        "specialist",
        "devops",
        "network",
        "telecom",
        "ai",
        "ml",
    )

    for line in lines[:14]:
        if is_label_line(line):
            continue
        if any(hint in line.lower() for hint in role_hints):
            candidate = clean_line(line)
            if candidate:
                return candidate

    for line in lines[:20]:
        if is_label_line(line):
            continue
        candidate = clean_line(line)
        if candidate and 3 <= len(candidate.split()) <= 18:
            return candidate

    fallback = clean_line(lines[0])
    return fallback or "CV Profile"


def _build_skill_extractor() -> SkillExtractor:
    vocab = sorted(set(DEFAULT_SKILL_VOCAB) | set(EXTRA_SKILL_VOCAB))
    return SkillExtractor(vocabulary=vocab)


def _domain_scores(skills: list[str], text: str) -> dict[str, float]:
    normalized_text = _normalize(text)
    skill_set = {_normalize_skill(skill) for skill in skills}
    scores: dict[str, float] = {}

    for domain, signals in DOMAIN_SKILL_GROUPS.items():
        signal_hits = sum(1 for signal in signals if _normalize_skill(signal) in skill_set)
        keyword_hits = sum(1 for keyword in DOMAIN_KEYWORDS.get(domain, []) if keyword in normalized_text)
        scores[domain] = (signal_hits * 2.5) + (keyword_hits * 1.0)

    # Explicit composite rules requested by product behavior.
    if {"python", "fastapi"}.issubset(skill_set) and ("docker" in skill_set or "machine learning" in skill_set):
        scores["backend_ai"] = scores.get("backend_ai", 0.0) + 4.0
    if {"kubernetes", "terraform"}.issubset(skill_set) and ({"aws", "azure", "gcp"} & skill_set):
        scores["devops"] = scores.get("devops", 0.0) + 5.0
    if {"telecommunications", "fiber optics"} & skill_set and ({"networking", "routing", "switching"} & skill_set):
        scores["telecom_network"] = scores.get("telecom_network", 0.0) + 3.0

    return scores


def _infer_domains(skills: list[str], text: str) -> tuple[str, list[str], dict[str, float]]:
    scores = _domain_scores(skills, text)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    if not ordered or ordered[0][1] <= 0:
        return "backend_ai", [], scores

    primary = ordered[0][0]
    secondary = [domain for domain, score in ordered[1:] if score >= max(2.0, ordered[0][1] * 0.45)][:2]
    return primary, secondary, scores


def _generate_dynamic_roles(insight: CandidateInsight) -> list[str]:
    return generate_dynamic_roles(insight.primary_domain, insight.secondary_domains, insight.skills, insight.level)


def _role_tags(role_name: str, primary_domain: str) -> set[str]:
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


def _merge_requirements(tags: set[str], primary_tag: str | None = None) -> dict[str, list[str]]:
    grouped = {"technical": [], "practical": [], "tools": []}

    ordered_tags = []
    if primary_tag and primary_tag in tags:
        ordered_tags.append(primary_tag)
    ordered_tags.extend(tag for tag in sorted(tags) if tag != primary_tag)

    for tag in ordered_tags:
        req = TAG_REQUIREMENTS.get(tag)
        if not req:
            continue
        # Keep role requirements focused: full weight for primary tag, lighter for supporting tags.
        is_primary = tag == primary_tag
        limits = {"technical": 3 if is_primary else 1, "practical": 2 if is_primary else 1, "tools": 2 if is_primary else 1}
        for key in grouped:
            for skill in req[key][: limits[key]]:
                if skill not in grouped[key]:
                    grouped[key].append(skill)

    for key in grouped:
        grouped[key] = grouped[key][:4]

    # Safety baseline if no tag requirements resolved.
    if not any(grouped.values()):
        grouped = {
            "technical": ["system design", "problem solving"],
            "practical": ["implementation experience", "production support"],
            "tools": ["git", "linux"],
        }

    return grouped


def _required_skill_set(grouped: dict[str, list[str]]) -> set[str]:
    merged: set[str] = set()
    for values in grouped.values():
        for value in values:
            merged.add(_normalize_skill(value))
    return merged


def _candidate_skill_set(skills: list[str]) -> set[str]:
    return {_normalize_skill(skill) for skill in skills}


def _role_specific_requirements(role_name: str) -> list[str]:
    lowered = role_name.lower()
    extras: list[str] = []

    if "llm" in lowered:
        extras.extend(["llm", "rag", "transformers"])
    if "nlp" in lowered or "language" in lowered:
        extras.extend(["nlp", "transformers", "sentence-transformers"])
    if "backend" in lowered or "api" in lowered:
        extras.extend(["python", "fastapi", "rest api"])
    if "devops" in lowered or "reliability" in lowered or "sre" in lowered:
        extras.extend(["kubernetes", "terraform", "ci/cd"])
    if "cloud" in lowered:
        extras.extend(["aws", "azure", "gcp"])
    if "network operations" in lowered:
        extras.extend(["network operations", "noc", "network troubleshooting"])
    if "wireless" in lowered:
        extras.extend(["wireless networking", "wimax", "microwave links"])
    if "telecom" in lowered:
        extras.extend(["telecommunications", "fiber optics", "network integration"])

    deduped: list[str] = []
    seen: set[str] = set()
    for item in extras:
        key = _normalize_skill(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:4]


def _skill_variants(skill: str) -> set[str]:
    base = _normalize_skill(skill)
    variants = {base}
    synonym_map = {
        "telecommunications": {"telecom"},
        "telecom": {"telecommunications"},
        "network operations": {"noc"},
        "noc": {"network operations"},
        "microwave": {"microwave links"},
        "microwave links": {"microwave"},
        "wan/lan": {"wan", "lan"},
        "tcp/ip": {"tcpip"},
    }
    variants |= synonym_map.get(base, set())
    return variants


def _is_skill_covered(required_skill: str, candidate_set: set[str], normalized_text: str) -> bool:
    normalized_required = _normalize_skill(required_skill)
    variants = _skill_variants(normalized_required)
    if any(variant in candidate_set for variant in variants):
        return True
    if any((" " in variant and variant in normalized_text) for variant in variants):
        return True
    if "/" in required_skill:
        parts = [_normalize_skill(part) for part in required_skill.split("/")]
        if any(part and part in normalized_text for part in parts):
            return True
    return False


def _match_details(insight: CandidateInsight, role_name: str) -> tuple[float, float, float, dict[str, list[str]], list[str], str]:
    required_grouped = build_role_requirements(role_name, insight.primary_domain)
    required_skills: list[str] = []
    for values in required_grouped.values():
        required_skills.extend(values)

    match_result = compare_role_match(
        candidate_skills=insight.skills,
        required_skills=required_skills,
        normalized_text=insight.normalized_text,
        evidence_by_skill=insight.skill_evidence,
        skill_depths=insight.skill_depths,
        years_of_experience=insight.years_of_experience,
        leadership_score=insight.leadership_score,
        project_depth_score=insight.project_depth_score,
        role_name=role_name,
    )

    missing_grouped: dict[str, list[str]] = {}
    for key, values in required_grouped.items():
        missing_grouped[key] = [value for value in values if value in match_result.missing_skills]

    print(f"[VALIDATION][ROLE] {role_name}")
    print(f"[VALIDATION][ROLE] candidate_skills: {', '.join(insight.skills) if insight.skills else 'none'}")
    print(
        f"[VALIDATION][ROLE] required_skills: {', '.join(required_skills) if required_skills else 'none'}"
    )
    print(
        f"[VALIDATION][ROLE] matched: {', '.join(match_result.matched_skills) if match_result.matched_skills else 'none'} | "
        f"missing: {', '.join(match_result.missing_skills) if match_result.missing_skills else 'none'}"
    )

    return (
        match_result.confidence,
        match_result.composite,
        match_result.priority_score,
        missing_grouped,
        match_result.missing_skills,
        match_result.reason,
    )


def build_candidate_insight(cv_text: str) -> CandidateInsight:
    cleaned = (cv_text or "").strip()
    if not cleaned:
        raise ValueError("Uploaded file is empty or unreadable.")

    extractor = _build_skill_extractor()
    grouped_skills, skill_evidence, skill_depths = extractor.extract_grouped_with_metadata(cleaned)
    skills: list[str] = []
    for group_key in grouped_skills:
        skills.extend(grouped_skills[group_key])

    deduped: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        key = _normalize_skill(skill)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(skill)
    skills = deduped

    years = _extract_years_of_experience(cleaned)
    leadership_score = _score_leadership(cleaned)
    project_depth_score = _score_project_depth(cleaned)
    skill_depth_score = _score_skill_depths(skill_depths)
    project_depth_score = min(1.0, (project_depth_score * 0.7) + (skill_depth_score * 0.3))
    level = _infer_level(years, leadership_score, project_depth_score, cleaned)

    primary_domain, secondary_domains, _ = _infer_domains(skills, cleaned)

    return CandidateInsight(
        inferred_headline=_infer_headline(cleaned),
        level=level,
        years_of_experience=years,
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        skills=skills,
        skill_evidence=skill_evidence,
        skill_depths=skill_depths,
        leadership_score=leadership_score,
        project_depth_score=project_depth_score,
        normalized_text=_normalize(cleaned),
    )


def recommend_job_titles_from_cv_text(cv_text: str, top_k: int = 5) -> RecommendationResult:
    insight = build_candidate_insight(cv_text)
    print(f"[VALIDATION] Extracted skills: {', '.join(insight.skills) if insight.skills else 'none'}")
    print(
        "[VALIDATION] Domain detected: "
        f"{insight.primary_domain}"
        f" | secondary: {', '.join(insight.secondary_domains) if insight.secondary_domains else 'none'}"
    )
    generated_roles = _generate_dynamic_roles(insight)
    selected_roles = generated_roles[: max(1, min(top_k, len(generated_roles)))]

    ranked_rows: list[tuple[str, float, float, float, dict[str, list[str]], list[str], str]] = []
    for role_name in selected_roles:
        confidence, composite, priority_score, missing_grouped, missing_flat, reason = _match_details(insight, role_name)
        ranked_rows.append((role_name, confidence, composite, priority_score, missing_grouped, missing_flat, reason))

    ranked_rows.sort(key=lambda row: (row[3], row[2], row[1]), reverse=True)

    matches: list[CandidateMatchResponse] = []
    for rank, (role_name, confidence, composite, priority_score, missing_grouped, missing_flat, reason) in enumerate(ranked_rows, start=1):
        depth_score = min(1.0, (insight.years_of_experience / 8.0) * 0.45 + (insight.project_depth_score * 0.4) + (insight.leadership_score * 0.15))
        match_level = _match_level(confidence, depth_score, insight.level)

        matches.append(
            CandidateMatchResponse(
                job_title=role_name,
                match_percentage=round(composite * 100.0, 2),
                ranking=rank,
                similarity=round(composite, 4),
                skill_score=round(confidence, 4),
                title_score=round(insight.project_depth_score, 4),
                missing_skills=missing_flat,
                missing_skills_by_group=missing_grouped,
                reason=reason,
                confidence_score=round(confidence, 4),
                match_level=match_level,
                feedback=reason,
                score_breakdown={
                    "confidence": round(confidence, 4),
                    "depth": round(insight.project_depth_score, 4),
                    "leadership": round(insight.leadership_score, 4),
                    "priority": round(priority_score, 4),
                },
                logs=[
                    "Mode: reasoning-based CV analysis",
                    "No posted jobs used",
                    "No cosine similarity or static job catalog used",
                    "Confidence formula: matched_skills / total_required_skills",
                    f"Inferred level: {insight.level}",
                    f"Primary domain: {insight.primary_domain}",
                    f"Secondary domains: {', '.join(insight.secondary_domains) if insight.secondary_domains else 'none'}",
                    f"Inferred headline: {insight.inferred_headline}",
                    f"Detected skills: {', '.join(insight.skills) if insight.skills else 'none'}",
                    f"Skill depth summary: {', '.join(f'{skill}:{depth}' for skill, depth in list(insight.skill_depths.items())[:8]) if insight.skill_depths else 'none'}",
                    f"Match level: {match_level}",
                ],
            )
        )

    return RecommendationResult(total_catalog=len(matches), matches=matches)

from backend.app.services.cv_reasoning_engine import CandidateInsight as CandidateInsight  # noqa: E402,F401
from backend.app.services.cv_reasoning_engine import RecommendationResult as RecommendationResult  # noqa: E402,F401
from backend.app.services.cv_reasoning_engine import build_candidate_insight as build_candidate_insight  # noqa: E402,F401
from backend.app.services.cv_reasoning_engine import recommend_job_titles_from_cv_text as recommend_job_titles_from_cv_text  # noqa: E402,F401
