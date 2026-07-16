"""Local in-memory vector retrieval with optional FAISS acceleration."""

from app.models.schemas import DocumentChunk, RetrievalResult
from app.services.embeddings import EmbeddingProvider, HashingEmbeddingProvider
from app.services.retrieval_scoring import hybrid_retrieval_score


DEFAULT_TOP_K = 5


class LocalVectorStore:
    """Small local vector store for per-document retrieval."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self._chunks: list[DocumentChunk] = []
        self._vectors: list[list[float]] = []
        self._faiss_index: object | None = None
        self.backend_name = "python"

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Embed and add chunks to the in-memory index."""
        if not chunks:
            return
        vectors = self.embedding_provider.encode([chunk.text for chunk in chunks])
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)
        self._rebuild_faiss_index()

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievalResult]:
        """Return top-k chunks ranked by hybrid local relevance."""
        if not self._chunks or not query.strip():
            return []

        query_vector = self.embedding_provider.encode([query])[0]
        if self._faiss_index is not None:
            return self._search_faiss(query, query_vector, top_k)

        return self._search_python(query, query_vector, top_k)

    def _search_python(
        self, query: str, query_vector: list[float], top_k: int
    ) -> list[RetrievalResult]:
        scored = [
            RetrievalResult(
                chunk=chunk,
                score=hybrid_retrieval_score(
                    query,
                    chunk.text,
                    _dot(query_vector, vector),
                ),
            )
            for chunk, vector in zip(self._chunks, self._vectors, strict=True)
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]

    def _search_faiss(
        self, query_text: str, query_vector: list[float], top_k: int
    ) -> list[RetrievalResult]:
        try:
            import numpy as np
        except ImportError:
            return self._search_python(query_text, query_vector, top_k)

        query = np.array([query_vector], dtype="float32")
        scores, indexes = self._faiss_index.search(query, len(self._chunks))  # type: ignore[attr-defined]
        results: list[RetrievalResult] = []
        for score, index in zip(scores[0].tolist(), indexes[0].tolist(), strict=True):
            if index < 0:
                continue
            chunk = self._chunks[index]
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=hybrid_retrieval_score(
                        query_text,
                        chunk.text,
                        float(score),
                    ),
                )
            )
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

    def _rebuild_faiss_index(self) -> None:
        try:
            import faiss
            import numpy as np
        except ImportError:
            self._faiss_index = None
            self.backend_name = "python"
            return

        if not self._vectors:
            self._faiss_index = None
            self.backend_name = "python"
            return

        vectors = np.array(self._vectors, dtype="float32")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        self._faiss_index = index
        self.backend_name = "faiss"


def _dot(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=True)))
