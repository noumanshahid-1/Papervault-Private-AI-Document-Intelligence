"""FastAPI application entry point for Papervault."""

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import get_settings
from app.models.schemas import (
    AnalyzeRequest,
    AskRequest,
    ChecklistResult,
    DocumentInsight,
    ExtractionResult,
    HealthResponse,
    IntelligenceRuntimeResponse,
    QuestionAnswer,
    SavedSession,
    SaveSessionRequest,
    SessionCreatedResponse,
    SessionMetadata,
    SessionsClearedResponse,
)
from app.services.document_loader import DocumentLoaderError, load_document
from app.services.checklist_engine import generate_checklist
from app.services.insight_engine import analyze_document
from app.services.intelligence_runtime import get_intelligence_runtime
from app.services.qa_engine import answer_question
from app.services.text_extractor import extract_text
from app.storage.database import DocuSenseDatabase

settings = get_settings()
_db = DocuSenseDatabase()

app = FastAPI(
    title=settings.app_name,
    description="Local-first document intelligence assistant.",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a minimal health response for smoke checks."""
    return HealthResponse(status="ok", app=settings.app_name)


@app.get("/intelligence/runtime", response_model=IntelligenceRuntimeResponse)
def intelligence_runtime() -> IntelligenceRuntimeResponse:
    """Return configured local model, embedding, and vector runtime diagnostics."""
    return get_intelligence_runtime()


@app.post("/documents/extract", response_model=ExtractionResult)
async def extract_document(file: UploadFile = File(...)) -> ExtractionResult:
    """Extract text from an uploaded document without storing the original file."""
    content = await file.read()
    try:
        document = load_document(
            filename=file.filename or "uploaded-document",
            content=content,
            content_type=file.content_type,
        )
    except DocumentLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return extract_text(document)


@app.post("/documents/analyze", response_model=DocumentInsight)
def analyze_extracted_document(request: AnalyzeRequest) -> DocumentInsight:
    """Analyze already-extracted text and return grounded structured insights."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="No document text was provided.")
    return analyze_document(request.text, filename=request.filename)


@app.post("/documents/checklist", response_model=ChecklistResult)
def create_document_checklist(request: AnalyzeRequest) -> ChecklistResult:
    """Generate an action checklist and risk panel from extracted document text."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="No document text was provided.")
    insight = analyze_document(request.text, filename=request.filename)
    return generate_checklist(insight)


@app.post("/documents/ask", response_model=QuestionAnswer)
def ask_document(request: AskRequest) -> QuestionAnswer:
    """Answer a question using local retrieval over provided document text."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="No document text was provided.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="No question was provided.")
    return answer_question(
        text=request.text,
        question=request.question,
        filename=request.filename,
        top_k=request.top_k,
        answer_mode=request.answer_mode,
        model=request.model,
    )


@app.post("/sessions", response_model=SessionCreatedResponse)
def create_session(request: SaveSessionRequest) -> SessionCreatedResponse:
    """Save privacy-preserving local session history."""
    session_id = _db.save_session(
        filename=request.filename,
        extracted_text=request.extracted_text,
        insight=request.insight,
        checklist=request.checklist,
    )
    return SessionCreatedResponse(id=session_id)


@app.get("/sessions", response_model=list[SessionMetadata])
def get_sessions() -> list[SessionMetadata]:
    """Return recent session metadata for the history page."""
    return _db.list_sessions()


@app.delete("/sessions", response_model=SessionsClearedResponse)
def clear_sessions() -> SessionsClearedResponse:
    """Delete every saved session and its Q&A history. Local-only, no recovery."""
    _db.clear_sessions()
    return SessionsClearedResponse(deleted=True)


@app.get("/sessions/{session_id}", response_model=SavedSession)
def get_session(session_id: str) -> SavedSession:
    """Return saved structured results and optional explicitly retained text."""
    session = _db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session
