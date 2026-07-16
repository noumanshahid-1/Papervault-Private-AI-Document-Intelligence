"""Tests for deterministic extraction and OCR quality diagnostics."""

from app.services.extraction_quality import assess_extraction_quality


def test_clean_text_receives_explainable_high_confidence() -> None:
    text = (
        "Admission offer letter. You must accept the offer by 15 July 2026. "
        "Required documents include a passport copy and official transcript. "
        "The enrollment deposit is USD 500."
    )

    diagnostics = assess_extraction_quality(text, engine="pymupdf")

    assert diagnostics.confidence == "high"
    assert diagnostics.confidence_score >= 0.82
    assert diagnostics.engine == "pymupdf"
    assert diagnostics.is_ocr is False
    assert diagnostics.word_count > 20
    assert diagnostics.signals
    assert diagnostics.recommendations == []


def test_low_confidence_ocr_recommends_a_clearer_scan() -> None:
    diagnostics = assess_extraction_quality(
        "N0t1ce \ufffd \ufffd Rs. 3.OOO",
        engine="rapidocr",
        is_ocr=True,
        ocr_engine="rapidocr",
        ocr_mean_confidence=0.41,
    )

    assert diagnostics.confidence == "low"
    assert diagnostics.ocr_mean_confidence == 0.41
    assert diagnostics.suspicious_character_ratio > 0
    assert any("higher-resolution" in item for item in diagnostics.recommendations)
    assert any("source image" in item for item in diagnostics.recommendations)
