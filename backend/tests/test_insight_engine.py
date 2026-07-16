"""Tests for structured deterministic insight extraction."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.insight_engine import analyze_document


ADMISSION_TEXT = """
University of Northbridge
Admission Offer Letter

Congratulations, you have been admitted to the MSc Data Science program.
You must accept this offer by July 15, 2026.
Required documents: passport copy, official transcript, and proof of English proficiency.
Pay the enrollment deposit of $500 before registration.
For questions contact admissions@northbridge.edu.
Failure to submit documents by the deadline may delay your enrollment.
"""


SCHOLARSHIP_TEXT = """
Global Scholars Fund
Scholarship Award Notice

Your scholarship covers tuition and a monthly stipend of USD 1,200.
Submit the signed award acceptance form by August 1, 2026.
Required documents include bank details and proof of enrollment.
Missing bank details may delay payment.
Contact scholarships@example.org for support.
"""


CONTRACT_TEXT = """
Service Agreement

This agreement is made between Alpha LLC and the contractor.
The contractor shall deliver monthly reports and invoices.
Payment amount is $2,500 per month.
Either party may terminate this agreement with 30 days written notice.
Late delivery may result in penalties.
"""


UNKNOWN_TEXT = "A brief personal note about arranging chairs for a community event."


GOVERNMENT_NOTICE_OCR_TEXT = """
EXTRAORDINARY REGISTEREDNO.PIII GOVERNMENT GAZETTE KHYBERPAKHTUNKHWA
KHYBERPAKHTUNKHWAREVENUEAUTHORITY NOTIFICATION
PeshawarDated,the16tJune,2025.
No.KPRA/ADMN/GN/2025/3337.
The Policy Board of the Khyber Pakhtunkhwa Revenue Authority is pleased to specify the services
for which the liability to pay tax shall be on the person other than the service provider.
Custom House Agents 9806.3000 Pakistan Single Window Fixed rate of Rs. 3.000/-per goods declaration.
This notification is issued with immediate effect. The person made liable to pay tax shall ensure
timely collection and payment of sales tax on services not later than the 15 day of the following tax period.
Non-payment or short-payment may result in penalty, default surcharge and recovery of tax.
"""


def test_analyze_admission_letter_extracts_structured_fields() -> None:
    result = analyze_document(ADMISSION_TEXT)

    assert result.title == "University of Northbridge"
    assert result.classification.document_type == "university admission letter"
    assert "MSc Data Science program" in result.summary
    assert result.important_dates[0].value == "July 15, 2026"
    assert "passport copy" in result.required_documents
    assert "$500" in [amount.value for amount in result.fees_or_amounts]
    assert "admissions@northbridge.edu" in result.contact_information
    assert result.risks
    assert result.action_items
    assert result.confidence in {"medium", "high"}


def test_analyze_scholarship_document_extracts_award_details() -> None:
    result = analyze_document(SCHOLARSHIP_TEXT)

    assert result.classification.document_type == "scholarship document"
    assert any(item.value == "August 1, 2026" for item in result.important_dates)
    assert any(amount.value == "USD 1,200" for amount in result.fees_or_amounts)
    assert "bank details" in result.required_documents
    assert result.missing_information


def test_instruction_document_extracts_imperative_actions() -> None:
    result = analyze_document(
        "Psychological Assessment for Selection of KNB and TIAS Scholarship. "
        "Please be present on Zoom 15 minutes before the scheduled test. "
        "Prepare your identity card and passport. Download SEB according to your device. "
        "Do not use any form of reading material."
    )

    assert result.classification.document_type == "scholarship document"
    assert any("present on zoom" in item.lower() for item in result.action_items)
    assert any("prepare your identity card" in item.lower() for item in result.action_items)
    assert any("download seb" in item.lower() for item in result.action_items)
    assert any("do not use" in item.lower() for item in result.action_items)


def test_analyze_contract_extracts_amounts_actions_and_risks() -> None:
    result = analyze_document(CONTRACT_TEXT)

    assert result.classification.document_type == "contract/agreement"
    assert "$2,500" in [amount.value for amount in result.fees_or_amounts]
    assert any("deliver monthly reports" in item.lower() for item in result.action_items)
    assert any("possible issue" in risk.issue.lower() for risk in result.risks)


def test_unknown_document_does_not_hallucinate_missing_fields() -> None:
    result = analyze_document(UNKNOWN_TEXT)

    assert result.classification.document_type == "unknown document"
    assert result.important_dates == []
    assert result.fees_or_amounts == []
    assert result.required_documents == []
    assert result.contact_information == []
    assert result.confidence == "low"


def test_academic_format_text_does_not_create_false_risks() -> None:
    result = analyze_document(
        "Guidelines for preparation of thesis. The text includes literature review, "
        "methodology, experimental result and discussion, conclusion and future work. "
        "The document discusses problem definition, evaluation skills, and formatting."
    )

    assert result.classification.document_type == "unknown document"
    assert result.risks == []


def test_government_notice_extracts_dates_amounts_obligations_and_risks() -> None:
    result = analyze_document(GOVERNMENT_NOTICE_OCR_TEXT)

    assert result.classification.document_type == "government form"
    assert "Khyber Pakhtunkhwa Revenue Authority" in result.summary
    assert any(item.value == "16 June, 2025" for item in result.important_dates)
    assert any(
        item.value == "not later than the 15 day of the following tax period"
        for item in result.important_dates
    )
    assert any("Rs. 3,000/- per goods declaration" in item.value for item in result.fees_or_amounts)
    assert any("collection and payment" in action.lower() for action in result.action_items)
    assert any("default surcharge" in risk.issue.lower() for risk in result.risks)
    assert result.official_notice is not None
    assert result.official_notice.notice_number == "KPRA/ADMN/GN/2025/3337"
    assert result.official_notice.table_rows


def test_analyze_endpoint_returns_structured_result() -> None:
    client = TestClient(app)

    response = client.post("/documents/analyze", json={"text": ADMISSION_TEXT})

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"]["document_type"] == "university admission letter"
    assert payload["important_dates"][0]["value"] == "July 15, 2026"


def test_analyze_endpoint_rejects_empty_text() -> None:
    client = TestClient(app)

    response = client.post("/documents/analyze", json={"text": "   "})

    assert response.status_code == 400
    assert "No document text" in response.json()["detail"]
