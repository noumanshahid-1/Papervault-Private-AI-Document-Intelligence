"""Tests for Markdown and JSON report exports."""

import json

from app.services.checklist_engine import generate_checklist
from app.services.insight_engine import analyze_document
from app.services.qa_engine import answer_question
from app.services.report_exporter import build_json_report, build_markdown_report


SAMPLE_TEXT = """
Scholarship Award Notice
Submit the signed award acceptance form by August 1, 2026.
Required documents include bank details and proof of enrollment.
Missing bank details may delay payment.
Contact scholarships@example.org for support.
"""

NOTICE_TEXT = """
GOVERNMENT GAZETTE KHYBER PAKHTUNKHWA
KHYBER PAKHTUNKHWA REVENUE AUTHORITY NOTIFICATION
Peshawar Dated,the 16 June, 2025.
No. KPRA/ADMN/GN/2025/3337.
Custom House Agents 9806.3000 Pakistan Single Window Fixed rate of Rs. 3.000/-per goods declaration.
The person made liable to pay tax shall ensure timely collection and payment of sales tax on services
not later than the 15 day of the following tax period.
"""


def test_markdown_report_contains_required_sections() -> None:
    insight = analyze_document(SAMPLE_TEXT, filename="scholarship.txt")
    checklist = generate_checklist(insight)
    qa_history = [
        answer_question(
            text=SAMPLE_TEXT,
            question="Which documents are required?",
            filename="scholarship.txt",
        )
    ]

    report = build_markdown_report(
        filename="scholarship.txt",
        insight=insight,
        checklist=checklist,
        qa_history=qa_history,
    )

    assert "# DocuSense AI Report" in report
    assert "## Deadlines" in report
    assert "## Requirements" in report
    assert "## Risks" in report
    assert "## Action Checklist" in report
    assert "## Q&A History" in report
    assert "not professional advice" in report.lower()


def test_json_report_is_parseable_and_structured() -> None:
    insight = analyze_document(SAMPLE_TEXT, filename="scholarship.txt")
    checklist = generate_checklist(insight)

    report = build_json_report(
        filename="scholarship.txt",
        insight=insight,
        checklist=checklist,
        qa_history=[],
    )
    payload = json.loads(report)

    assert payload["filename"] == "scholarship.txt"
    assert payload["document_type"] == "scholarship document"
    assert payload["insight"]["classification"]["document_type"] == "scholarship document"
    assert payload["checklist"]["items"]
    assert "limitations" in payload


def test_markdown_report_includes_official_notice_breakdown() -> None:
    insight = analyze_document(NOTICE_TEXT, filename="notice.txt")
    checklist = generate_checklist(insight)

    report = build_markdown_report(
        filename="notice.txt",
        insight=insight,
        checklist=checklist,
        qa_history=[],
    )

    assert "## Official Notice Breakdown" in report
    assert "Notice number: KPRA/ADMN/GN/2025/3337" in report
    assert "Service: Custom House Agents" in report
    assert "Rate/amount: Rs. 3,000/- per goods declaration" in report
