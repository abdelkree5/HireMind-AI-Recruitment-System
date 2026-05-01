import numpy as np
from ai_engine.embeddings import EmbeddingEngine

def test_embedding_engine():
    engine = EmbeddingEngine()
    vec = engine.encode("This is a test document")
    assert isinstance(vec, np.ndarray)
    assert len(vec.shape) == 1
    assert vec.shape[0] > 0
