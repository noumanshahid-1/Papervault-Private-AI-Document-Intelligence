"""Describe configured local intelligence providers and Ollama availability."""

from __future__ import annotations

import importlib.util

from app.config import get_settings
from app.models.schemas import IntelligenceRuntimeResponse
from app.services.embeddings import get_embedding_provider
from app.services.llm_adapter import OllamaLLMAdapter


def get_intelligence_runtime() -> IntelligenceRuntimeResponse:
    """Return local provider configuration with bounded Ollama discovery."""
    settings = get_settings()
    provider = get_embedding_provider()
    models = []
    ollama_available = False
    status_message = "Local LLM is disabled; extractive Q&A remains available."

    if settings.local_llm_enabled:
        adapter = OllamaLLMAdapter()
        models, discovery_error = adapter.discover_models()
        ollama_available = discovery_error is None
        if discovery_error:
            status_message = (
                "Ollama is enabled but unavailable. Questions will use extractive fallback."
            )
        elif models:
            status_message = f"Ollama is ready with {len(models)} installed model(s)."
        else:
            status_message = (
                "Ollama is reachable but no installed models were reported."
            )

    return IntelligenceRuntimeResponse(
        local_llm_enabled=settings.local_llm_enabled,
        ollama_available=ollama_available,
        configured_model=settings.local_llm_model,
        available_models=models,
        embedding_provider=getattr(provider, "provider_name", "unknown"),
        embedding_model=getattr(provider, "model_name", None),
        vector_backend=(
            "faiss" if importlib.util.find_spec("faiss") is not None else "python"
        ),
        status_message=status_message,
    )
