"""Tests for local RAG chunking."""

from app.services.chunker import chunk_text


def test_chunk_text_adds_metadata_and_overlap() -> None:
    text = (
        "Admission offer details. Required documents include passport copy and transcript. "
        "The acceptance deadline is July 15, 2026. Pay the enrollment deposit before registration."
    )

    chunks = chunk_text(
        text,
        filename="admission.txt",
        chunk_size=80,
        chunk_overlap=20,
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_id == "admission.txt:0"
    assert chunks[0].source_filename == "admission.txt"
    assert chunks[0].char_start == 0
    assert chunks[0].char_end > chunks[0].char_start
    assert chunks[1].char_start < chunks[0].char_end
    assert all(chunk.text.strip() for chunk in chunks)


def test_chunk_text_tracks_page_numbers_from_form_feed() -> None:
    text = "Page one admission text.\fPage two deadline July 15, 2026."

    chunks = chunk_text(text, filename="pages.pdf", chunk_size=200)

    assert [chunk.page_number for chunk in chunks] == [1, 2]
    assert chunks[1].char_start > chunks[0].char_start
