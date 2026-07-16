"""Document loading and upload validation for local-only processing."""

from pathlib import Path

from app.models.schemas import UploadedDocument

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".md", ".docx"}
DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class DocumentLoaderError(ValueError):
    """Base class for document upload validation errors."""


class UnsupportedDocumentTypeError(DocumentLoaderError):
    """Raised when an uploaded file extension is not supported."""


class EmptyDocumentError(DocumentLoaderError):
    """Raised when an uploaded file has no content."""


class DocumentTooLargeError(DocumentLoaderError):
    """Raised when an uploaded file exceeds the local processing limit."""


def supported_extensions() -> set[str]:
    """Return file extensions planned for local document ingestion."""
    return set(SUPPORTED_EXTENSIONS)


def sanitize_filename(filename: str) -> str:
    """Return only the filename portion to avoid trusting client paths."""
    sanitized = Path(filename or "uploaded-document").name.strip()
    return sanitized or "uploaded-document"


def load_document(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    max_size_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> UploadedDocument:
    """Validate uploaded bytes and return an in-memory document object."""
    safe_filename = sanitize_filename(filename)
    extension = Path(safe_filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentTypeError(
            f"Unsupported document type '{extension or 'none'}'. Supported types: {allowed}."
        )

    size_bytes = len(content)
    if size_bytes == 0:
        raise EmptyDocumentError("Uploaded document is empty.")
    if size_bytes > max_size_bytes:
        size_mb = max_size_bytes / (1024 * 1024)
        raise DocumentTooLargeError(
            f"Uploaded document is too large. Maximum size is {size_mb:.0f} MB."
        )

    return UploadedDocument(
        filename=safe_filename,
        content=content,
        extension=extension,
        content_type=content_type,
        size_bytes=size_bytes,
    )
