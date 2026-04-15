from __future__ import annotations

import numpy as np


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left, right) / denominator)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def map_similarity_to_score(similarity: float) -> float:
    return clamp(similarity, 0.0, 1.0) * 100.0


def apply_smart_adjustments(
    score: float,
    required_overlap: float,
    experience_match: bool,
    domain_match: bool,
) -> tuple[float, list[str]]:
    adjusted = score
    penalties_or_bonuses: list[str] = []

    if required_overlap > 0.70:
        adjusted += 5.0
        penalties_or_bonuses.append("+5% required skills overlap > 70%")

    if not experience_match:
        adjusted -= 10.0
        penalties_or_bonuses.append("-10% experience level mismatch")

    if not domain_match:
        adjusted -= 10.0
        penalties_or_bonuses.append("-10% domain mismatch")

    adjusted = clamp(adjusted, 0.0, 100.0)
    return adjusted, penalties_or_bonuses


def to_match_level(score: float) -> str:
    if score > 80.0:
        return "Strong"
    if score >= 60.0:
        return "Medium"
    return "Weak"
