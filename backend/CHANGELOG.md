# Changelog

## 2026-07-17 - Explainable local intelligence

- Added deterministic extraction-quality diagnostics with confidence scores,
  readable-character ratios, PDF text coverage, and OCR confidence feedback.
- Added configurable local embedding provider/model settings with cached-only
  sentence-transformer loading and hashing fallback.
- Added retrieval diagnostics for provider, vector backend, relevance scores,
  matched terms, and threshold warnings.
- Strengthened extractive Q&A with dependency-free hybrid vector, lexical, and
  intent ranking plus targeted handling for start dates, deadlines, required
  documents, payments, obligations, and contact details.
- Added a deterministic 17-case evaluation pack covering retrieval hit rate,
  answer accuracy, evidence grounding, and absent-answer false positives.
- Improved obligation routing, total-amount selection, and missing-detail
  rejection based on evaluation failures.
- Added local answer-mode and Ollama model selection with explicit fallback
  diagnostics.
- Added `/intelligence/runtime` for bounded Ollama model discovery and local
  provider status.
- Added explainable analysis confidence and Q&A confidence reasons.

## 2026-07-16 - Canonical API contracts

- Added explicit response models for session creation and history clearing.
- Added reproducible OpenAPI export and contract-freshness checks.
- Added OpenAPI coverage for official-notice and saved-session structures.
- Extended privacy redaction to official-notice table source snippets.

## 2026-07-16 - Privacy and validation foundation

- Routed session endpoints through the privacy-preserving SQLite repository.
- Made saved history summary-only by default, with explicit opt-in full-text retention.
- Added legacy-session sanitization for raw text and source snippets.
- Added session API coverage and restored full backend test collection.
- Removed obsolete Streamlit tests and dependencies.
- Replaced the invalid `httpx2` requirement with `httpx`.
- Updated backend documentation for the React/BFF architecture.

## 2026-06-11 - Visual hierarchy polish

- Upgraded the review metrics with semantic color accents for findings, actions, risks, and evidence.
- Reworked the workspace tabs into a clearer segmented navigation control with hover and keyboard focus states.
- Added category labels, counts, and restrained color coding to the overview finding groups.
- Flattened nested finding rows to reduce the empty white-card appearance while preserving scanability.

All notable changes to DocuSense AI will be documented in this file.

## 0.1.0 - Phase 0

- Initialized the local-first DocuSense AI repository structure.
- Added FastAPI backend package, Streamlit UI package, service boundaries, storage boundary, and utility package.
- Added open-source/local dependency manifest.
- Added `.gitignore`, `.env.example`, README, sample document guidance, and AGENTS.md.
- Added pytest smoke tests for core module imports and FastAPI app metadata.
- Added `pytest.ini` so the standalone `pytest` command resolves local packages reliably.

## 0.2.0 - Phase 1

- Added in-memory document upload validation for PDF, image, TXT, Markdown, and DOCX files.
- Added local text extraction for TXT/Markdown, PDF, DOCX, and image OCR with graceful missing-OCR fallback.
- Added structured Pydantic extraction schemas that keep extracted text separate from interpretation.
- Added `POST /documents/extract` for text extraction without permanently storing uploaded originals.
- Added text cleaning utilities and Phase 1 pytest coverage, including a programmatically generated PDF fixture.
- Added the `httpx` test-client dependency required by FastAPI/Starlette tests.

## 0.3.0 - Phase 2

- Added deterministic classification for admission, scholarship, visa/immigration, government form, contract/agreement, resume/CV, job description, medical/lab report, and unknown documents.
- Added structured insight extraction for likely title, summary, important dates, fees/amounts, required documents, action items, risks, missing information, contacts, and confidence.
- Added careful risk language and responsible-use limitations for high-stakes document categories.
- Added `POST /documents/analyze` for analyzing already-extracted document text.
- Added pytest coverage for admission letter, scholarship document, contract/agreement, unknown document, and analyze endpoint behavior.

## 0.4.0 - Phase 3

- Added checklist generation from deadlines, required documents, action items, fees/amounts, missing information, and warnings.
- Added checklist item metadata: title, reason, priority, due date, source snippet, and pending status.
- Added a separate risk panel with possible issue, why it matters, suggested verification step, confidence level, and source snippet.
- Added `POST /documents/checklist` for generating checklist and risk output from extracted text.
- Added pytest coverage for checklist generation, priority assignment, unknown-document handling, risk wording, and endpoint behavior.

## 0.5.0 - Phase 4

- Added document chunking with chunk ids, page numbers, character ranges, and source filenames.
- Added deterministic local hashing embeddings plus an optional sentence-transformers provider for local open-source models.
- Added local vector retrieval with FAISS support when available and cosine-search fallback when FAISS is unavailable.
- Added extractive document Q&A with source snippets, confidence level, and `Not found in the document.` behavior.
- Added `POST /documents/ask` for local RAG question answering over provided extracted text.
- Added pytest coverage for chunking, vector indexing, retrieval, no-answer behavior, extractive fallback, and endpoint behavior.

## 0.6.0 - Phase 5

- Added an optional Ollama-compatible local LLM adapter using local HTTP only.
- Added local LLM configuration support through existing `LOCAL_LLM_*` settings.
- Added strict prompt templates for summary, document explanation, context-only Q&A, and risk explanation.
- Integrated optional local LLM Q&A with extractive fallback when disabled, unavailable, timed out, invalid, or empty.
- Kept extractive Q&A as the default so the app remains functional without Ollama.
- Added mocked tests for local LLM success, disabled state, connection failure fallback, prompt grounding rules, and Q&A integration.

