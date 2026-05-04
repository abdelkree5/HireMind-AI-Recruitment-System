from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Literal

import json
import sqlite3
import numpy as np

# Configuration
BASE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FINETUNED_MODEL_DIR = Path(__file__).resolve().parents[1] / "ai_engine" / "training" / "artifacts"
EMBEDDING_DIMENSIONS = 256
CACHE_DB_PATH = Path("database/embeddings_cache.db")

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
    model_source: Literal["artifacts", "base", "fallback"] = "fallback"

def _resolve_artifact_model_path() -> Path | None:
    if not FINETUNED_MODEL_DIR.exists():
        return None
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

def _init_cache():
    try:
        CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS embeddings (hash TEXT PRIMARY KEY, vector TEXT)")
    except Exception:
        pass

_init_cache()

def _get_from_cache(text_hash: str) -> tuple[float, ...] | None:
    try:
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            cursor = conn.execute("SELECT vector FROM embeddings WHERE hash = ?", (text_hash,))
            row = cursor.fetchone()
            if row:
                return tuple(json.loads(row[0]))
    except Exception:
        pass
    return None

def _save_to_cache(text_hash: str, vector: tuple[float, ...]):
    try:
        with sqlite3.connect(CACHE_DB_PATH) as conn:
            conn.execute("INSERT OR REPLACE INTO embeddings (hash, vector) VALUES (?, ?)", (text_hash, json.dumps(vector)))
    except Exception:
        pass

@lru_cache(maxsize=4096)
def _cached_embedding(text: str) -> tuple[float, ...]:
    text_hash = sha256(text.encode("utf-8")).hexdigest()
    cached = _get_from_cache(text_hash)
    if cached is not None:
        return cached

    model = get_embedding_model()
    vector = np.asarray(model.encode([text], normalize_embeddings=True))[0]
    vec_tuple = tuple(float(x) for x in vector)
    
    _save_to_cache(text_hash, vec_tuple)
    return vec_tuple

class EmbeddingEngine:
    """Unified engine for text embeddings with caching."""
    def encode(self, text: str) -> np.ndarray:
        return np.asarray(_cached_embedding(text), dtype=np.float32)

    def get_runtime_info(self) -> dict[str, str]:
        artifact_path = _resolve_artifact_model_path()
        return {
            "model_source": _EmbeddingRuntimeState.model_source,
            "artifact_path": str(artifact_path) if artifact_path else "",
            "base_model": BASE_MODEL_NAME,
        }

# Global utility functions for backward compatibility
_engine = EmbeddingEngine()

def embed_text(text: str) -> np.ndarray:
    return _engine.encode(text)

def get_embedding_runtime_info() -> dict[str, str]:
    return _engine.get_runtime_info()
