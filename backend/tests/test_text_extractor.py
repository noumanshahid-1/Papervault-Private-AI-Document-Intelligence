"""Tests for local document validation and text extraction."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import UploadedDocument
from app.services.document_loader import UnsupportedDocumentTypeError, load_document
from app.services.text_extractor import extract_text
from app.utils.text_cleaning import normalize_extracted_text, normalize_whitespace


def test_normalize_whitespace_collapses_spacing() -> None:
    assert normalize_whitespace("  Hello\t\tworld\n\nagain  ") == "Hello world again"


def test_normalize_extracted_text_preserves_paragraph_breaks() -> None:
    raw = " First line   has   gaps.\n\n\nSecond\tline.\r\nThird line. "

    assert normalize_extracted_text(raw) == (
        "First line has gaps.\n\nSecond line.\nThird line."
    )


def test_load_document_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedDocumentTypeError) as exc_info:
        load_document(filename="malware.exe", content=b"not a document")

    assert ".exe" in str(exc_info.value)


def test_extract_txt_returns_clean_text() -> None:
    document = UploadedDocument(
        filename="note.txt",
        content=b"  Scholarship   deadline:\n\nJune 1, 2026  ",
        extension=".txt",
        content_type="text/plain",
        size_bytes=39,
    )

    result = extract_text(document)

    assert result.filename == "note.txt"
    assert result.document_type == "txt"
    assert result.text == "Scholarship deadline:\n\nJune 1, 2026"
    assert result.warnings == []
    assert result.error is None
    assert result.metadata["size_bytes"] == 39


def test_extract_pdf_generated_programmatically() -> None:
    fitz = pytest.importorskip("fitz")
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Admission offer deadline is July 15, 2026.")
    pdf_bytes = pdf.tobytes()
    pdf.close()

    document = UploadedDocument(
        filename="admission.pdf",
        content=pdf_bytes,
        extension=".pdf",
        content_type="application/pdf",
        size_bytes=len(pdf_bytes),
    )

    result = extract_text(document)

    assert "Admission offer deadline" in result.text
    assert result.document_type == "pdf"
    assert result.page_count == 1
    assert result.error is None
    assert result.diagnostics.engine == "pymupdf"
    assert result.diagnostics.page_text_coverage == 1
    assert result.diagnostics.confidence in {"medium", "high"}


def test_extract_image_without_local_ocr_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import text_extractor

    monkeypatch.setattr(text_extractor, "_tesseract_is_available", lambda: False)
    monkeypatch.setattr(text_extractor, "_extract_image_with_rapidocr", lambda document: text_extractor._result(
        document,
        text="",
        warnings=["No local OCR engine is available."],
        error=text_extractor.ExtractionError(
            code="ocr_unavailable",
            message="No local OCR engine is available.",
        ),
    ))
    document = UploadedDocument(
        filename="scan.png",
        content=b"not-real-image",
        extension=".png",
        content_type="image/png",
        size_bytes=14,
    )

    result = extract_text(document)

    assert result.text == ""
    assert result.error is not None
    assert result.error.code == "ocr_unavailable"
    assert "No local OCR engine" in result.error.message
    assert result.warnings


def test_extract_image_uses_local_ocr_fallback_when_tesseract_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import text_extractor

    monkeypatch.setattr(text_extractor, "_tesseract_is_available", lambda: False)
    monkeypatch.setattr(
        text_extractor,
        "_extract_image_with_rapidocr",
        lambda document: text_extractor._result(
            document,
            text="Required documents: passport copy.",
            warnings=["Tesseract was not found; used RapidOCR local fallback."],
        ),
    )
    document = UploadedDocument(
        filename="scan.jpg",
        content=b"image-bytes",
        extension=".jpg",
        content_type="image/jpeg",
        size_bytes=11,
    )

    result = extract_text(document)

    assert result.error is None
    assert "passport copy" in result.text
    assert result.warnings == ["Tesseract was not found; used RapidOCR local fallback."]


def test_extract_endpoint_returns_text_for_uploaded_txt() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={"file": ("sample.txt", b" Visa instructions\n\nSubmit passport copy. ", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.txt"
    assert payload["text"] == "Visa instructions\n\nSubmit passport copy."
    assert payload["error"] is None
    assert payload["diagnostics"]["engine"] == "plain_text"
    assert payload["diagnostics"]["confidence_score"] > 0


def test_extract_endpoint_rejects_unsupported_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={"file": ("sample.exe", b"bad", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]
