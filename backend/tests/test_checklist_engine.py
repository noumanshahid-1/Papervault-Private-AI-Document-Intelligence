"""Tests for checklist and risk panel generation."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    ClassificationResult,
    DocumentInsight,
    ExtractedItem,
    RiskInsight,
)
from app.services.checklist_engine import generate_checklist


def _insight_with_actions() -> DocumentInsight:
    return DocumentInsight(
        title="Admission Offer Letter",
        classification=ClassificationResult(
            document_type="university admission letter",
            confidence="high",
            evidence=["You must accept this offer by July 15, 2026."],
        ),
        summary="You have been admitted and must complete enrollment steps.",
        important_dates=[
            ExtractedItem(
                value="July 15, 2026",
                source_snippet="You must accept this offer by July 15, 2026.",
            )
        ],
        fees_or_amounts=[
            ExtractedItem(
                value="$500",
                source_snippet="Pay the enrollment deposit of $500 before registration.",
            )
        ],
        required_documents=["passport copy", "official transcript"],
        action_items=[
            "accept this offer by July 15, 2026",
            "Pay the enrollment deposit of $500 before registration",
        ],
        risks=[
            RiskInsight(
                issue="Possible issue: Failure to submit documents may delay enrollment.",
                why_it_matters="The document appears to mention a timing risk.",
                suggested_verification="Verify this with the admissions office.",
                confidence="medium",
                source_snippet="Failure to submit documents may delay enrollment.",
            )
        ],
        missing_information=["Missing bank details may delay payment."],
        contact_information=["admissions@example.edu"],
        confidence="high",
        limitations=[],
    )


def test_generate_checklist_from_insights() -> None:
    result = generate_checklist(_insight_with_actions())

    titles = [item.title for item in result.items]
    assert "Verify deadline: July 15, 2026" in titles
    assert "Prepare required document: passport copy" in titles
    assert "Confirm fee or amount: $500" in titles
    assert all(item.status == "pending" for item in result.items)
    assert any(item.source_snippet for item in result.items)


def test_priority_assignment_uses_dates_risks_and_missing_information() -> None:
    result = generate_checklist(_insight_with_actions())

    by_title = {item.title: item for item in result.items}
    assert by_title["Verify deadline: July 15, 2026"].priority == "high"
    assert by_title["Review possible issue"].priority == "high"
    assert by_title["Resolve missing information"].priority == "high"
    assert by_title["Prepare required document: official transcript"].priority == "medium"


def test_empty_unknown_document_returns_empty_checklist_with_guidance() -> None:
    insight = DocumentInsight(
        title=None,
        classification=ClassificationResult(
            document_type="unknown document",
            confidence="low",
            evidence=[],
        ),
        summary="No extractable summary was found in the document text.",
        confidence="low",
        limitations=[],
    )

    result = generate_checklist(insight)

    assert result.items == []
    assert result.risks == []
    assert result.guidance == (
        "No actionable checklist items were found. Review the extracted text manually "
        "or provide a clearer document scan."
    )


def test_risk_panel_uses_careful_language() -> None:
    result = generate_checklist(_insight_with_actions())

    assert result.risks
    risk = result.risks[0]
    assert risk.possible_issue.startswith("Possible issue")
    assert "verify" in risk.suggested_verification_step.lower()
    assert risk.confidence_level == "medium"


def test_checklist_endpoint_returns_items_and_risks() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/checklist",
        json={"text": "Admission Offer Letter. Required documents: passport copy. You must accept this offer by July 15, 2026. Failure to submit documents may delay enrollment."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert payload["risks"]
    assert payload["items"][0]["status"] == "pending"


def test_checklist_endpoint_rejects_empty_text() -> None:
    client = TestClient(app)

    response = client.post("/documents/checklist", json={"text": ""})

    assert response.status_code == 400
    assert "No document text" in response.json()["detail"]
