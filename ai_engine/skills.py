from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

DEFAULT_SKILL_VOCAB = [
    "python",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "pandas",
    "numpy",
    "scikit-learn",
    "pytorch",
    "tensorflow",
    "transformers",
    "sentence-transformers",
    "nlp",
    "machine learning",
    "deep learning",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "react",
    "javascript",
    "typescript",
    "html",
    "css",
    "rest api",
    "microservices",
    "git",
    "linux",
    "networking",
    "network security",
    "wan",
    "lan",
    "tcp/ip",
    "routing",
    "switching",
    "firewall",
    "vpn",
    "dns",
    "dhcp",
    "fiber optics",
    "wimax",
    "microwave",
    "telecommunications",
    "telecom",
    "radio access network",
    "noc",
    "network operations",
    "cisco",
    "ccna",
    "ccnp",
    "juniper",
    "vmware",
    "windows server",
    "active directory",
    "bash",
    "powershell",
    "ansible",
    "jenkins",
    "prometheus",
    "grafana",
    "splunk",
    "elk",
    "monitoring",
    "observability",
    "infrastructure automation",
    "cloud architecture",
    "multi-account architecture",
    "incident response",
    "mlops",
]


GROUP_KEYS = (
    "languages",
    "frameworks",
    "ai_ml",
    "devops_tools",
    "databases",
    "concepts",
)


