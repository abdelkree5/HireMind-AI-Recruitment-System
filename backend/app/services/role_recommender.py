from __future__ import annotations

# Backward-compatible alias module used by some flows.
from backend.app.services.cv_reasoning_engine import (  # noqa: F401
    CandidateInsight,
    RecommendationResult,
    build_candidate_insight,
    recommend_job_titles_from_cv_text,
)
