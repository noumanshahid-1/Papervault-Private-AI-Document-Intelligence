"""Command-line scorecard for local retrieval and extractive Q&A."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from evaluation.runner import DEFAULT_DATASET, EvaluationReport, evaluate_cases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic Papervault retrieval and Q&A.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to an evaluation cases JSON file.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete report as JSON.",
    )
    parser.add_argument("--min-answer-accuracy", type=float, default=0.9)
    parser.add_argument("--min-retrieval-hit-at-k", type=float, default=0.9)
    parser.add_argument("--min-grounding-accuracy", type=float, default=0.9)
    parser.add_argument("--min-negative-accuracy", type=float, default=1.0)
    args = parser.parse_args()

    report = evaluate_cases(args.dataset, top_k=args.top_k)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_scorecard(report, top_k=args.top_k)

    thresholds_met = (
        report.answer_accuracy >= args.min_answer_accuracy
        and report.retrieval_hit_at_k >= args.min_retrieval_hit_at_k
        and report.grounding_accuracy >= args.min_grounding_accuracy
        and report.negative_case_accuracy >= args.min_negative_accuracy
    )
    return 0 if thresholds_met else 1


def _print_scorecard(report: EvaluationReport, *, top_k: int) -> None:
    print("Papervault local Q&A evaluation")
    print(
        f"Dataset v{report.dataset_version}: {report.total_cases} cases "
        f"({report.positive_cases} answerable, {report.negative_cases} negative)"
    )
    print()
    print(f"Answer accuracy:       {_percent(report.answer_accuracy)}")
    print(f"Retrieval hit@1:       {_percent(report.retrieval_hit_at_1)}")
    print(f"Retrieval hit@{top_k}:       {_percent(report.retrieval_hit_at_k)}")
    print(f"Grounded source rate:  {_percent(report.grounding_accuracy)}")
    print(f"Negative-case accuracy:{_percent(report.negative_case_accuracy):>8}")
    print(f"Fully passed cases:    {report.passed_cases}/{report.total_cases}")
    print()
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status:4}  {result.case_id:38} "
            f"confidence={result.confidence:6} score={result.top_score:.3f}"
        )
        if not result.passed:
            print(f"      answer: {result.answer}")


def _percent(value: float) -> str:
    return f"{value * 100:6.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