CATEGORY_ALIAS_PATTERNS: dict[str, dict[str, tuple[str, ...]]] = {
    "languages": {
        "Python": (r"\bpython(?:\s+programming)?\b",),
        "JavaScript": (r"\bjavascript\b", r"\bjs\b"),
        "TypeScript": (r"\btypescript\b", r"\bts\b"),
        "HTML": (r"\bhtml5?\b",),
        "CSS": (r"\bcss3?\b",),
        "Dart": (r"\bdart\b",),
        "SQL": (r"\bsql\b",),
        "Java": (r"\bjava\b",),
        "C++": (r"\bc\+\+\b",),
        "C#": (r"\bc#\b", r"\bc\s*sharp\b"),
        "Go": (r"\bgo(?:lang)?\b",),
        "Bash": (r"\bbash\b",),
        "PowerShell": (r"\bpowershell\b",),
    },
    "frameworks": {
        "FastAPI": (r"\bfastapi\b",),
        "Django": (r"\bdjango\b",),
        "Flask": (r"\bflask\b",),
        "React": (r"\breact(?:\.js)?\b",),
        "Vue.js": (r"\bvue(?:\.js)?\b",),
        "Angular": (r"\bangular\b",),
        "Next.js": (r"\bnext\.?js\b",),
        "TailwindCSS": (r"\btailwind(?:\s*css)?\b",),
        "Redux": (r"\bredux\b",),
        "Vite": (r"\bvite\b",),
        "Flutter": (r"\bflutter\b",),
        "Spring Boot": (r"\bspring\s+boot\b",),
        "Node.js": (r"\bnode\.?js\b",),
        "Express": (r"\bexpress(?:\.js)?\b",),
        "TensorFlow": (r"\btensorflow(?:\s+framework)?\b",),
        "PyTorch": (r"\bpytorch\b",),
        "scikit-learn": (r"\bscikit[-\s]?learn\b", r"\bsklearn\b"),
        "Transformers": (r"\btransformers?\b",),
        "sentence-transformers": (r"\bsentence[-\s]?transformers?\b",),
        "LangChain": (r"\blangchain\b",),
    },
    "ai_ml": {
        "Machine Learning": (r"\bmachine\s+learning\b", r"\bml\b"),
        "Deep Learning": (r"\bdeep\s+learning\b",),
        "NLP": (r"\bnlp\b", r"\bnatural\s+language\s+processing\b"),
        "LLM": (r"\bllm(?:s)?\b", r"\blarge\s+language\s+models?\b"),
        "RAG": (r"\brag\b", r"\bretrieval[-\s]augmented\s+generation\b"),
        "Model Evaluation": (r"\bmodel\s+evaluation\b", r"\bevaluation\s+metrics\b"),
        "Feature Engineering": (r"\bfeature\s+engineering\b",),
        "Information Retrieval": (r"\binformation\s+retrieval\b",),
        "Prompt Engineering": (r"\bprompt\s+engineering\b",),
    },
    "devops_tools": {
        "Docker": (r"\bdocker\b",),
        "Kubernetes": (r"\bkubernetes\b", r"\bk8s\b"),
        "Terraform": (r"\bterraform\b",),
        "AWS": (r"\baws\b", r"amazon\s+web\s+services\b"),
        "Azure": (r"\bazure\b", r"microsoft\s+azure\b"),
        "GCP": (r"\bgcp\b", r"google\s+cloud\s+platform\b"),
        "CI/CD": (r"\bci\s*/\s*cd\b", r"\bci\b", r"\bcd\b"),
        "Jenkins": (r"\bjenkins\b",),
        "Git": (r"\bgit\b",),
        "Linux": (r"\blinux\b",),
        "Prometheus": (r"\bprometheus\b",),
        "Grafana": (r"\bgrafana\b",),
        "Monitoring": (r"\bmonitoring\b", r"\bmonitored\b", r"\bmonitor\b"),
        "Splunk": (r"\bsplunk\b",),
        "ELK Stack": (r"\belk\b", r"\belasticsearch\b", r"\blogstash\b", r"\bkibana\b"),
        "NOC": (r"\bnoc\b", r"\bnetwork\s+operations\b"),
        "VMware": (r"\bvmware\b",),
        "Ansible": (r"\bansible\b",),
        "Cisco": (r"\bcisco\b",),
        "CCNA": (r"\bccna\b",),
        "CCNP": (r"\bccnp\b",),
        "Wireshark": (r"\bwireshark\b",),
        "Nagios": (r"\bnagios\b",),
        "Zabbix": (r"\bzabbix\b",),
    },
    "databases": {
        "PostgreSQL": (r"\bpostgres(?:ql)?\b",),
        "MySQL": (r"\bmysql\b",),
        "MongoDB": (r"\bmongodb\b",),
        "Redis": (r"\bredis\b",),
        "SQLite": (r"\bsqlite\b",),
        "SQL Server": (r"\bsql\s+server\b",),
    },
    "concepts": {
        "Microservices": (r"\bmicroservices?\b",),
        "Distributed Systems": (r"\bdistributed\s+systems?\b",),
        "REST API": (r"\brest\s*(?:ful)?\s+apis?\b",),
        "System Design": (r"\bsystem\s+design\b",),
        "Infrastructure Automation": (r"\binfrastructure\s+automation\b", r"\bautomation\s+of\s+infrastructure\b"),
        "Observability": (r"\bobservability\b",),
        "Cloud Architecture": (r"\bcloud\s+architecture\b", r"\bmulti[-\s]?account\s+architecture\b", r"\bmulti[-\s]?account\s+infrastructure\b"),
        "Network Security": (r"\bnetwork\s+security\b",),
        "Incident Response": (r"\bincident\s+response\b",),
        "MLOps": (r"\bmlops\b",),
        "WAN/LAN": (r"\bwan\b", r"\blan\b"),
        "TCP/IP": (r"\btcp\s*/\s*ip\b", r"\btcpip\b"),
        "Fiber Optics": (r"\bfiber\s+optics?\b",),
        "Routing & Switching": (r"\brouting\b", r"\bswitching\b"),
        "WiMAX": (r"\bwimax\b",),
        "Microwave Links": (r"\bmicrowave(?:s)?\b",),
        "Wireless Networking": (r"\bwi[-\s]?fi\b", r"\bwireless\b"),
        "Network Integration": (r"\bnetwork\s+integration\b",),
        "Site Survey": (r"\bsite\s+survey\b", r"\bsurvey\b"),
    },
}


NOISE_TERMS = {
    "experience",
    "project",
    "projects",
    "responsible",
    "responsibilities",
    "worked",
    "work",
    "team",
    "support",
    "management",
    "services",
    "service",
    "technology",
    "technologies",
    "tools",
    "framework",
    "frameworks",
}


ADVANCED_CONTEXT_TERMS = (
    "designed",
    "architected",
    "architect",
    "led",
    "owned",
    "built",
    "deployed",
    "scaled",
    "enterprise",
    "production",
    "production-grade",
    "multi-account",
    "multi account",
    "end-to-end",
    "end to end",
    "at scale",
)

