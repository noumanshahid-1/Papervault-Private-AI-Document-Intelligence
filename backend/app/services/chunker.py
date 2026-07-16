"""Text chunking for local retrieval-augmented generation."""

from app.models.schemas import DocumentChunk
from app.utils.text_cleaning import normalize_extracted_text


DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150


def chunk_text(
    text: str,
    *,
    filename: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Split text into overlapping chunks with source metadata."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    source_name = filename or "document"
    chunks: list[DocumentChunk] = []
    page_offset = 0

    for page_index, page_text in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\f"), start=1):
        normalized_page = normalize_extracted_text(page_text)
        if not normalized_page:
            page_offset += len(page_text) + 1
            continue
        for start, end, chunk_body in _chunk_page(normalized_page, chunk_size, chunk_overlap):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source_name}:{len(chunks)}",
                    text=chunk_body,
                    page_number=page_index,
                    char_start=page_offset + start,
                    char_end=page_offset + end,
                    source_filename=filename,
                )
            )
        page_offset += len(page_text) + 1

    return chunks


def _chunk_page(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            boundary = text.rfind(" ", start + max(1, chunk_size // 2), end)
            if boundary > start:
                end = boundary

        chunk_body = text[start:end].strip()
        if chunk_body:
            leading_trim = len(text[start:end]) - len(text[start:end].lstrip())
            trailing_trim = len(text[start:end].rstrip())
            adjusted_start = start + leading_trim
            adjusted_end = start + trailing_trim
            chunks.append((adjusted_start, adjusted_end, chunk_body))

        if end >= text_length:
            break
        start = max(0, end - chunk_overlap)

    return chunks
