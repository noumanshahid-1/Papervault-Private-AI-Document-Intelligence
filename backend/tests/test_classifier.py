"""Tests for deterministic document classification."""

from app.services.classifier import classify_document


def test_classifies_university_admission_letter() -> None:
    result = classify_document(
        "Dear applicant, congratulations on your admission offer to the "
        "Bachelor of Science program. Please accept your offer by July 15, 2026."
    )

    assert result.document_type == "university admission letter"
    assert result.confidence == "high"
    assert any("admission" in match.lower() for match in result.evidence)


def test_classifies_scholarship_document() -> None:
    result = classify_document(
        "Scholarship award notice: tuition waiver and stipend will be paid after "
        "you submit financial aid documents."
    )

    assert result.document_type == "scholarship document"
    assert result.confidence in {"medium", "high"}


def test_classifies_contract_agreement() -> None:
    result = classify_document(
        "This agreement is made between the parties. The contractor shall provide "
        "services under the terms and conditions stated herein."
    )

    assert result.document_type == "contract/agreement"
    assert result.confidence in {"medium", "high"}


def test_unknown_document_has_low_confidence() -> None:
    result = classify_document("Blue notebook. Short reminder about lunch.")

    assert result.document_type == "unknown document"
    assert result.confidence == "low"
    assert result.evidence == []


def test_academic_thesis_format_is_not_government_form() -> None:
    result = classify_document(
        "Department of Computer Science guidelines for preparation of thesis. "
        "Bachelor of Science Computer Science thesis format. A thesis is a "
        "formal document with formatting requirements, title page, abstract, "
        "contents, chapters, references, appendices, evaluation skills, and "
        "specimen certificate pages."
    )

    assert result.document_type == "unknown document"
    assert result.confidence == "low"


def test_scholarship_assessment_instruction_is_not_admission_letter() -> None:
    result = classify_document(
        "Psychological Assessment for Selection of KNB and TIAS Scholarship. "
        "Technical instruction: please be present on Zoom and wait until you get admitted."
    )

    assert result.document_type == "scholarship document"
    assert result.confidence in {"medium", "high"}
