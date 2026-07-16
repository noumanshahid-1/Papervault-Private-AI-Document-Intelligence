"""Tests for privacy-preserving session API routes."""

import sqlite3

from fastapi.testclient import TestClient

import app.main as main_module
from app.services.checklist_engine import generate_checklist
from app.services.insight_engine import analyze_document
from app.storage.database import DocuSenseDatabase


SAMPLE_TEXT = """
Admission Offer Letter
Required documents: passport copy and official transcript.
You must accept this offer by July 15, 2026.
"""


def test_session_routes_do_not_store_raw_text_by_default(tmp_path, monkeypatch) -> None:
    database = DocuSenseDatabase(
        tmp_path / "docsense.sqlite3",
        store_extracted_text=False,
    )
    monkeypatch.setattr(main_module, "_db", database)
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    checklist = generate_checklist(insight)
    client = TestClient(main_module.app)

    response = client.post(
        "/sessions",
        json={
            "filename": "admission.txt",
            "document_type": insight.classification.document_type,
            "extracted_text": SAMPLE_TEXT,
            "insight": insight.model_dump(mode="json"),
            "checklist": checklist.model_dump(mode="json"),
        },
    )

    assert response.status_code == 200
    session_id = response.json()["id"]

    detail = client.get(f"/sessions/{session_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["content_stored"] is False
    assert payload["extracted_text"] is None

    with sqlite3.connect(database.path) as connection:
        stored_text = connection.execute(
            "SELECT extracted_text FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
    assert stored_text == ""


def test_session_routes_list_and_clear_history(tmp_path, monkeypatch) -> None:
    database = DocuSenseDatabase(
        tmp_path / "docsense.sqlite3",
        store_extracted_text=False,
    )
    monkeypatch.setattr(main_module, "_db", database)
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    checklist = generate_checklist(insight)
    client = TestClient(main_module.app)
    client.post(
        "/sessions",
        json={
            "filename": "admission.txt",
            "document_type": insight.classification.document_type,
            "extracted_text": SAMPLE_TEXT,
            "insight": insight.model_dump(mode="json"),
            "checklist": checklist.model_dump(mode="json"),
        },
    )

    listed = client.get("/sessions")
    assert listed.status_code == 200
    assert listed.json()[0]["content_stored"] is False

    cleared = client.delete("/sessions")
    assert cleared.status_code == 200
    assert cleared.json() == {"deleted": True}
    assert client.get("/sessions").json() == []
