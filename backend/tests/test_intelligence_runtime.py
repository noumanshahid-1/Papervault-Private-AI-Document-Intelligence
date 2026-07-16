"""Tests for local model and retrieval runtime diagnostics."""

from fastapi.testclient import TestClient

from app.main import app


def test_runtime_endpoint_reports_local_provider_status() -> None:
    response = TestClient(app).get("/intelligence/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["embedding_provider"] in {"hashing", "sentence_transformers"}
    assert payload["vector_backend"] in {"python", "faiss"}
    assert isinstance(payload["available_models"], list)
    assert payload["configured_model"]
    assert payload["status_message"]
