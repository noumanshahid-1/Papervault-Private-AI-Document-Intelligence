"""Local embedding providers for retrieval."""

import hashlib
import math
import re
from typing import Protocol


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_HASHING_DIMENSIONS = 384


class EmbeddingProvider(Protocol):
    """Protocol for local embedding providers."""

    provider_name: str
    model_name: str | None

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""


class HashingEmbeddingProvider:
    """Deterministic local bag-of-words embedder used as no-download fallback."""

    def __init__(self, dimensions: int = DEFAULT_HASHING_DIMENSIONS) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero.")
        self.dimensions = dimensions
        self.provider_name = "hashing"
        self.model_name = f"hashing-{dimensions}"

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode text with normalized hashing vectors."""
        return [self._encode_one(text) for text in texts]

    def _encode_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self.dimensions
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingProvider:
    """Local sentence-transformers provider for installed/cached open-source models."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install it or use the hashing provider."
            ) from exc

        self.provider_name = "sentence_transformers"
        self.model_name = model_name
        self._model = SentenceTransformer(model_name, local_files_only=True)

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode text using a local sentence-transformers model."""
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


def get_embedding_provider(
    *,
    prefer_sentence_transformers: bool | None = None,
    provider_name: str | None = None,
    model_name: str | None = None,
) -> EmbeddingProvider:
    """Return a local embedding provider with deterministic fallback."""
    from app.config import get_settings

    settings = get_settings()
    configured_provider = (
        provider_name
        or (
            "sentence_transformers"
            if prefer_sentence_transformers
            else settings.local_embedding_provider
        )
    ).strip().lower()
    configured_model = model_name or settings.local_embedding_model or DEFAULT_EMBEDDING_MODEL
    if configured_provider in {"sentence_transformers", "sentence-transformers"}:
        try:
            return SentenceTransformerEmbeddingProvider(model_name=configured_model)
        except (RuntimeError, OSError, TypeError, ValueError):
            return HashingEmbeddingProvider()
    return HashingEmbeddingProvider()


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in re.finditer(r"[a-zA-Z0-9]+", text.lower()):
        token = match.group(0)
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return tokens
