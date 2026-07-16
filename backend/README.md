# Papervault Backend

Papervault's FastAPI backend provides local document extraction, deterministic
analysis, checklist generation, grounded retrieval, optional Ollama-assisted
Q&A, privacy-preserving session history, and report generation.

No paid or hosted AI API is required.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the API from this directory:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Run validation:

```powershell
python -m pytest
python -m compileall app tests
```

Run the deterministic retrieval and Q&A evaluation:

```powershell
python scripts/evaluate_qa.py
```

The evaluation pack contains fictional admission, government notice, contract,
invoice, and appointment documents. It reports answer accuracy, retrieval
hit@1, retrieval hit@3, evidence-grounding rate, and negative-case accuracy.

Export the canonical OpenAPI document used by the frontend:

```powershell
python scripts/export_openapi.py ../frontend/src/lib/openapi.json
```

Verify that the committed contract is current:

```powershell
python scripts/export_openapi.py ../frontend/src/lib/openapi.json --check
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Local health check |
| GET | `/intelligence/runtime` | Local Ollama, embedding, and vector runtime status |
| POST | `/documents/extract` | Validate and extract an uploaded document |
| POST | `/documents/analyze` | Produce structured document insights |
| POST | `/documents/checklist` | Build an actionable checklist |
| POST | `/documents/ask` | Answer a grounded document question |
| POST | `/sessions` | Save privacy-preserving review history |
| GET | `/sessions` | List saved review metadata |
| GET | `/sessions/{id}` | Load redacted results and optional retained text |
| DELETE | `/sessions` | Clear local review history |

## Privacy

Uploaded originals are processed in memory. Session history stores a SHA-256 text
hash plus structured insights and checklists with source snippets removed by
default. It does not retain raw extracted text.

Structured findings can still contain sensitive derived facts such as names,
dates, obligations, and amounts. Clear history when those results are no longer
needed.

Full-content history is an explicit local opt-in:

```text
PAPERVAULT_STORE_EXTRACTED_TEXT=true
```

When this setting is disabled, existing locally stored text is removed during
database initialization. Summary-only sessions can restore findings and
checklists, but the user must re-upload the document for new Q&A or evidence
inspection.

## Optional local model

Ollama support is disabled by default. Configure it in `.env`:

```text
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3.2
LOCAL_LLM_TIMEOUT=30
LOCAL_LLM_DISCOVERY_TIMEOUT=2
```

The runtime endpoint discovers installed Ollama models with a short bounded
timeout. The Q&A request can select `auto`, `extractive`, or `local_llm` mode
and may provide an installed model name. If Ollama is unavailable, disabled,
or returns an unusable response, Papervault reports the fallback reason and
uses extractive local Q&A.

## Retrieval and quality diagnostics

```text
LOCAL_EMBEDDING_PROVIDER=hashing
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOCAL_RETRIEVAL_MIN_SCORE=0.08
```

The sentence-transformer provider loads cached local files only and falls back
to deterministic hashing. Q&A responses report the effective embedding
provider, model, vector backend, retrieved/relevant chunk counts, similarity
scores, matched terms, generation mode, confidence reasons, and limitations.

Extraction responses include the effective engine, normalized confidence score,
readable/suspicious character ratios, PDF page-text coverage, and OCR engine
confidence when available. Low-quality scans receive actionable local
rescan/verification guidance.

## Data location

SQLite defaults to:

```text
.docsense_data/docsense.sqlite3
```

The legacy directory name remains for compatibility and is ignored by Git.
