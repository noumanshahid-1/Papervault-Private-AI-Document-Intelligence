"""Optional Ollama-compatible local LLM adapter with graceful fallback."""

from dataclasses import dataclass

import requests

from app.config import get_settings
from app.models.schemas import LocalModelInfo


class LocalLLMUnavailableError(RuntimeError):
    """Raised when optional local LLM inference is unavailable."""


@dataclass(frozen=True)
class LocalLLMResult:
    """Result from an optional local LLM generation attempt."""

    text: str
    available: bool
    model: str | None = None
    error: str | None = None


class OllamaLLMAdapter:
    """Small adapter for Ollama's local `/api/generate` endpoint."""

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        discovery_timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self.enabled = settings.local_llm_enabled if enabled is None else enabled
        self.base_url = (base_url or settings.local_llm_base_url).rstrip("/")
        self.model = model or settings.local_llm_model
        self.timeout = timeout if timeout is not None else settings.local_llm_timeout
        self.discovery_timeout = (
            discovery_timeout
            if discovery_timeout is not None
            else settings.local_llm_discovery_timeout
        )

    def generate(self, prompt: str) -> LocalLLMResult:
        """Generate text locally, returning unavailable state on any failure."""
        if not self.enabled:
            return LocalLLMResult(
                text="",
                available=False,
                model=self.model,
                error="Local LLM disabled; using extractive mode.",
            )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            return LocalLLMResult(
                text="",
                available=False,
                model=self.model,
                error=f"Local LLM unavailable; using extractive mode. Details: {exc}",
            )
        except ValueError as exc:
            return LocalLLMResult(
                text="",
                available=False,
                model=self.model,
                error=f"Local LLM returned invalid JSON; using extractive mode. Details: {exc}",
            )

        generated = str(payload.get("response") or "").strip()
        if not generated:
            return LocalLLMResult(
                text="",
                available=False,
                model=self.model,
                error="Local LLM returned an empty response; using extractive mode.",
            )

        return LocalLLMResult(text=generated, available=True, model=self.model)

    def discover_models(self) -> tuple[list[LocalModelInfo], str | None]:
        """Return locally installed Ollama models without changing runtime state."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.discovery_timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            return [], f"Ollama is not reachable: {exc}"
        except ValueError as exc:
            return [], f"Ollama returned invalid model metadata: {exc}"

        models: list[LocalModelInfo] = []
        for item in payload.get("models") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if not name:
                continue
            size = item.get("size")
            models.append(
                LocalModelInfo(
                    name=name,
                    size_bytes=int(size) if isinstance(size, (int, float)) else None,
                    modified_at=(
                        str(item["modified_at"])
                        if item.get("modified_at")
                        else None
                    ),
                )
            )
        return models, None


def build_summary_prompt(document_text: str) -> str:
    """Build a grounded summary prompt."""
    return _strict_prompt(
        "Summarize the document in clear plain language.",
        f"Document text:\n{document_text}",
    )


def build_document_explanation_prompt(document_text: str) -> str:
    """Build a grounded explanation prompt."""
    return _strict_prompt(
        "Explain what this document appears to be asking the reader to understand or do.",
        f"Document text:\n{document_text}",
    )


def build_qa_prompt(context: str, question: str) -> str:
    """Build a Q&A prompt constrained to retrieved context."""
    return _strict_prompt(
        f"Answer the question using only the context.\nQuestion: {question}",
        f"Context:\n{context}",
    )


def build_risk_explanation_prompt(risk_context: str) -> str:
    """Build a cautious risk explanation prompt."""
    return _strict_prompt(
        "Explain possible issues and verification steps using careful non-advisory language.",
        f"Risk context:\n{risk_context}",
    )


def _strict_prompt(task: str, source: str) -> str:
    return (
        "You are DocuSense AI, a local document intelligence assistant.\n"
        "Only use the provided context or document text.\n"
        "If the answer is not found, say \"not found in the document\".\n"
        "Do not invent deadlines, requirements, contacts, amounts, or facts.\n"
        "Do not present legal, medical, financial, immigration, or government conclusions as professional advice.\n"
        "Use careful language such as \"document appears to mention\" and \"verify this\".\n\n"
        f"Task:\n{task}\n\n"
        f"Provided source:\n{source}\n"
    )
