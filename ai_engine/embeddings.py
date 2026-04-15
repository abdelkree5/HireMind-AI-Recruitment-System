from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import numpy as np

from ai_engine.config import BASE_MODEL_NAME, FINETUNED_MODEL_DIR

EMBEDDING_DIMENSIONS = 256


class FallbackSentenceTransformer:
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


class EmbeddingEngine:
    def __init__(self) -> None:
        self.model = self._load_model()

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model():
        model_path = str(FINETUNED_MODEL_DIR) if Path(FINETUNED_MODEL_DIR).exists() else BASE_MODEL_NAME
        try:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(model_path)
        except Exception:
            return FallbackSentenceTransformer()

    def encode(self, text: str) -> np.ndarray:
        return np.asarray(self.model.encode([text], normalize_embeddings=True))[0]
