"""Dense embedding generation with support for SentenceTransformers and fast vector fallback."""

import logging
from typing import List
import numpy as np
from app.config import settings

logger = logging.getLogger("ai_assistant.embeddings")


class EmbeddingEngine:
    """Embedding generator using sentence-transformers or deterministic vectorization."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._initialized = False

    def _lazy_init(self):
        if not self._initialized:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to fast hashed vectorizer.")
                self._model = None
                self._initialized = True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute dense embedding vectors for a list of texts."""
        self._lazy_init()
        if not texts:
            return []

        if self._model is not None:
            embeddings = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return embeddings.tolist()
        else:
            # Fallback deterministic pseudo-embedding (384-dimensional) for test environments
            return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Compute dense embedding vector for a search query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * 384

    def _fallback_embed(self, text: str, dim: int = 384) -> List[float]:
        """Generate deterministic normalized hash-based embedding vector."""
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for idx, word in enumerate(words):
            h = hash(word)
            pos = abs(h) % dim
            vec[pos] += 1.0 / (idx + 1.0)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Global embedding engine instance
embedding_engine = EmbeddingEngine()
