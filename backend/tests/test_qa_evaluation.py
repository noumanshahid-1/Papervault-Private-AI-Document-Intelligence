"""Regression coverage for the local retrieval and Q&A evaluation pack."""

from evaluation.runner import DEFAULT_DATASET, evaluate_cases, load_evaluation_cases


def test_evaluation_dataset_is_complete_and_valid() -> None:
    version, cases = load_evaluation_cases(DEFAULT_DATASET)

    assert version == 1
    assert len(cases) >= 15
    assert len({case.case_id for case in cases}) == len(cases)
    assert sum(case.expect_not_found for case in cases) >= 3
    assert all(case.document_path.is_file() for case in cases)


def test_local_qa_evaluation_meets_baseline() -> None:
    report = evaluate_cases()

    assert report.answer_accuracy == 1.0
    assert report.retrieval_hit_at_1 == 1.0
    assert report.retrieval_hit_at_k == 1.0
    assert report.grounding_accuracy == 1.0
    assert report.negative_case_accuracy == 1.0
    assert report.passed_cases == report.total_cases
