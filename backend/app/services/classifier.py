"""Deterministic document classification for common official documents."""

from collections.abc import Iterable
import re

from app.models.schemas import ClassificationResult


UNKNOWN_DOCUMENT_TYPE = "unknown document"

_RULES: dict[str, tuple[str, ...]] = {
    "university admission letter": (
        "admission offer",
        "admission letter",
        "admitted to the",
        "offer letter",
        "accept your offer",
        "enrollment",
        "enrollment deposit",
        "msc",
    ),
    "scholarship document": (
        "scholarship",
        "scholarship technical instruction",
        "selection of",
        "psychological assessment",
        "award notice",
        "tuition waiver",
        "stipend",
        "financial aid",
    ),
    "visa/immigration instruction": (
        "visa",
        "immigration",
        "passport",
        "embassy",
        "consulate",
        "residence permit",
    ),
    "government form": (
        "government gazette",
        "revenue authority",
        "official notification",
        "notification",
        "treasury",
        "taxable service",
        "sales tax",
        "public notice",
        "application number",
        "official use",
    ),
    "contract/agreement": (
        "agreement",
        "contract",
        "party",
        "parties",
        "terms and conditions",
        "contractor",
        "terminate",
    ),
    "resume/CV": (
        "resume",
        "curriculum vitae",
        "work experience",
        "professional experience",
        "employment history",
        "skills summary",
        "technical skills",
    ),
    "job description": (
        "job description",
        "responsibilities",
        "qualifications",
        "salary",
        "apply",
    ),
    "medical/lab report": (
        "lab report",
        "patient",
        "blood specimen",
        "urine specimen",
        "specimen collection",
        "diagnosis",
        "test result",
        "reference range",
    ),
}


def classify_document(text: str) -> ClassificationResult:
    """Classify document text using transparent keyword rules."""
    normalized = text.lower()
    best_type = UNKNOWN_DOCUMENT_TYPE
    best_matches: list[str] = []

    for document_type, keywords in _RULES.items():
        matches = [keyword for keyword in keywords if _contains_keyword(normalized, keyword)]
        if len(matches) > len(best_matches):
            best_type = document_type
            best_matches = matches

    if not best_matches:
        return ClassificationResult(
            document_type=UNKNOWN_DOCUMENT_TYPE,
            confidence="low",
            evidence=[],
        )

    return ClassificationResult(
        document_type=best_type,
        confidence=_confidence_for_matches(best_matches),
        evidence=_evidence_snippets(text, best_matches),
    )


def _confidence_for_matches(matches: Iterable[str]) -> str:
    count = len(list(matches))
    if count >= 2:
        return "high"
    if count >= 1:
        return "medium"
    return "low"


def _contains_keyword(normalized_text: str, keyword: str) -> bool:
    """Match keywords as phrases, not as accidental substrings inside words."""
    escaped = re.escape(keyword.lower())
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def _evidence_snippets(text: str, matches: list[str]) -> list[str]:
    snippets: list[str] = []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    for sentence in sentences:
        lowered = sentence.lower()
        if any(_contains_keyword(lowered, match) for match in matches):
            cleaned = " ".join(sentence.split())
            if cleaned and cleaned not in snippets:
                snippets.append(cleaned[:240])
        if len(snippets) >= 3:
            break
    return snippets
