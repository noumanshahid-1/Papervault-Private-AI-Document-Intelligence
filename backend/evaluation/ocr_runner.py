"""Evaluate local OCR extraction and downstream extractive Q&A."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.models.schemas import UploadedDocument
from app.services.embeddings import HashingEmbeddingProvider
from app.services.qa_engine import answer_question
from app.services.text_extractor import extract_text


EVALUATION_ROOT = Path(__file__).resolve().parent
DEFAULT_OCR_DATASET = EVALUATION_ROOT / "ocr_cases.json"


@dataclass(frozen=True)
class OCRQuestion:
    question: str
    expected_answer_contains: tuple[str, ...]


@dataclass(frozen=True)
class OCRCase:
    case_id: str
    profile: str
    document_path: Path
    content_type: str
    expected_text_contains: tuple[str, ...]
    minimum_confidence_score: float
    expected_page_count: int | None
    questions: tuple[OCRQuestion, ...]


@dataclass(frozen=True)
class OCRQuestionResult:
    question: str
    passed: bool
    answer: str


@dataclass(frozen=True)
class OCRCaseResult:
    case_id: str
    profile: str
    passed: bool
    extraction_correct: bool
    ocr_detected: bool
    quality_passed: bool
    qa_accuracy: float
    engine: str
    ocr_engine: str | None
    confidence_score: float
    word_count: int
    warnings: tuple[str, ...]
    question_results: tuple[OCRQuestionResult, ...]


@dataclass(frozen=True)
class OCRReport:
    dataset_version: int
    total_cases: int
    passed_cases: int
    total_questions: int
    extraction_accuracy: float
    ocr_detection_accuracy: float
    quality_pass_rate: float
    downstream_qa_accuracy: float
    results: tuple[OCRCaseResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_ocr_cases(
    dataset_path: Path = DEFAULT_OCR_DATASET,
) -> tuple[int, list[OCRCase]]:
    """Load OCR cases and verify their local fixture paths."""
    resolved_dataset = dataset_path.resolve()
    payload = json.loads(resolved_dataset.read_text(encoding="utf-8"))
    version = int(payload.get("version", 0))
    raw_cases = payload.get("cases")
    if version <= 0 or not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("OCR dataset must contain a version and cases.")

    dataset_root = resolved_dataset.parent.resolve()
    seen_ids: set[str] = set()
    cases: list[OCRCase] = []
    for raw_case in raw_cases:
        case = _parse_case(raw_case, dataset_root)
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate OCR case id: {case.case_id}")
        seen_ids.add(case.case_id)
        cases.append(case)
    return version, cases


def evaluate_ocr_cases(
    dataset_path: Path = DEFAULT_OCR_DATASET,
) -> OCRReport:
    """Measure OCR text recovery, diagnostics, and downstream Q&A."""
    version, cases = load_ocr_cases(dataset_path)
    results = [_evaluate_case(case) for case in cases]
    question_results = [
        question_result
        for result in results
        for question_result in result.question_results
    ]
    return OCRReport(
        dataset_version=version,
        total_cases=len(results),
        passed_cases=sum(result.passed for result in results),
        total_questions=len(question_results),
        extraction_accuracy=_ratio(
            sum(result.extraction_correct for result in results),
            len(results),
        ),
        ocr_detection_accuracy=_ratio(
            sum(result.ocr_detected for result in results),
            len(results),
        ),
        quality_pass_rate=_ratio(
            sum(result.quality_passed for result in results),
            len(results),
        ),
        downstream_qa_accuracy=_ratio(
            sum(result.passed for result in question_results),
            len(question_results),
        ),
        results=tuple(results),
    )


def _parse_case(raw_case: object, dataset_root: Path) -> OCRCase:
    if not isinstance(raw_case, dict):
        raise ValueError("Each OCR case must be an object.")

    case_id = _required_text(raw_case, "id")
    document_path = (dataset_root / _required_text(raw_case, "document")).resolve()
    if not document_path.is_relative_to(dataset_root):
        raise ValueError(f"OCR fixture escapes dataset directory: {case_id}")
    if not document_path.is_file():
        raise ValueError(f"OCR fixture does not exist: {document_path}")

    raw_questions = raw_case.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise ValueError(f"OCR case requires downstream questions: {case_id}")
    questions = tuple(_parse_question(question) for question in raw_questions)
    minimum_confidence = float(raw_case.get("minimum_confidence_score", 0.0))
    if not 0 <= minimum_confidence <= 1:
        raise ValueError(f"Invalid confidence threshold for OCR case: {case_id}")

    expected_page_count = raw_case.get("expected_page_count")
    if expected_page_count is not None:
        expected_page_count = int(expected_page_count)
        if expected_page_count <= 0:
            raise ValueError(f"Invalid page count for OCR case: {case_id}")

    return OCRCase(
        case_id=case_id,
        profile=_required_text(raw_case, "profile"),
        document_path=document_path,
        content_type=_required_text(raw_case, "content_type"),
        expected_text_contains=_text_list(raw_case.get("expected_text_contains")),
        minimum_confidence_score=minimum_confidence,
        expected_page_count=expected_page_count,
        questions=questions,
    )


def _parse_question(raw_question: object) -> OCRQuestion:
    if not isinstance(raw_question, dict):
        raise ValueError("Each OCR question must be an object.")
    return OCRQuestion(
        question=_required_text(raw_question, "question"),
        expected_answer_contains=_text_list(
            raw_question.get("expected_answer_contains")
        ),
    )


def _evaluate_case(case: OCRCase) -> OCRCaseResult:
    content = case.document_path.read_bytes()
    extraction = extract_text(
        UploadedDocument(
            filename=case.document_path.name,
            content=content,
            extension=case.document_path.suffix.lower(),
            content_type=case.content_type,
            size_bytes=len(content),
        )
    )
    extraction_correct = (
        extraction.error is None
        and _contains_all(extraction.text, case.expected_text_contains)
        and (
            case.expected_page_count is None
            or extraction.page_count == case.expected_page_count
        )
    )
    ocr_detected = (
        extraction.diagnostics.is_ocr
        and extraction.diagnostics.ocr_engine is not None
    )
    quality_passed = (
        extraction.diagnostics.confidence_score
        >= case.minimum_confidence_score
    )

    provider = HashingEmbeddingProvider()
    question_results: list[OCRQuestionResult] = []
    for question in case.questions:
        answer = answer_question(
            text=extraction.text,
            question=question.question,
            filename=case.document_path.name,
            embedding_provider=provider,
            use_local_llm=False,
            answer_mode="extractive",
        )
        question_results.append(
            OCRQuestionResult(
                question=question.question,
                passed=_contains_all(
                    answer.answer,
                    question.expected_answer_contains,
                ),
                answer=answer.answer,
            )
        )

    qa_accuracy = _ratio(
        sum(result.passed for result in question_results),
        len(question_results),
    )
    passed = extraction_correct and ocr_detected and quality_passed and qa_accuracy == 1
    return OCRCaseResult(
        case_id=case.case_id,
        profile=case.profile,
        passed=passed,
        extraction_correct=extraction_correct,
        ocr_detected=ocr_detected,
        quality_passed=quality_passed,
        qa_accuracy=qa_accuracy,
        engine=extraction.diagnostics.engine,
        ocr_engine=extraction.diagnostics.ocr_engine,
        confidence_score=extraction.diagnostics.confidence_score,
        word_count=extraction.diagnostics.word_count,
        warnings=tuple(extraction.warnings),
        question_results=tuple(question_results),
    )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"OCR case field '{key}' must be non-empty text.")
    return value.strip()


def _text_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("OCR expectation fields must be non-empty lists.")
    values = tuple(
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    )
    if len(values) != len(value):
        raise ValueError("OCR expectations must contain non-empty text.")
    return values


def _contains_all(text: str, expected: tuple[str, ...]) -> bool:
    compact_text = re.sub(r"[^a-z0-9]+", "", text.lower())
    return all(
        re.sub(r"[^a-z0-9]+", "", value.lower()) in compact_text
        for value in expected
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)