INTERMEDIATE_CONTEXT_TERMS = (
    "implemented",
    "configured",
    "maintained",
    "operated",
    "managed",
    "monitored",
    "supported",
    "integrated",
)

BASIC_CONTEXT_TERMS = (
    "familiar",
    "exposure",
    "knowledge of",
    "awareness of",
)


CONTEXT_PATTERNS = (
    re.compile(
        r"(?:experience\s+with|worked\s+with|using|use\s+of|knowledge\s+of|skilled\s+in|hands-on\s+with|proficient\s+in|built\s+with)\s+([a-z0-9\+#\./\-\s,]{3,120})",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?:technologies|tools|stack|skills)\s*[:\-]\s*([a-z0-9\+#\./\-\s,]{3,180})",
        flags=re.IGNORECASE,
    ),
)


@dataclass
class SkillEvidence:
    skill: str
    category: str
    evidence: str
    depth: str = "Basic"


class SkillExtractor:
    def __init__(self, vocabulary: list[str] | None = None) -> None:
        self.vocabulary = vocabulary or DEFAULT_SKILL_VOCAB
        self._canonical_to_category: dict[str, str] = {
            canonical: category
            for category, entries in CATEGORY_ALIAS_PATTERNS.items()
            for canonical in entries.keys()
        }

    def extract(self, text: str) -> list[str]:
        grouped = self.extract_grouped(text)
        flattened: list[str] = []
        for category in GROUP_KEYS:
            flattened.extend(grouped[category])
        return self._deduplicate(flattened)

    def extract_grouped(self, text: str) -> dict[str, list[str]]:
        grouped, _ = self.extract_grouped_with_evidence(text)
        return grouped

    def extract_grouped_with_evidence(self, text: str) -> tuple[dict[str, list[str]], dict[str, str]]:
        grouped, evidence, _ = self.extract_grouped_with_metadata(text)
        return grouped, evidence

    def extract_grouped_with_metadata(self, text: str) -> tuple[dict[str, list[str]], dict[str, str], dict[str, str]]:
        lowered_text = text.lower()
        grouped: dict[str, list[str]] = {key: [] for key in GROUP_KEYS}
        evidence: dict[str, str] = {}
        depth_by_skill: dict[str, str] = {}

        # Pass 1: robust alias matching with normalization.
        for category, entries in CATEGORY_ALIAS_PATTERNS.items():
            for canonical, patterns in entries.items():
                for pattern in patterns:
                    match = re.search(pattern, lowered_text, flags=re.IGNORECASE)
                    if not match:
                        continue
                    if canonical not in grouped[category]:
                        grouped[category].append(canonical)
                    snippet = self._capture_evidence_sentence(text, match.start(), match.end())
                    evidence.setdefault(canonical, snippet)
                    depth_by_skill.setdefault(canonical, self._classify_skill_depth(snippet, canonical, lowered_text))
                    break

        # Pass 2: context-driven candidate mining for non-exact phrasing.
        for candidate, snippet in self._collect_context_candidates(text):
            canonical = self._normalize_candidate(candidate)
            if not canonical:
                continue
            if not self._canonical_present_in_text(canonical, lowered_text):
                continue
            category = self._infer_category(canonical)
            if not category:
                continue
            if canonical not in grouped[category]:
                grouped[category].append(canonical)
            evidence.setdefault(canonical, snippet)
            depth_by_skill.setdefault(canonical, self._classify_skill_depth(snippet, canonical, lowered_text))

        # Keep output stable and clean.
        for key in GROUP_KEYS:
            grouped[key] = self._deduplicate(grouped[key])

        return grouped, evidence, depth_by_skill

    def overlap_score(self, resume_skills: list[str], required_skills: list[str]) -> float:
        if not required_skills:
            return 0.0
        resume_counter = Counter(skill.lower() for skill in resume_skills)
        hit_count = sum(1 for skill in required_skills if resume_counter[skill.lower()] > 0)
        return hit_count / len(required_skills)

    def missing_skills(self, resume_skills: list[str], required_skills: list[str]) -> list[str]:
        resume_set = {skill.lower() for skill in resume_skills}
        return [skill for skill in required_skills if skill.lower() not in resume_set]

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    def _collect_context_candidates(self, text: str) -> list[tuple[str, str]]:
        normalized_text = self._normalize(text)
        found: list[tuple[str, str]] = []

        for pattern in CONTEXT_PATTERNS:
            for match in pattern.finditer(normalized_text):
                chunk = match.group(1)
                raw_candidates = re.split(r",|/|\band\b|\bwith\b|\busing\b", chunk)
                for item in raw_candidates:
                    cleaned = item.strip(" .;:-")
                    if not cleaned:
                        continue
                    if cleaned in NOISE_TERMS:
                        continue
                    if len(cleaned) < 2 or len(cleaned) > 40:
                        continue
                    snippet = self._capture_evidence_sentence(text, match.start(1), match.end(1))
                    found.append((cleaned, snippet))

        return found

    def _normalize_candidate(self, candidate: str) -> str | None:
        value = self._normalize(candidate)
        value = re.sub(r"\b(programming|framework|tool|database|databases|library|libraries)\b", "", value).strip()
        if not value or value in NOISE_TERMS:
            return None

        # Exact or alias-based canonicalization.
        for category, entries in CATEGORY_ALIAS_PATTERNS.items():
            for canonical, patterns in entries.items():
                if value == canonical.lower():
                    return canonical
                for pattern in patterns:
                    if re.search(pattern, value, flags=re.IGNORECASE):
                        return canonical

        # Token-level approximations for common noisy forms.
        approximate_map = {
            "python programming": "Python",
            "tensorflow framework": "TensorFlow",
            "pytorch framework": "PyTorch",
            "postgres": "PostgreSQL",
            "nodejs": "Node.js",
            "restful api": "REST API",
            "distributed system": "Distributed Systems",
        }
        if value in approximate_map:
            return approximate_map[value]

        telecom_map = {
            "wimax": "WiMAX",
            "microwaves": "Microwave Links",
            "microwave": "Microwave Links",
            "wifi": "Wireless Networking",
            "wi-fi": "Wireless Networking",
            "cisco": "Cisco",
            "ccna": "CCNA",
            "ccnp": "CCNP",
            "fiber": "Fiber Optics",
            "fiber optics": "Fiber Optics",
            "vpn": "Network Security",
            "wan": "WAN/LAN",
            "lan": "WAN/LAN",
            "tcpip": "TCP/IP",
        }
        if value in telecom_map:
            return telecom_map[value]

        return None

    def _canonical_present_in_text(self, canonical: str, lowered_text: str) -> bool:
        category = self._infer_category(canonical)
        if category and canonical in CATEGORY_ALIAS_PATTERNS.get(category, {}):
            for pattern in CATEGORY_ALIAS_PATTERNS[category][canonical]:
                if re.search(pattern, lowered_text, flags=re.IGNORECASE):
                    return True

        normalized_canonical = self._normalize(canonical)
        return bool(normalized_canonical) and normalized_canonical in lowered_text

    def _infer_category(self, canonical_skill: str) -> str | None:
        if canonical_skill in self._canonical_to_category:
            return self._canonical_to_category[canonical_skill]
        return None

    def _capture_evidence_sentence(self, original_text: str, start: int, end: int) -> str:
        if not original_text:
            return ""

        left_bound = 0
        right_bound = len(original_text)
        separators = ".\n;:!?"

        for i in range(max(0, start - 240), start):
            if original_text[i] in separators:
                left_bound = i + 1

        for i in range(end, min(len(original_text), end + 240)):
            if original_text[i] in separators:
                right_bound = i + 1
                break

        snippet = original_text[left_bound:right_bound]
        snippet = re.sub(r"\s+", " ", snippet).strip(" -\t\n\r")
        return snippet[:220]

    def _classify_skill_depth(self, snippet: str, canonical: str, lowered_text: str) -> str:
        context = f"{snippet} {canonical} {lowered_text}".lower()
        if any(term in context for term in ADVANCED_CONTEXT_TERMS):
            return "Advanced"
        if any(term in context for term in INTERMEDIATE_CONTEXT_TERMS):
            return "Intermediate"
        if any(term in context for term in BASIC_CONTEXT_TERMS):
            return "Basic"
        return "Basic"

    def _deduplicate(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
