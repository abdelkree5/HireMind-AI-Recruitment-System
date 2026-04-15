from __future__ import annotations

from pathlib import Path

BASE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FINETUNED_MODEL_DIR = Path(__file__).resolve().parent / "training" / "artifacts"

SEMANTIC_WEIGHT = 0.55
SKILL_WEIGHT = 0.25
TITLE_WEIGHT = 0.10
CONTEXT_WEIGHT = 0.10
