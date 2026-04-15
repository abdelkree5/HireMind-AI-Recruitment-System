from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

from backend.app.services.embedding_service import embed_text


def _normalize(text: str) -> str:
    return " ".join((text or "").split()).strip()


@lru_cache(maxsize=1)
def _get_sentence_transformer_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def _embed_with_sentence_transformers(text: str) -> np.ndarray:
    model = _get_sentence_transformer_model()
    vector = np.asarray(model.encode([text], normalize_embeddings=True))[0]
    return vector.astype(np.float32)


def _embed_with_openai(text: str) -> np.ndarray:
    from openai import OpenAI

    model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=model_name, input=[text])
    vector = np.asarray(response.data[0].embedding, dtype=np.float32)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector


def embed_text_semantic(text: str, provider: str = "auto") -> np.ndarray:
    normalized = _normalize(text)
    if not normalized:
        return np.zeros(384, dtype=np.float32)

    provider_choice = provider.lower().strip()
    if provider_choice == "openai":
        try:
            return _embed_with_openai(normalized)
        except Exception:
            return embed_text(normalized)

    if provider_choice == "sentence-transformers":
        try:
            return _embed_with_sentence_transformers(normalized)
        except Exception:
            return embed_text(normalized)

    # auto: prefer sentence-transformers, then OpenAI, then local fallback.
    try:
        return _embed_with_sentence_transformers(normalized)
    except Exception:
        try:
            if os.getenv("OPENAI_API_KEY"):
                return _embed_with_openai(normalized)
        except Exception:
            pass
    return embed_text(normalized)
