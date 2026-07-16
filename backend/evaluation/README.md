# Local Q&A Evaluation Pack

This pack measures retrieval and extractive question-answering behavior against
small, privacy-safe documents that represent common Papervault use cases.

The documents are fictional and contain no personal or confidential data.

## Coverage

- Date and deadline disambiguation
- Required-document questions
- Fees and total-amount selection
- Obligations and retention periods
- Contact details
- Negative questions where the answer is absent

## Run

From `backend/`:

```bash
npm run evaluate
```

Run individual scorecards:

```bash
npm run evaluate:qa
npm run evaluate:ocr
```

Machine-readable output:

```bash
python scripts/evaluate_qa.py --json
python scripts/evaluate_ocr.py --json
```

The Q&A evaluator uses deterministic hashing embeddings and extractive-only
mode. The OCR evaluator processes five files across baseline image, baseline
scanned PDF, rotated image, low-contrast image, and multi-page scanned PDF
profiles, then asks grounded questions against the recovered text.
