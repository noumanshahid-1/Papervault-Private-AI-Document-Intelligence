"""Shared Pydantic schemas for DocuSense AI APIs and services."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for backend health checks."""

    status: str = Field(description="Service status.")
    app: str = Field(description="Application name.")


class UploadedDocument(BaseModel):
    """In-memory representation of a validated uploaded document."""

    filename: str = Field(description="Sanitized source filename.")
    content: bytes = Field(description="Raw uploaded file bytes.")
    extension: str = Field(description="Lowercase file extension, including dot.")
    content_type: str | None = Field(default=None, description="Browser-provided MIME type.")
    size_bytes: int = Field(ge=0, description="Uploaded file size in bytes.")


class ExtractionError(BaseModel):
    """Structured extraction error suitable for user-facing feedback."""

    code: str = Field(description="Stable machine-readable error code.")
    message: str = Field(description="Human-readable error message.")


class ExtractionDiagnostics(BaseModel):
    """Explainable quality assessment for locally extracted text."""

    engine: str = Field(default="unknown", description="Extraction or OCR engine used.")
    confidence: str = Field(default="low", description="low, medium, or high.")
    confidence_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Normalized extraction quality score.",
    )
    is_ocr: bool = Field(default=False, description="Whether OCR produced the text.")
    ocr_engine: str | None = Field(default=None, description="OCR engine name when used.")
    ocr_mean_confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Mean OCR token confidence when the engine exposes it.",
    )
    word_count: int = Field(default=0, ge=0)
    character_count: int = Field(default=0, ge=0)
    readable_character_ratio: float = Field(default=0.0, ge=0, le=1)
    suspicious_character_ratio: float = Field(default=0.0, ge=0, le=1)
    page_text_coverage: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Share of pages containing meaningful text.",
    )
    signals: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Result of extracting text from a document without interpretation."""

    filename: str = Field(description="Source filename.")
    document_type: str = Field(description="Document extension without leading dot.")
    text: str = Field(description="Clean extracted text.")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings.")
    error: ExtractionError | None = Field(
        default=None, description="Structured error when extraction could not complete."
    )
    page_count: int | None = Field(default=None, description="Number of pages when known.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Local extraction metadata."
    )
    diagnostics: ExtractionDiagnostics = Field(default_factory=ExtractionDiagnostics)


class AnalyzeRequest(BaseModel):
    """Request body for analyzing already-extracted document text."""

    text: str = Field(description="Extracted document text to analyze.")
    filename: str | None = Field(default=None, description="Optional source filename.")


class ClassificationResult(BaseModel):
    """Deterministic document classification result."""

    document_type: str = Field(description="Best matching document category.")
    confidence: str = Field(description="low, medium, or high.")
    evidence: list[str] = Field(
        default_factory=list, description="Document snippets that supported classification."
    )


class ExtractedItem(BaseModel):
    """A grounded extracted value with optional source text."""

    value: str = Field(description="Extracted value.")
    source_snippet: str | None = Field(
        default=None, description="Nearby source text from the document."
    )


class RiskInsight(BaseModel):
    """Carefully worded possible risk grounded in document text."""

    issue: str = Field(description="Possible issue, not a definitive conclusion.")
    why_it_matters: str = Field(description="Plain-language reason to verify it.")
    suggested_verification: str = Field(description="Recommended verification step.")
    confidence: str = Field(description="low, medium, or high.")
    source_snippet: str | None = Field(default=None, description="Grounding snippet.")


class OfficialNoticeTableRow(BaseModel):
    """Structured row recovered from an official notice table."""

    service: str | None = Field(default=None, description="Taxable service or subject.")
    heading: str | None = Field(default=None, description="Schedule heading or code.")
    liable_party: str | None = Field(default=None, description="Person or party made liable.")
    rate_or_amount: str | None = Field(default=None, description="Rate, fee, or amount.")
    source_snippet: str | None = Field(default=None, description="Grounding source text.")


class OfficialNoticeBreakdown(BaseModel):
    """Domain-specific breakdown for government notices and gazette notifications."""

    issuing_authority: str | None = Field(default=None)
    notice_type: str | None = Field(default=None)
    notice_number: str | None = Field(default=None)
    gazette_date: str | None = Field(default=None)
    issue_date: str | None = Field(default=None)
    legal_basis: str | None = Field(default=None)
    subject: str | None = Field(default=None)
    effective_timing: str | None = Field(default=None)
    payment_timing: str | None = Field(default=None)
    table_rows: list[OfficialNoticeTableRow] = Field(default_factory=list)
    compliance_duties: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    confidence: str = Field(default="low", description="low, medium, or high.")
    limitations: list[str] = Field(default_factory=list)


class DocumentAnalysisDiagnostics(BaseModel):
    """Signals used to explain document-analysis confidence."""

    confidence_score: float = Field(default=0.0, ge=0, le=1)
    classification_confidence: str = Field(default="low")
    extracted_signal_count: int = Field(default=0, ge=0)
    grounded_field_count: int = Field(default=0, ge=0)
    reasons: list[str] = Field(default_factory=list)


class DocumentInsight(BaseModel):
    """Structured document insights derived from extracted text."""

    title: str | None = Field(default=None, description="Likely document title.")
    classification: ClassificationResult = Field(description="Document classification.")
    summary: str = Field(description="Short extractive summary.")
    important_dates: list[ExtractedItem] = Field(default_factory=list)
    fees_or_amounts: list[ExtractedItem] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    risks: list[RiskInsight] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contact_information: list[str] = Field(default_factory=list)
    official_notice: OfficialNoticeBreakdown | None = Field(default=None)
    confidence: str = Field(description="Overall extraction confidence.")
    diagnostics: DocumentAnalysisDiagnostics = Field(
        default_factory=DocumentAnalysisDiagnostics
    )
    limitations: list[str] = Field(default_factory=list)


class ChecklistItem(BaseModel):
    """Actionable checklist item derived from grounded document insights."""

    title: str = Field(description="Short action title.")
    reason: str = Field(description="Why this task matters.")
    priority: str = Field(description="high, medium, or low.")
    due_date: str | None = Field(default=None, description="Associated due date if known.")
    source_snippet: str | None = Field(
        default=None, description="Source text that supports this task."
    )
    status: str = Field(default="pending", description="Checklist status.")


class RiskPanelItem(BaseModel):
    """Risk panel item with careful non-advisory wording."""

    possible_issue: str = Field(description="Possible issue found in the document.")
    why_it_matters: str = Field(description="Why the user should verify it.")
    suggested_verification_step: str = Field(description="Suggested verification step.")
    confidence_level: str = Field(description="low, medium, or high.")
    source_snippet: str | None = Field(default=None, description="Grounding source text.")


class ChecklistResult(BaseModel):
    """Checklist and risk panel generated from document insights."""

    items: list[ChecklistItem] = Field(default_factory=list)
    risks: list[RiskPanelItem] = Field(default_factory=list)
    guidance: str = Field(description="User-facing guidance for the checklist result.")


class DocumentChunk(BaseModel):
    """Chunk of document text prepared for local retrieval."""

    chunk_id: str = Field(description="Stable chunk identifier.")
    text: str = Field(description="Chunk text.")
    page_number: int | None = Field(default=None, description="Source page number if known.")
    char_start: int = Field(ge=0, description="Start character offset in source text.")
    char_end: int = Field(ge=0, description="End character offset in source text.")
    source_filename: str | None = Field(default=None, description="Source filename if known.")


class RetrievalResult(BaseModel):
    """A retrieved chunk with a local relevance score."""

    chunk: DocumentChunk = Field(description="Retrieved document chunk.")
    score: float = Field(
        description="Hybrid vector, lexical, and intent relevance score."
    )


class AskRequest(BaseModel):
    """Request body for local document question answering."""

    text: str = Field(description="Extracted document text to search.")
    question: str = Field(description="Question to answer from the document.")
    filename: str | None = Field(default=None, description="Optional source filename.")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of chunks to retrieve.")
    answer_mode: Literal["auto", "extractive", "local_llm"] = Field(
        default="auto",
        description="Preferred answer mode. Local LLM mode still falls back safely.",
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional installed Ollama model override for this question.",
    )


class SourceSnippet(BaseModel):
    """Source snippet used to ground an answer."""

    text: str = Field(description="Source text snippet.")
    chunk_id: str = Field(description="Source chunk identifier.")
    score: float = Field(description="Retrieval similarity score.")
    page_number: int | None = Field(default=None, description="Source page number if known.")
    source_filename: str | None = Field(default=None, description="Source filename if known.")


class RetrievalDiagnostics(BaseModel):
    """Explain how document chunks were selected for an answer."""

    embedding_provider: str = Field(default="unknown")
    embedding_model: str | None = Field(default=None)
    vector_backend: str = Field(default="python")
    requested_top_k: int = Field(default=0, ge=0)
    retrieved_count: int = Field(default=0, ge=0)
    relevant_count: int = Field(default=0, ge=0)
    top_score: float = Field(default=0.0)
    mean_score: float = Field(default=0.0)
    score_spread: float = Field(default=0.0)
    query_terms: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerationDiagnostics(BaseModel):
    """Explain which local answer generator ran and whether fallback occurred."""

    requested_mode: str = Field(default="auto")
    actual_mode: str = Field(default="extractive")
    configured_model: str | None = Field(default=None)
    model_used: str | None = Field(default=None)
    local_llm_enabled: bool = Field(default=False)
    fallback_reason: str | None = Field(default=None)


class AnswerExplanation(BaseModel):
    """Human-readable basis for an answer and its confidence."""

    strategy: str = Field(default="no_answer")
    confidence_reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class QuestionAnswer(BaseModel):
    """Grounded answer produced from local document retrieval."""

    answer: str = Field(description="Answer grounded in source snippets.")
    source_snippets: list[SourceSnippet] = Field(default_factory=list)
    confidence: str = Field(description="low, medium, or high.")
    mode: str = Field(description="Answering mode, such as extractive or local_llm.")
    retrieval: RetrievalDiagnostics = Field(default_factory=RetrievalDiagnostics)
    generation: GenerationDiagnostics = Field(default_factory=GenerationDiagnostics)
    explanation: AnswerExplanation = Field(default_factory=AnswerExplanation)


class LocalModelInfo(BaseModel):
    """Installed model reported by the local Ollama runtime."""

    name: str = Field(description="Ollama model name.")
    size_bytes: int | None = Field(default=None, ge=0)
    modified_at: str | None = Field(default=None)


class IntelligenceRuntimeResponse(BaseModel):
    """Local intelligence runtime configuration and availability."""

    local_llm_enabled: bool = Field(description="Whether local LLM use is enabled.")
    ollama_available: bool = Field(description="Whether the configured Ollama runtime responded.")
    configured_model: str = Field(description="Default configured Ollama model.")
    available_models: list[LocalModelInfo] = Field(default_factory=list)
    embedding_provider: str = Field(description="Configured local embedding provider.")
    embedding_model: str | None = Field(default=None)
    vector_backend: str = Field(description="Available vector-search backend.")
    status_message: str = Field(description="Plain-language local runtime status.")


class SessionMetadata(BaseModel):
    """Privacy-preserving metadata for a saved local document session."""

    session_id: str = Field(description="Local session identifier.")
    filename: str = Field(description="Source filename.")
    document_type: str = Field(description="Classified document type.")
    extracted_text_hash: str = Field(description="SHA-256 hash of extracted text.")
    created_at: str = Field(description="UTC creation timestamp.")
    content_stored: bool = Field(
        default=False,
        description="Whether raw extracted text was explicitly retained for this session.",
    )
    text_preview: str | None = Field(
        default=None, description="Always None unless explicitly configured later."
    )


class SavedSession(SessionMetadata):
    """Saved session with structured outputs and Q&A history."""

    insight: DocumentInsight = Field(description="Structured document insight.")
    checklist: ChecklistResult = Field(description="Generated checklist and risk panel.")
    qa_history: list[QuestionAnswer] = Field(default_factory=list)
    extracted_text: str | None = Field(
        default=None,
        description="Raw extracted text when local full-content history is explicitly enabled.",
    )


class SessionCreatedResponse(BaseModel):
    """Response returned after saving a local review session."""

    id: str = Field(description="Created local session identifier.")


class SessionsClearedResponse(BaseModel):
    """Response returned after clearing local review history."""

    deleted: bool = Field(description="Whether the local history clear completed.")


class SaveSessionRequest(BaseModel):
    """Request body for saving a document review session from the frontend."""

    filename: str = Field(description="Source filename.")
    document_type: str = Field(description="Classified document type.")
    extracted_text: str = Field(
        description=(
            "Extracted text used for hashing. It is retained only when "
            "PAPERVAULT_STORE_EXTRACTED_TEXT is explicitly enabled."
        )
    )
    insight: DocumentInsight = Field(description="Full document insight to persist for reload.")
    checklist: ChecklistResult = Field(description="Full checklist to persist for reload.")
