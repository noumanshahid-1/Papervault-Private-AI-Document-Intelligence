"""Regression coverage for image and scanned-PDF OCR evaluation."""

from evaluation.ocr_runner import (
    DEFAULT_OCR_DATASET,
    evaluate_ocr_cases,
    load_ocr_cases,
)


def test_ocr_evaluation_dataset_is_complete_and_valid() -> None:
    version, cases = load_ocr_cases(DEFAULT_OCR_DATASET)

    assert version == 1
    assert {case.document_path.suffix for case in cases} == {".png", ".pdf"}
    assert all(case.document_path.is_file() for case in cases)
    assert sum(len(case.questions) for case in cases) >= 4


def test_ocr_evaluation_meets_baseline() -> None:
    report = evaluate_ocr_cases()

    assert report.extraction_accuracy == 1.0
    assert report.ocr_detection_accuracy == 1.0
    assert report.quality_pass_rate == 1.0
    assert report.downstream_qa_accuracy == 1.0
    assert report.passed_cases == report.total_cases
