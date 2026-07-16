"""Command-line scorecard for image and scanned-PDF OCR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.ocr_runner import (
    DEFAULT_OCR_DATASET,
    OCRReport,
    evaluate_ocr_cases,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate local image and scanned-PDF OCR.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_OCR_DATASET,
        help="Path to an OCR evaluation cases JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete report as JSON.",
    )
    args = parser.parse_args()

    report = evaluate_ocr_cases(args.dataset)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_scorecard(report)
    return 0 if report.passed_cases == report.total_cases else 1


def _print_scorecard(report: OCRReport) -> None:
    print("Papervault local OCR evaluation")
    print(
        f"Dataset v{report.dataset_version}: {report.total_cases} files, "
        f"{report.total_questions} downstream questions"
    )
    print()
    print(f"Extraction accuracy:      {_percent(report.extraction_accuracy)}")
    print(f"OCR detection accuracy:   {_percent(report.ocr_detection_accuracy)}")
    print(f"Quality threshold pass:   {_percent(report.quality_pass_rate)}")
    print(f"Downstream Q&A accuracy:  {_percent(report.downstream_qa_accuracy)}")
    print(f"Fully passed files:       {report.passed_cases}/{report.total_cases}")
    print()
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status:4}  {result.case_id:34} engine={result.engine:18} "
            f"quality={result.confidence_score:.3f}"
        )
        if not result.passed:
            for question in result.question_results:
                if not question.passed:
                    print(f"      question: {question.question}")
                    print(f"      answer: {question.answer}")


def _percent(value: float) -> str:
    return f"{value * 100:6.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
