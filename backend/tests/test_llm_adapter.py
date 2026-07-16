"""Tests for optional local LLM adapter behavior."""

import requests

from app.services.llm_adapter import (
    OllamaLLMAdapter,
    build_document_explanation_prompt,
    build_qa_prompt,
    build_risk_explanation_prompt,
    build_summary_prompt,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict[str, object]:
        return self._payload


def test_disabled_adapter_returns_unavailable_without_http_call(
    monkeypatch,
) -> None:
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("HTTP should not be called when disabled")

    monkeypatch.setattr(requests, "post", fake_post)
    adapter = OllamaLLMAdapter(enabled=False)

    result = adapter.generate("Summarize this.")

    assert result.available is False
    assert result.text == ""
    assert "disabled" in result.error.lower()
    assert called is False


def test_adapter_parses_ollama_generate_response(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/generate"
        assert json["stream"] is False
        assert json["model"] == "llama3.2"
        assert "Only use the provided context" in json["prompt"]
        assert timeout == 12
        return _FakeResponse({"response": "The deadline is July 15, 2026."})

    monkeypatch.setattr(requests, "post", fake_post)
    adapter = OllamaLLMAdapter(
        enabled=True,
        base_url="http://localhost:11434/",
        model="llama3.2",
        timeout=12,
    )

    result = adapter.generate(build_qa_prompt("Deadline July 15, 2026.", "What is due?"))

    assert result.available is True
    assert result.text == "The deadline is July 15, 2026."
    assert result.model == "llama3.2"
    assert result.error is None


def test_adapter_handles_connection_error_as_unavailable(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)
    adapter = OllamaLLMAdapter(enabled=True)

    result = adapter.generate("Prompt")

    assert result.available is False
    assert result.text == ""
    assert "Local LLM unavailable" in result.error


def test_adapter_discovers_installed_ollama_models(monkeypatch) -> None:
    def fake_get(url, timeout):
        assert url == "http://localhost:11434/api/tags"
        assert timeout == 2
        return _FakeResponse(
            {
                "models": [
                    {
                        "name": "qwen2.5:7b",
                        "size": 4_500_000_000,
                        "modified_at": "2026-07-17T00:00:00Z",
                    },
                    {"model": "llama3.2:3b", "size": 2_000_000_000},
                ]
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)
    adapter = OllamaLLMAdapter(enabled=True, discovery_timeout=2)

    models, error = adapter.discover_models()

    assert error is None
    assert [model.name for model in models] == ["qwen2.5:7b", "llama3.2:3b"]
    assert models[0].size_bytes == 4_500_000_000


def test_prompt_templates_include_strict_grounding_rules() -> None:
    prompts = [
        build_summary_prompt("Document text"),
        build_document_explanation_prompt("Document text"),
        build_qa_prompt("Context text", "Question?"),
        build_risk_explanation_prompt("Risk context"),
    ]

    for prompt in prompts:
        assert "Only use the provided" in prompt
        assert "not found" in prompt.lower()
        assert "Do not invent" in prompt
        assert "professional advice" in prompt
