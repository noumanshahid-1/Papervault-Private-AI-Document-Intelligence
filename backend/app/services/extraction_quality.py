"""Deterministic quality diagnostics for locally extracted document text."""

from __future__ import annotations

import string
import unicodedata

from app.models.schemas import ExtractionDiagnostics


_READABLE_SYMBOLS = set(string.punctuation + "£€¥₹₨")


def assess_extraction_quality(
    text: str,
    *,
    engine: str,
    is_ocr: bool = False,
    ocr_engine: str | None = None,
    ocr_mean_confidence: float | None = None,
    page_text_coverage: float | None = None,
) -> ExtractionDiagnostics:
    """Return explainable extraction quality metrics without external services."""
    word_count = len(text.split())
    character_count = len(text)
    visible = [character for character in text if not character.isspace()]
    readable_count = sum(_is_readable(character) for character in visible)
    suspicious_count = sum(_is_suspicious(character) for character in visible)
    visible_count = len(visible)
    readable_ratio = readable_count / visible_count if visible_count else 0.0
    suspicious_ratio = suspicious_count / visible_count if visible_count else 0.0

    if not text.strip():
        score = 0.0
    else:
        length_factor = min(word_count / 40, 1.0)
        cleanliness = max(0.0, 1.0 - suspicious_ratio * 4)
        if is_ocr and ocr_mean_confidence is not None:
            score = (
                readable_ratio * 0.3
                + cleanliness * 0.2
                + length_factor * 0.15
                + ocr_mean_confidence * 0.35
            )
        else:
            coverage = 1.0 if page_text_coverage is None else page_text_coverage
            score = (
                readable_ratio * 0.4
                + cleanliness * 0.25
                + length_factor * 0.2
                + coverage * 0.15
            )

    score = round(max(0.0, min(score, 1.0)), 3)
    confidence = _confidence_label(score)
    signals = _quality_signals(
        word_count=word_count,
        readable_ratio=readable_ratio,
        suspicious_ratio=suspicious_ratio,
        is_ocr=is_ocr,
        ocr_engine=ocr_engine,
        ocr_mean_confidence=ocr_mean_confidence,
        page_text_coverage=page_text_coverage,
    )
    recommendations = _recommendations(
        text=text,
        confidence=confidence,
        word_count=word_count,
        suspicious_ratio=suspicious_ratio,
        is_ocr=is_ocr,
        ocr_mean_confidence=ocr_mean_confidence,
        page_text_coverage=page_text_coverage,
    )

    return ExtractionDiagnostics(
        engine=engine,
        confidence=confidence,
        confidence_score=score,
        is_ocr=is_ocr,
        ocr_engine=ocr_engine,
        ocr_mean_confidence=(
            round(ocr_mean_confidence, 3)
            if ocr_mean_confidence is not None
            else None
        ),
        word_count=word_count,
        character_count=character_count,
        readable_character_ratio=round(readable_ratio, 3),
        suspicious_character_ratio=round(suspicious_ratio, 3),
        page_text_coverage=(
            round(page_text_coverage, 3)
            if page_text_coverage is not None
            else None
        ),
        signals=signals,
        recommendations=recommendations,
    )


def _is_readable(character: str) -> bool:
    return character.isalnum() or character in _READABLE_SYMBOLS


def _is_suspicious(character: str) -> bool:
    if character == "\ufffd":
        return True
    category = unicodedata.category(character)
    if category.startswith("C"):
        return True
    if category.startswith("S") and character not in _READABLE_SYMBOLS:
        return True
    return False


def _confidence_label(score: float) -> str:
    if score >= 0.82:
        return "high"
    if score >= 0.58:
        return "medium"
    return "low"


def _quality_signals(
    *,
    word_count: int,
    readable_ratio: float,
    suspicious_ratio: float,
    is_ocr: bool,
    ocr_engine: str | None,
    ocr_mean_confidence: float | None,
    page_text_coverage: float | None,
) -> list[str]:
    signals = [
        f"Extracted {word_count:,} words.",
        f"{readable_ratio:.0%} of visible characters look readable.",
    ]
    if suspicious_ratio > 0:
        signals.append(
            f"{suspicious_ratio:.1%} of visible characters look like OCR or encoding artifacts."
        )
    if page_text_coverage is not None:
        signals.append(
            f"Meaningful text was detected on {page_text_coverage:.0%} of pages."
        )
    if is_ocr:
        signals.append(f"Text was produced with {ocr_engine or 'a local OCR engine'}.")
        if ocr_mean_confidence is not None:
            signals.append(
                f"The OCR engine reported {ocr_mean_confidence:.0%} mean token confidence."
            )
    return signals


def _recommendations(
    *,
    text: str,
    confidence: str,
    word_count: int,
    suspicious_ratio: float,
    is_ocr: bool,
    ocr_mean_confidence: float | None,
    page_text_coverage: float | None,
) -> list[str]:
    recommendations: list[str] = []
    if not text.strip():
        recommendations.append(
            "No readable text was recovered. Verify the file and try a clearer source."
        )
    if is_ocr and ocr_mean_confidence is not None and ocr_mean_confidence < 0.65:
        recommendations.append(
            "Use a higher-resolution, straightened image with stronger contrast."
        )
    if suspicious_ratio >= 0.02:
        recommendations.append(
            "Compare names, dates, codes, and amounts against the source image."
        )
    if page_text_coverage is not None and page_text_coverage < 0.7:
        recommendations.append(
            "Some PDF pages contain little text and may require OCR."
        )
    if word_count < 10 and text.strip():
        recommendations.append(
            "Very little text was recovered; confirm that the document is complete."
        )
    if confidence == "low" and not recommendations:
        recommendations.append(
            "Verify extracted details against the source before relying on the analysis."
        )
    return recommendations