## 0.7.0 - Phase 6

- Replaced the placeholder Streamlit screen with a professional document workspace.
- Added upload processing, sample text mode, processing status, extracted text preview, insight cards, checklist view, risk panel, Q&A panel, source evidence, and Markdown export.
- Wired the UI directly to local service functions without adding backend cloud dependencies.
- Added UI helper tests for workspace generation, grounded Q&A, and Markdown report output.
- Smoke-checked the Streamlit app locally on `http://localhost:8501`.

## 0.8.0 - Phase 7

- Added SQLite initialization and local session persistence.
- Saved session metadata, extracted text hash, structured insights, checklist, and Q&A history without storing original uploads or raw extracted text.
- Added source-snippet redaction before writing session data to SQLite.
- Added reusable Markdown and JSON report exporters.
- Added JSON report download and local session history sidebar to the Streamlit app.
- Added pytest coverage for database initialization, save/load behavior, recent session metadata, Markdown export, and JSON export.

## 0.9.0 - Phase 8

- Performed final QA, security, and GitHub-readiness review.
- Reworked README into a presentation-ready project guide with architecture diagram, local-only commitment, troubleshooting, limitations, future improvements, and screenshot placeholders.
- Added screenshot placeholder guidance under `docs/screenshots/`.
- Added repository readiness tests for prohibited hosted AI SDKs, ignored private/runtime files, and required README sections.
- Fixed an encoding artifact in amount extraction and kept currency extraction ASCII-safe.
- Verified dependency consistency, backend routes, Streamlit runtime, compile checks, and the full pytest suite.

## Unreleased - OCR Repair And UI Polish

- Consolidated duplicate and legacy Streamlit render paths into one maintainable analyst workspace.
- Added a reference-informed product shell with persistent review navigation, guided intake, upload queue feedback, responsive review tabs, and local-processing status.
- Added review completion tracking, finding/action/risk/evidence metrics, filterable risk prompts, priority filtering, and a more usable interactive action register.
- Promoted source verification and Markdown/JSON exports into a dedicated evidence workspace.
- Improved Q&A with suggested review questions, chat history, answer mode/confidence labels, and source snippet expansion.
- Improved extractive deadline answers so general deadline questions prefer explicit dated sentences and prioritize matching evidence chunks.
- Added focused tests for review metrics, evidence collection, and deadline-answer grounding; full suite passes with 66 tests.
- Browser-QA checked the intake, sample review, checklist completion, grounded Q&A, evidence/export, and 390px responsive layouts without horizontal overflow.

- Diagnosed image upload failure with `notification-regarding-collection-agents-2025.jpg`; root cause was missing local Tesseract OCR.
- Added RapidOCR as a local Python OCR fallback so image documents can be processed without a separate OCR system binary.
- Improved Streamlit upload/status/empty states with clearer extraction guidance, a light professional theme, and less duplicate warning noise.
- Added tests for OCR fallback behavior and user-facing OCR setup guidance.
- Improved OCR artifact cleanup for scanned official notices, including broken dates, authority names, and rupee rate formatting.
- Added stronger government-notice extraction for summaries, timing rules, financial terms, obligations, and risk language.
- Reworked the Streamlit results workspace into source preview, overview, obligations, dates and money, risks, checklist, Q&A, evidence, and export sections.
- Verified the uploaded `notification-regarding-collection-agents-2025.jpg` image through the Streamlit upload path.
- Improved extractive Q&A for common review questions about document purpose, obligations, required documents, and payment/rate language.
- QA-checked tab content, Q&A, checklist controls, export preview, local session saving, and browser/server logs.
- Added a dedicated official notice engine for gazette notifications, recovering notice metadata, legal basis, table rows, liable party, rates, compliance duties, and consequences.
- Added a `Notice Breakdown` UI tab and report export section for detected official notices.
- Rebuilt the Streamlit shell into a polished document workspace with a stronger header, session vault, intake/status panels, review map, summary treatment, notice table, risk cards, priority checklist styling, and responsive empty states.
- Verified the transformed UI with pytest, compile checks, Streamlit AppTest sample flow, and the exact `notification-regarding-collection-agents-2025.jpg` upload path.
- Upgraded the UI again with a modern pipeline bar, finished-app chrome treatment, capsule tabs, refined button/input styling, richer header chips, and designed runtime notices.
- Reframed successful RapidOCR fallback as a positive local OCR status instead of an alarming warning while preserving the underlying extraction warning for tests and reports.
- Refactored the Streamlit app into a compliance-review desk layout with a left-side upload and metadata column plus a right-side `[Findings | Risks | Checklist | Q&A]` tab panel.
- Added IBM Plex typography, paper-toned background, white bordered review panels, deep navy accents, traffic-light risk chips, interactive checkbox task styling, sidebar mode/settings controls, and chat-style Q&A bubbles.
- Fixed blank white Streamlit panels caused by standalone HTML section wrappers around widgets; mixed widget sections now use native Streamlit containers styled as review cards.
- Improved VS Code terminal run reliability by documenting `python -m streamlit` / `python -m uvicorn`, adding Windows UTF-8 terminal guidance, and making the Streamlit entry point robust to working-directory import issues.
- Tightened deterministic classification to avoid over-labeling academic documents as government, admission, resume, or medical documents due to broad substring matches.
- Added regression coverage for academic thesis-format text and scholarship assessment instructions, plus instruction-style action extraction for checklist generation.
