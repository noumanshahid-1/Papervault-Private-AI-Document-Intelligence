"""Markdown and JSON report export helpers."""

import json
from typing import Any

from app.models.schemas import ChecklistResult, DocumentInsight, QuestionAnswer


DISCLAIMER = (
    "DocuSense AI helps inspect documents, but this report is not professional "
    "advice. Verify high-stakes decisions with official sources or qualified "
    "professionals."
)


def build_markdown_report(
    *,
    filename: str,
    insight: DocumentInsight,
    checklist: ChecklistResult,
    qa_history: list[QuestionAnswer] | None = None,
) -> str:
    """Build a Markdown report from structured local outputs."""
    qa_history = qa_history or []
    lines = [
        "# DocuSense AI Report",
        "",
        f"Source: {filename}",
        "",
        DISCLAIMER,
        "",
        "## Key Findings",
        "",
        f"- Likely document type: {insight.classification.document_type}",
        f"- Confidence: {insight.confidence}",
        f"- Summary: {insight.summary}",
        "",
    ]
    if insight.official_notice:
        lines.extend(_official_notice_report_lines(insight))
    lines.extend(["## Deadlines", ""])
    lines.extend(_items_or_empty([item.value for item in insight.important_dates]))
    lines.extend(["", "## Requirements", ""])
    lines.extend(_items_or_empty(insight.required_documents))
    lines.extend(["", "## Risks", ""])
    lines.extend(_items_or_empty([risk.issue for risk in insight.risks]))
    lines.extend(["", "## Action Checklist", ""])
    lines.extend(
        _items_or_empty(
            [
                f"{item.title} ({item.priority}, {item.status})"
                for item in checklist.items
            ]
        )
    )
    lines.extend(["", "## Q&A History", ""])
    if qa_history:
        for index, answer in enumerate(qa_history, start=1):
            lines.extend(
                [
                    f"### Answer {index}",
                    "",
                    answer.answer,
                    "",
                    f"Confidence: {answer.confidence}",
                    f"Mode: {answer.mode}",
                    "",
                ]
            )
    else:
        lines.append("- No questions asked yet.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(_items_or_empty(insight.limitations))
    return "\n".join(lines).strip() + "\n"


def build_json_report(
    *,
    filename: str,
    insight: DocumentInsight,
    checklist: ChecklistResult,
    qa_history: list[QuestionAnswer] | None = None,
) -> str:
    """Build a JSON report from structured local outputs."""
    payload: dict[str, Any] = {
        "filename": filename,
        "document_type": insight.classification.document_type,
        "confidence": insight.confidence,
        "disclaimer": DISCLAIMER,
        "insight": insight.model_dump(mode="json"),
        "checklist": checklist.model_dump(mode="json"),
        "qa_history": [
            answer.model_dump(mode="json") for answer in (qa_history or [])
        ],
        "limitations": insight.limitations,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _items_or_empty(items: list[str]) -> list[str]:
    if not items:
        return ["- Not found in the document."]
    return [f"- {item}" for item in items]


def _official_notice_report_lines(insight: DocumentInsight) -> list[str]:
    notice = insight.official_notice
    if notice is None:
        return []

    lines = [
        "## Official Notice Breakdown",
        "",
        f"- Issuing authority: {notice.issuing_authority or 'Not found'}",
        f"- Notice type: {notice.notice_type or 'Not found'}",
        f"- Notice number: {notice.notice_number or 'Not found'}",
        f"- Gazette date: {notice.gazette_date or 'Not found'}",
        f"- Issue date: {notice.issue_date or 'Not found'}",
        f"- Effective timing: {notice.effective_timing or 'Not found'}",
        f"- Payment timing: {notice.payment_timing or 'Not found'}",
        "",
        "### Notice Table",
        "",
    ]
    if notice.table_rows:
        for row in notice.table_rows:
            lines.append(
                "- "
                f"Service: {row.service or 'Not found'}; "
                f"Heading: {row.heading or 'Not found'}; "
                f"Liable party: {row.liable_party or 'Not found'}; "
                f"Rate/amount: {row.rate_or_amount or 'Not found'}"
            )
    else:
        lines.append("- Not found in the document.")

    lines.extend(["", "### Compliance Duties", ""])
    lines.extend(_items_or_empty(notice.compliance_duties))
    lines.extend(["", "### Possible Consequences", ""])
    lines.extend(_items_or_empty(notice.consequences))
    lines.extend([""])
    return lines
