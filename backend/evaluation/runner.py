"""Run privacy-safe retrieval and extractive Q&A evaluations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.services.chunker import chunk_text
from app.services.embeddings import HashingEmbeddingProvider
from app.services.qa_engine import NOT_FOUND_MESSAGE, answer_question
from app.services.vector_store import LocalVectorStore


EVALUATION_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = EVALUATION_ROOT / "cases.json"
EVALUATION_CHUNK_SIZE = 360
EVALUATION_CHUNK_OVERLAP = 60


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: str
    document_path: Path
    question: str
    expected_answer_contains: tuple[str, ...]
    expected_evidence_contains: tuple[str, ...]
    expect_not_found: bool


@dataclass(frozen=True)
class EvaluationCaseResult:
    case_id: str
    category: str
    passed: bool
    answer_correct: bool
    retrieval_hit_at_1: bool | None
    retrieval_hit_at_k: bool | None
    grounded_source: bool | None
    answer: str
    confidence: str
    top_score: float


@dataclass(frozen=True)
class EvaluationReport:
    dataset_version: int
    total_cases: int
    positive_cases: int
    negative_cases: int
    passed_cases: int
    answer_accuracy: float
    retrieval_hit_at_1: float
    retrieval_hit_at_k: float
    grounding_accuracy: float
    negative_case_accuracy: float
    results: tuple[EvaluationCaseResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_evaluation_cases(
    dataset_path: Path = DEFAULT_DATASET,
) -> tuple[int, list[EvaluationCase]]:
    """Load and validate evaluation cases from JSON."""
    resolved_dataset = dataset_path.resolve()
    payload = json.loads(resolved_dataset.read_text(encoding="utf-8"))
    version = int(payload.get("version", 0))
    raw_cases = payload.get("cases")
    if version <= 0 or not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Evaluation dataset must contain a version and cases.")

    dataset_root = resolved_dataset.parent
    seen_ids: set[str] = set()
    cases: list[EvaluationCase] = []
    for raw_case in raw_cases:
        case = _parse_case(raw_case, dataset_root)
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case.case_id}")
        seen_ids.add(case.case_id)
        cases.append(case)
    return version, cases


def evaluate_cases(
    dataset_path: Path = DEFAULT_DATASET,
    *,
    top_k: int = 3,
) -> EvaluationReport:
    """Evaluate retrieval ranking, answer correctness, and source grounding."""
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    version, cases = load_evaluation_cases(dataset_path)
    provider = HashingEmbeddingProvider()
    results = [
        _evaluate_case(case, provider=provider, top_k=top_k)
        for case in cases
    ]
    positive = [result for result in results if result.retrieval_hit_at_k is not None]
    negative = [result for result in results if result.retrieval_hit_at_k is None]

    return EvaluationReport(
        dataset_version=version,
        total_cases=len(results),
        positive_cases=len(positive),
        negative_cases=len(negative),
        passed_cases=sum(result.passed for result in results),
        answer_accuracy=_ratio(
            sum(result.answer_correct for result in results),
            len(results),
        ),
        retrieval_hit_at_1=_ratio(
            sum(result.retrieval_hit_at_1 is True for result in positive),
            len(positive),
        ),
        retrieval_hit_at_k=_ratio(
            sum(result.retrieval_hit_at_k is True for result in positive),
            len(positive),
        ),
        grounding_accuracy=_ratio(
            sum(result.grounded_source is True for result in positive),
            len(positive),
        ),
        negative_case_accuracy=_ratio(
            sum(result.answer_correct for result in negative),
            len(negative),
        ),
        results=tuple(results),
    )


def _parse_case(raw_case: object, dataset_root: Path) -> EvaluationCase:
    if not isinstance(raw_case, dict):
        raise ValueError("Each evaluation case must be an object.")

    case_id = _required_text(raw_case, "id")
    category = _required_text(raw_case, "category")
    question = _required_text(raw_case, "question")
    document_value = _required_text(raw_case, "document")
    document_path = (dataset_root / document_value).resolve()
    if not document_path.is_relative_to(dataset_root.resolve()):
        raise ValueError(f"Evaluation document escapes dataset directory: {case_id}")
    if not document_path.is_file():
        raise ValueError(f"Evaluation document does not exist: {document_path}")

    expect_not_found = bool(raw_case.get("expect_not_found", False))
    expected_answer = _text_list(raw_case.get("expected_answer_contains", []))
    expected_evidence = _text_list(raw_case.get("expected_evidence_contains", []))
    if expect_not_found:
        if expected_answer or expected_evidence:
            raise ValueError(
                f"Negative evaluation case cannot define expected evidence: {case_id}"
            )
    elif not expected_answer or not expected_evidence:
        raise ValueError(
            f"Positive evaluation case needs answer and evidence expectations: {case_id}"
        )

    return EvaluationCase(
        case_id=case_id,
        category=category,
        document_path=document_path,
        question=question,
        expected_answer_contains=expected_answer,
        expected_evidence_contains=expected_evidence,
        expect_not_found=expect_not_found,
    )


def _evaluate_case(
    case: EvaluationCase,
    *,
    provider: HashingEmbeddingProvider,
    top_k: int,
) -> EvaluationCaseResult:
    text = case.document_path.read_text(encoding="utf-8")
    chunks = chunk_text(
        text,
        filename=case.document_path.name,
        chunk_size=EVALUATION_CHUNK_SIZE,
        chunk_overlap=EVALUATION_CHUNK_OVERLAP,
    )
    store = LocalVectorStore(embedding_provider=provider)
    store.add_chunks(chunks)
    retrieved = store.search(case.question, top_k=top_k)

    answer = answer_question(
        text=text,
        question=case.question,
        filename=case.document_path.name,
        top_k=top_k,
        embedding_provider=provider,
        use_local_llm=False,
        answer_mode="extractive",
    )

    if case.expect_not_found:
        answer_correct = answer.answer == NOT_FOUND_MESSAGE
        return EvaluationCaseResult(
            case_id=case.case_id,
            category=case.category,
            passed=answer_correct and not answer.source_snippets,
            answer_correct=answer_correct,
            retrieval_hit_at_1=None,
            retrieval_hit_at_k=None,
            grounded_source=None,
            answer=answer.answer,
            confidence=answer.confidence,
            top_score=answer.retrieval.top_score if answer.retrieval else 0.0,
        )

    answer_correct = _contains_all(answer.answer, case.expected_answer_contains)
    first_chunk = retrieved[0].chunk.text if retrieved else ""
    retrieved_text = " ".join(result.chunk.text for result in retrieved)
    retrieval_hit_at_1 = _contains_all(
        first_chunk,
        case.expected_evidence_contains,
    )
    retrieval_hit_at_k = _contains_all(
        retrieved_text,
        case.expected_evidence_contains,
    )
    source_text = " ".join(snippet.text for snippet in answer.source_snippets)
    grounded_source = _contains_all(
        source_text,
        case.expected_evidence_contains,
    )
    passed = (
        answer_correct
        and retrieval_hit_at_k
        and grounded_source
    )
    return EvaluationCaseResult(
        case_id=case.case_id,
        category=case.category,
        passed=passed,
        answer_correct=answer_correct,
        retrieval_hit_at_1=retrieval_hit_at_1,
        retrieval_hit_at_k=retrieval_hit_at_k,
        grounded_source=grounded_source,
        answer=answer.answer,
        confidence=answer.confidence,
        top_score=answer.retrieval.top_score if answer.retrieval else 0.0,
    )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Evaluation case field '{key}' must be non-empty text.")
    return value.strip()


def _text_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("Evaluation expectation fields must be lists.")
    values = tuple(
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    )
    if len(values) != len(value):
        raise ValueError("Evaluation expectations must contain non-empty text.")
    return values


def _contains_all(text: str, expected: tuple[str, ...]) -> bool:
    normalized = " ".join(text.lower().split())
    return all(" ".join(value.lower().split()) in normalized for value in expected)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)
