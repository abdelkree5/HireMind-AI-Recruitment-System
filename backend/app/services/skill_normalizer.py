from __future__ import annotations

from dataclasses import dataclass
import re


NORMALIZATION_PATTERNS: dict[str, tuple[str, ...]] = {
    "aws": (r"\baws\b", r"amazon\s+web\s+services?\b"),
    "azure": (r"\bazure\b", r"microsoft\s+azure\b"),
    "gcp": (r"\bgcp\b", r"google\s+cloud\s+platform\b", r"google\s+cloud\b"),
    "ci/cd": (
        r"\bci\s*/\s*cd\b",
        r"\bci\s*cd\b",
        r"\bcontinuous\s+integration\b",
        r"\bcontinuous\s+deployment\b",
        r"\bgithub\s+actions\b",
        r"\bbuild\s+pipelines?\b",
        r"\bpipelines?\b",
        r"\bjenkins\b",
    ),
    "monitoring": (
        r"\bmonitoring\b",
        r"\bobservability\b",
        r"\bgrafana\b",
        r"\bprometheus\b",
        r"\belk\b",
        r"\belasticsearch\b",
        r"\blogstash\b",
        r"\bkibana\b",
        r"\bsplunk\b",
        r"\bnagios\b",
        r"\bzabbix\b",
    ),
    "cloud architecture": (
        r"\bcloud\s+architecture\b",
        r"\bmulti[-\s]?account\s+architecture\b",
        r"\bmulti[-\s]?account\s+infrastructure\b",
    ),
    "infrastructure automation": (
        r"\binfrastructure\s+automation\b",
        r"\bautomation\s+of\s+infrastructure\b",
    ),
    "kubernetes": (r"\bkubernetes\b", r"\bk8s\b"),
    "terraform": (r"\bterraform\b",),
    "docker": (r"\bdocker\b",),
    "python": (r"\bpython(?:\s+programming)?\b",),
    "fastapi": (r"\bfastapi\b",),
    "rest api": (r"\brest\s+api\b", r"\brestful\s+api\b"),
    "machine learning": (r"\bmachine\s+learning\b", r"\bml\b"),
    "deep learning": (r"\bdeep\s+learning\b",),
    "nlp": (r"\bnlp\b", r"\bnatural\s+language\s+processing\b"),
    "llm": (r"\bllm(?:s)?\b", r"\blarge\s+language\s+models?\b"),
    "rag": (r"\brag\b", r"\bretrieval[-\s]augmented\s+generation\b"),
    "scikit-learn": (r"\bscikit[-\s]?learn\b", r"\bsklearn\b"),
    "transformers": (r"\btransformers?\b",),
    "sentence-transformers": (r"\bsentence[-\s]?transformers?\b",),
    "feature engineering": (r"\bfeature\s+engineering\b",),
    "model evaluation": (r"\bmodel\s+evaluation\b", r"\bevaluation\s+metrics\b"),
    "observability": (r"\bobservability\b",),
    "incident response": (r"\bincident\s+response\b",),
}


ADVANCED_TERMS = (
    "designed",
    "architected",
    "architect",
    "led",
    "owned",
    "spearheaded",
    "scaled",
    "enterprise",
    "production",
    "multi-account",
    "multi account",
    "governance",
    "at scale",
)

INTERMEDIATE_TERMS = (
    "implemented",
    "built",
    "managed",
    "deployed",
    "integrated",
    "operated",
    "maintained",
    "configured",
    "monitored",
)

BASIC_TERMS = (
    "used",
    "familiar",
    "exposure",
    "knowledge of",
    "worked with",
)


@dataclass(frozen=True)
class NormalizedSkillHit:
    canonical_skill: str
    evidence: str
    level: str


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def normalize_skill(skill: str) -> str:
    normalized = normalize_text(skill)
    for canonical, patterns in NORMALIZATION_PATTERNS.items():
        if normalized == canonical:
            return canonical
        for pattern in patterns:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                return canonical
    return normalized.replace("-", " ")


def normalize_skills(skills: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        canonical = normalize_skill(skill)
        if canonical and canonical not in seen:
            seen.add(canonical)
            ordered.append(canonical)
    return ordered


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[\.!?\n])\s+", text or "")
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _skill_regex(skill: str) -> re.Pattern[str]:
    canonical = normalize_skill(skill)
    patterns = list(NORMALIZATION_PATTERNS.get(canonical, ()))
    if not patterns:
        patterns = [re.escape(canonical)]
    return re.compile(r"(?:" + "|".join(patterns) + r")", flags=re.IGNORECASE)


def find_skill_sentence(text: str, skill: str) -> str:
    skill_pattern = _skill_regex(skill)
    for sentence in _split_sentences(text):
        if skill_pattern.search(sentence):
            return sentence.strip()
    return ""


def detect_skill_level(text: str, skill: str) -> str:
    """Detect skill level with context-aware analysis.
    
    Instead of just looking at sentence where skill is mentioned,
    examine the surrounding context for proficiency indicators.
    """
    canonical = normalize_skill(skill)
    skill_pattern = _skill_regex(skill)
    normalized_text = normalize_text(text)
    
    # Find exact sentence with skill
    sentence = find_skill_sentence(text, skill)
    
    # Build search space: sentence + surrounding context
    if sentence:
        sentences = _split_sentences(text)
        skill_idx = None
        for i, sent in enumerate(sentences):
            if skill_pattern.search(sent):
                skill_idx = i
                break
        
        # Include 1 sentence before and after for context
        context_sentences = []
        if skill_idx is not None:
            start = max(0, skill_idx - 1)
            end = min(len(sentences), skill_idx + 2)
            context_sentences = sentences[start:end]
        
        search_space = normalize_text(" ".join(context_sentences)) if context_sentences else normalized_text
    else:
        search_space = normalized_text
    
    # Check for proficiency levels
    if any(term in search_space for term in ADVANCED_TERMS):
        return "Advanced"
    if any(term in search_space for term in INTERMEDIATE_TERMS):
        return "Intermediate"
    if any(term in search_space for term in BASIC_TERMS):
        return "Basic"
    
    # Fallback skill-specific detection
    if canonical in {"aws", "cloud architecture", "infrastructure automation", "monitoring", "ci/cd", "kubernetes", "terraform"}:
        # If mentioned with enterprise/production context, likely advanced
        if any(term in search_space for term in ["architecture", "production", "enterprise", "multi-account", "scale", "infrastructure", "designed", "architected"]):
            return "Advanced"
        # If mentioned with implementation context, intermediate
        if any(term in search_space for term in ["implemented", "deployed", "managed", "configured", "integrated"]):
            return "Intermediate"
    
    return "Basic"
