"""Tests for local SQLite session persistence."""

import sqlite3

from app.models.schemas import OfficialNoticeBreakdown, OfficialNoticeTableRow
from app.services.checklist_engine import generate_checklist
from app.services.insight_engine import analyze_document
from app.services.qa_engine import answer_question
from app.storage.database import (
    DocuSenseDatabase,
    initialize_database,
    text_sha256,
)


SAMPLE_TEXT = """
Admission Offer Letter
Required documents: passport copy and official transcript.
You must accept this offer by July 15, 2026.
Failure to submit documents may delay enrollment.
"""


def test_initialize_database_creates_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "docsense.sqlite3"

    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"sessions", "qa_history"}.issubset(tables)


def test_save_and_load_session_without_storing_raw_text(tmp_path) -> None:
    db = DocuSenseDatabase(tmp_path / "docsense.sqlite3")
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    insight.official_notice = OfficialNoticeBreakdown(
        notice_type="notification",
        table_rows=[
            OfficialNoticeTableRow(
                service="Custom House Agents",
                source_snippet="Sensitive source table text",
            )
        ],
    )
    checklist = generate_checklist(insight)
    qa = [
        answer_question(
            text=SAMPLE_TEXT,
            question="What is the deadline?",
            filename="admission.txt",
        )
    ]

    session_id = db.save_session(
        filename="admission.txt",
        extracted_text=SAMPLE_TEXT,
        insight=insight,
        checklist=checklist,
        qa_history=qa,
    )
    loaded = db.get_session(session_id)

    assert loaded is not None
    assert loaded.session_id == session_id
    assert loaded.filename == "admission.txt"
    assert loaded.extracted_text_hash == text_sha256(SAMPLE_TEXT)
    assert loaded.content_stored is False
    assert loaded.extracted_text is None
    assert loaded.insight.classification.document_type == "university admission letter"
    assert loaded.checklist.items
    assert loaded.qa_history[0].answer
    assert loaded.insight.official_notice is not None
    assert loaded.insight.official_notice.table_rows[0].source_snippet is None

    with sqlite3.connect(tmp_path / "docsense.sqlite3") as connection:
        raw_db_values = "\n".join(
            str(row)
            for row in connection.execute(
                """
                SELECT filename, extracted_text_hash, insight_json,
                       checklist_json, extracted_text
                FROM sessions
                """
            )
        )
    assert SAMPLE_TEXT.strip() not in raw_db_values
    assert '"source_snippet":"Required documents' not in raw_db_values


def test_list_sessions_returns_recent_metadata_only(tmp_path) -> None:
    db = DocuSenseDatabase(tmp_path / "docsense.sqlite3")
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    checklist = generate_checklist(insight)
    db.save_session(
        filename="admission.txt",
        extracted_text=SAMPLE_TEXT,
        insight=insight,
        checklist=checklist,
        qa_history=[],
    )

    sessions = db.list_sessions()

    assert len(sessions) == 1
    assert sessions[0].filename == "admission.txt"
    assert sessions[0].document_type == "university admission letter"
    assert sessions[0].content_stored is False
    assert sessions[0].text_preview is None


def test_full_text_history_requires_explicit_opt_in(tmp_path) -> None:
    db = DocuSenseDatabase(
        tmp_path / "docsense.sqlite3",
        store_extracted_text=True,
    )
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    checklist = generate_checklist(insight)

    session_id = db.save_session(
        filename="admission.txt",
        extracted_text=SAMPLE_TEXT,
        insight=insight,
        checklist=checklist,
    )
    loaded = db.get_session(session_id)

    assert loaded is not None
    assert loaded.content_stored is True
    assert loaded.extracted_text == SAMPLE_TEXT


def test_privacy_mode_sanitizes_legacy_full_text_sessions(tmp_path) -> None:
    path = tmp_path / "docsense.sqlite3"
    opted_in = DocuSenseDatabase(path, store_extracted_text=True)
    insight = analyze_document(SAMPLE_TEXT, filename="admission.txt")
    checklist = generate_checklist(insight)
    session_id = opted_in.save_session(
        filename="admission.txt",
        extracted_text=SAMPLE_TEXT,
        insight=insight,
        checklist=checklist,
    )

    privacy_db = DocuSenseDatabase(path, store_extracted_text=False)
    loaded = privacy_db.get_session(session_id)

    assert loaded is not None
    assert loaded.content_stored is False
    assert loaded.extracted_text is None
    assert all(item.source_snippet is None for item in loaded.insight.important_dates)
