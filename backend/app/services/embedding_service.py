from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Literal

import numpy as np

BASE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FINETUNED_MODEL_DIR = Path(__file__).resolve().parents[3] / "ai_engine" / "training" / "artifacts"
EMBEDDING_DIMENSIONS = 256


class FallbackEmbeddingModel:
    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> np.ndarray:
        vectors = np.asarray([self._hash_text(text) for text in texts], dtype=np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vectors = vectors / norms
        return vectors

    def _hash_text(self, text: str) -> np.ndarray:
        vector = np.zeros(EMBEDDING_DIMENSIONS, dtype=np.float32)
        for token in text.lower().split():
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % EMBEDDING_DIMENSIONS
            vector[index] += 1.0
        return vector


class _EmbeddingRuntimeState:
    # بنحتفظ بمصدر الموديل علشان يظهر في الـ logs والـ health checks.
    model_source: Literal["artifacts", "base", "fallback"] = "fallback"


def _resolve_artifact_model_path() -> Path | None:
    if not FINETUNED_MODEL_DIR.exists():
        return None

    # sentence-transformers بيقدر يحمل من جذر المجلد أو من فولدر checkpoint.
    if (FINETUNED_MODEL_DIR / "config.json").exists():
        return FINETUNED_MODEL_DIR

    for candidate in sorted(FINETUNED_MODEL_DIR.glob("checkpoint-*"), reverse=True):
        if (candidate / "config.json").exists():
            return candidate

    return FINETUNED_MODEL_DIR


@lru_cache(maxsize=1)
def get_embedding_model():
    artifact_model_path = _resolve_artifact_model_path()
    try:
        from sentence_transformers import SentenceTransformer

        if artifact_model_path is not None:
            _EmbeddingRuntimeState.model_source = "artifacts"
            return SentenceTransformer(str(artifact_model_path))

        _EmbeddingRuntimeState.model_source = "base"
        return SentenceTransformer(BASE_MODEL_NAME)
    except Exception:
        _EmbeddingRuntimeState.model_source = "fallback"
        return FallbackEmbeddingModel()


@lru_cache(maxsize=4096)
def _cached_embedding(text: str) -> tuple[float, ...]:
    model = get_embedding_model()
    vector = np.asarray(model.encode([text], normalize_embeddings=True))[0]
    return tuple(float(x) for x in vector)


def embed_text(text: str) -> np.ndarray:
    return np.asarray(_cached_embedding(text), dtype=np.float32)


def get_embedding_runtime_info() -> dict[str, str]:
    artifact_path = _resolve_artifact_model_path()
    return {
        "model_source": _EmbeddingRuntimeState.model_source,
        "artifact_path": str(artifact_path) if artifact_path else "",
        "base_model": BASE_MODEL_NAME,
    }
