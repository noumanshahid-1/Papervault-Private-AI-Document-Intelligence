"""Tests for the public OpenAPI contract."""

from app.main import app


def test_openapi_exposes_canonical_session_models() -> None:
    schema = app.openapi()
    schemas = schema["components"]["schemas"]

    assert "SessionCreatedResponse" in schemas
    assert "SessionsClearedResponse" in schemas
    assert "SavedSession" in schemas
    assert "OfficialNoticeBreakdown" in schemas
    assert "OfficialNoticeTableRow" in schemas
    assert "ExtractionDiagnostics" in schemas
    assert "RetrievalDiagnostics" in schemas
    assert "GenerationDiagnostics" in schemas
    assert "AnswerExplanation" in schemas
    assert "IntelligenceRuntimeResponse" in schemas


def test_official_notice_contract_preserves_structured_fields() -> None:
    notice = app.openapi()["components"]["schemas"]["OfficialNoticeBreakdown"]
    properties = notice["properties"]

    for field in [
        "issuing_authority",
        "notice_type",
        "notice_number",
        "gazette_date",
        "issue_date",
        "legal_basis",
        "subject",
        "effective_timing",
        "payment_timing",
        "table_rows",
        "compliance_duties",
        "consequences",
        "confidence",
        "limitations",
    ]:
        assert field in properties


def test_diagnostic_contracts_are_attached_to_public_responses() -> None:
    schemas = app.openapi()["components"]["schemas"]

    assert "diagnostics" in schemas["ExtractionResult"]["properties"]
    assert "diagnostics" in schemas["DocumentInsight"]["properties"]
    assert "retrieval" in schemas["QuestionAnswer"]["properties"]
    assert "generation" in schemas["QuestionAnswer"]["properties"]
    assert "explanation" in schemas["QuestionAnswer"]["properties"]


def test_runtime_diagnostics_endpoint_is_documented() -> None:
    paths = app.openapi()["paths"]

    assert "/intelligence/runtime" in paths
