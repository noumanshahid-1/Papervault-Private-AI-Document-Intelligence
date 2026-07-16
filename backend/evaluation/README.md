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
python scripts/evaluate_qa.py
```

Machine-readable output:

```bash
python scripts/evaluate_qa.py --json
```

The evaluator uses deterministic hashing embeddings and extractive-only mode,
so results do not depend on downloaded models or a running local model service.
