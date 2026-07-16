"""SQLite persistence for local-only Papervault session metadata."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from app.config import get_settings
from app.models.schemas import (
    ChecklistResult,
    DocumentInsight,
    QuestionAnswer,
    SavedSession,
    SessionMetadata,
)


DEFAULT_DATABASE_NAME = "docsense.sqlite3"


def text_sha256(text: str) -> str:
    """Return a stable SHA-256 hash for extracted text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_database_path() -> Path:
    """Return the configured local SQLite path."""
    settings = get_settings()
    return settings.data_dir / DEFAULT_DATABASE_NAME


def initialize_database(path: str | Path | None = None) -> Path:
    """Create the local SQLite database and required tables."""
    db_path = Path(path) if path is not None else default_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                extracted_text_hash TEXT NOT NULL,
                insight_json TEXT NOT NULL,
                checklist_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                extracted_text TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS qa_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                qa_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
            """
        )
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
        }
        if "extracted_text" not in columns:
            connection.execute(
                "ALTER TABLE sessions ADD COLUMN extracted_text TEXT NOT NULL DEFAULT ''"
            )
    return db_path


class DocuSenseDatabase:
    """Repository for privacy-preserving local session history."""

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        store_extracted_text: bool | None = None,
    ) -> None:
        settings = get_settings()
        self.store_extracted_text = (
            settings.store_extracted_text
            if store_extracted_text is None
            else store_extracted_text
        )
        self.path = initialize_database(path)
        if not self.store_extracted_text:
            self._sanitize_existing_sessions()

    def save_session(
        self,
        *,
        filename: str,
        extracted_text: str,
        insight: DocumentInsight,
        checklist: ChecklistResult,
        qa_history: list[QuestionAnswer] | None = None,
    ) -> str:
        """Save privacy-preserving history, with raw text retained only by opt-in."""
        session_id = str(uuid4())
        created_at = _utc_now()
        qa_history = qa_history or []
        stored_insight = _redact_insight_sources(insight)
        stored_checklist = _redact_checklist_sources(checklist)
        stored_qa_history = [_redact_qa_sources(answer) for answer in qa_history]
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id, filename, document_type, extracted_text_hash,
                    insight_json, checklist_json, created_at, extracted_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    filename,
                    insight.classification.document_type,
                    text_sha256(extracted_text),
                    stored_insight.model_dump_json(),
                    stored_checklist.model_dump_json(),
                    created_at,
                    extracted_text if self.store_extracted_text else "",
                ),
            )
            connection.executemany(
                """
                INSERT INTO qa_history (session_id, qa_json, created_at)
                VALUES (?, ?, ?)
                """,
                [
                    (session_id, answer.model_dump_json(), created_at)
                    for answer in stored_qa_history
                ],
            )
        return session_id

    def get_session(self, session_id: str) -> SavedSession | None:
        """Load a saved session by id."""
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT session_id, filename, document_type, extracted_text_hash,
                       insight_json, checklist_json, created_at, extracted_text
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            qa_rows = connection.execute(
                """
                SELECT qa_json FROM qa_history
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return SavedSession(
            session_id=row["session_id"],
            filename=row["filename"],
            document_type=row["document_type"],
            extracted_text_hash=row["extracted_text_hash"],
            created_at=row["created_at"],
            content_stored=bool(row["extracted_text"]),
            text_preview=None,
            insight=DocumentInsight.model_validate_json(row["insight_json"]),
            checklist=ChecklistResult.model_validate_json(row["checklist_json"]),
            qa_history=[
                QuestionAnswer.model_validate_json(qa_row["qa_json"])
                for qa_row in qa_rows
            ],
            extracted_text=row["extracted_text"] or None,
        )

    def list_sessions(self, limit: int = 20) -> list[SessionMetadata]:
        """Return recent saved session metadata without raw text."""
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT session_id, filename, document_type, extracted_text_hash,
                       created_at, extracted_text
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            SessionMetadata(
                session_id=row["session_id"],
                filename=row["filename"],
                document_type=row["document_type"],
                extracted_text_hash=row["extracted_text_hash"],
                created_at=row["created_at"],
                content_stored=bool(row["extracted_text"]),
                text_preview=None,
            )
            for row in rows
        ]

    def clear_sessions(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM qa_history")
            connection.execute("DELETE FROM sessions")

    def _sanitize_existing_sessions(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            session_rows = connection.execute(
                "SELECT session_id, insight_json, checklist_json FROM sessions"
            ).fetchall()
            for row in session_rows:
                try:
                    insight = DocumentInsight.model_validate_json(row["insight_json"])
                    checklist = ChecklistResult.model_validate_json(row["checklist_json"])
                except (ValueError, TypeError):
                    connection.execute(
                        "UPDATE sessions SET extracted_text = '' WHERE session_id = ?",
                        (row["session_id"],),
                    )
                    continue
                connection.execute(
                    """
                    UPDATE sessions
                    SET insight_json = ?, checklist_json = ?, extracted_text = ''
                    WHERE session_id = ?
                    """,
                    (
                        _redact_insight_sources(insight).model_dump_json(),
                        _redact_checklist_sources(checklist).model_dump_json(),
                        row["session_id"],
                    ),
                )

            qa_rows = connection.execute(
                "SELECT id, qa_json FROM qa_history"
            ).fetchall()
            for row in qa_rows:
                try:
                    answer = QuestionAnswer.model_validate_json(row["qa_json"])
                except (ValueError, TypeError):
                    continue
                connection.execute(
                    "UPDATE qa_history SET qa_json = ? WHERE id = ?",
                    (_redact_qa_sources(answer).model_dump_json(), row["id"]),
                )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _redact_insight_sources(insight: DocumentInsight) -> DocumentInsight:
    stored = insight.model_copy(deep=True)
    for item in stored.important_dates:
        item.source_snippet = None
    for item in stored.fees_or_amounts:
        item.source_snippet = None
    for risk in stored.risks:
        risk.source_snippet = None
    if stored.official_notice:
        for row in stored.official_notice.table_rows:
            row.source_snippet = None
    return stored


def _redact_checklist_sources(checklist: ChecklistResult) -> ChecklistResult:
    stored = checklist.model_copy(deep=True)
    for item in stored.items:
        item.source_snippet = None
    for risk in stored.risks:
        risk.source_snippet = None
    return stored


def _redact_qa_sources(answer: QuestionAnswer) -> QuestionAnswer:
    stored = answer.model_copy(deep=True)
    stored.source_snippets = []
    return stored
