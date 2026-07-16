"""Structured deterministic document insight extraction."""

import re

from app.models.schemas import (
    ClassificationResult,
    DocumentAnalysisDiagnostics,
    DocumentInsight,
    ExtractedItem,
    RiskInsight,
)
from app.services.classifier import UNKNOWN_DOCUMENT_TYPE, classify_document
from app.services.official_notice_engine import extract_official_notice
from app.utils.text_cleaning import normalize_extracted_text, normalize_ocr_artifacts


CONFIDENCE_UNKNOWN = "unknown"

_MONTH_PATTERN = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
_DATE_RE = re.compile(
    rf"\b(?:{_MONTH_PATTERN})\.?\s+\d{{1,2}},\s+\d{{4}}\b|"
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH_PATTERN})\.?,?\s+\d{{4}}\b|"
    r"\bnot later than the \d{1,2}(?:st|nd|rd|th)?\s+day of the following tax period\b",
    re.IGNORECASE,
)
_AMOUNT_RE = re.compile(
    r"\b(?:USD|EUR|GBP|PKR)\s?[\d,]+(?:\.\d{2})?\b|"
    r"\$\s?[\d,]+(?:\.\d{2})?|"
    r"\bRs\.?\s?\d[\d,.]*(?:/-)?(?:\s*(?:per|/)\s*[A-Za-z\s]{2,80})?|"
    r"\b\d[\d,.]+/-\s*per\s+[A-Za-z\s]{2,80}",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


def analyze_document(text: str, filename: str | None = None) -> DocumentInsight:
    """Return grounded, rule-based document insights from extracted text."""
    cleaned = normalize_ocr_artifacts(normalize_extracted_text(text))
    classification = classify_document(cleaned)
    sentences = _sentences(cleaned)

    important_dates = _extract_items(cleaned, _DATE_RE)
    fees_or_amounts = _extract_items(cleaned, _AMOUNT_RE)
    required_documents = _extract_required_documents(sentences)
    action_items = _extract_action_items(sentences)
    risks = _extract_risks(sentences)
    missing_information = _extract_missing_information(sentences)
    contacts = _extract_contacts(cleaned)
    official_notice = extract_official_notice(cleaned)
    diagnostics = _analysis_diagnostics(
        classification=classification,
        dates=important_dates,
        required_documents=required_documents,
        action_items=action_items,
        amounts=fees_or_amounts,
        risks=risks,
        has_official_notice=official_notice is not None,
    )

    limitations = [
        "Insights are extracted with deterministic local rules and should be verified against the source document."
    ]
    if classification.document_type in {
        "visa/immigration instruction",
        "contract/agreement",
        "medical/lab report",
        "government form",
    }:
        limitations.append(
            "This is not professional advice. Verify high-stakes decisions with the relevant authority or a qualified professional."
        )

    return DocumentInsight(
        title=_extract_title(cleaned, filename),
        classification=classification,
        summary=_build_summary(sentences, classification.document_type, cleaned),
        important_dates=important_dates,
        fees_or_amounts=fees_or_amounts,
        required_documents=required_documents,
        action_items=action_items,
        risks=risks,
        missing_information=missing_information,
        contact_information=contacts,
        official_notice=official_notice,
        confidence=_confidence_from_score(diagnostics.confidence_score),
        diagnostics=diagnostics,
        limitations=limitations,
    )


def _sentences(text: str) -> list[str]:
    joined_lines = re.sub(r"(?<![.!?])\n(?!\n)", " ", text)
    rough_sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", joined_lines)
    return [" ".join(sentence.split()) for sentence in rough_sentences if sentence.strip()]


def _extract_title(text: str, filename: str | None) -> str | None:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:120]
    return filename


def _build_summary(sentences: list[str], document_type: str, text: str) -> str:
    if not sentences:
        return "No extractable summary was found in the document text."
    if document_type == "government form":
        return _build_government_summary(sentences, text)
    return " ".join(sentences[:3])


def _build_government_summary(sentences: list[str], text: str) -> str:
    authority = _detect_authority(text)
    subject_sentence = _first_sentence_matching(
        sentences,
        ("notification", "sales tax", "taxable service", "liability", "collection"),
    )
    obligation_sentence = _first_sentence_matching(
        sentences,
        ("shall ensure", "liable to pay", "collection and payment", "not later"),
    )
    parts: list[str] = []
    if authority:
        parts.append(f"This appears to be an official notice from {authority}.")
    if subject_sentence:
        parts.append(subject_sentence)
    if obligation_sentence and obligation_sentence != subject_sentence:
        parts.append(obligation_sentence)
    if parts:
        return " ".join(parts)[:900]
    return " ".join(sentences[:3])


def _extract_items(text: str, pattern: re.Pattern[str]) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        value = _normalize_extracted_value(match.group(0).strip())
        snippet = _snippet(text, match.start(), match.end())
        if _looks_like_ocr_table_artifact(value, snippet):
            continue
        if value in seen:
            continue
        seen.add(value)
        items.append(
            ExtractedItem(
                value=value,
                source_snippet=snippet,
            )
        )
    return items


def _extract_required_documents(sentences: list[str]) -> list[str]:
    requirements: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if (
            "required documents" in lowered
            or "documents include" in lowered
            or "include " in lowered
        ):
            fragment = re.split(
                r":| include | includes ",
                sentence,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[-1]
            for part in re.split(r",| and ", fragment):
                item = _clean_list_item(part)
                if _looks_like_requirement(item) and item not in requirements:
                    requirements.append(item)
    return requirements


def _extract_action_items(sentences: list[str]) -> list[str]:
    actions: list[str] = []
    action_markers = (
        "must ",
        "shall ",
        "shall ensure",
        "submit ",
        "pay ",
        "accept ",
        "deliver ",
        "provide ",
        "complete ",
        "please ",
        "make sure",
        "prepare ",
        "ensure ",
        "open ",
        "download ",
        "write down",
        "listen carefully",
        "do not ",
        "show ",
        "liable to pay",
        "liability to pay",
        "payment of",
        "collection and payment",
        "e-filing",
        "maintenance of record",
    )
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in action_markers):
            action = _action_from_sentence(sentence)
            if action and action not in actions:
                actions.append(action)
    return actions


def _extract_risks(sentences: list[str]) -> list[RiskInsight]:
    risks: list[RiskInsight] = []
    marker_patterns = (
        r"\bfailure\b",
        r"\bmay delay\b",
        r"\bmissing\b",
        r"\bpenalt\w*\b",
        r"\bterminate\b",
        r"\blate\b",
        r"\bnon-payment\b",
        r"\bshort-payment\b",
        r"\bdefault surcharge\b",
        r"\brecovery of tax\b",
        r"\bnot later than\b",
    )
    for sentence in sentences:
        if any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in marker_patterns):
            risks.append(
                RiskInsight(
                    issue=f"Possible issue: {sentence}",
                    why_it_matters="The document appears to mention a condition that could affect timing, eligibility, payment, or obligations.",
                    suggested_verification="Verify this point against the source document and the relevant authority or responsible contact.",
                    confidence="medium",
                    source_snippet=sentence,
                )
            )
    return risks


def _extract_missing_information(sentences: list[str]) -> list[str]:
    missing: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if (
            "missing " in lowered
            or "incomplete" in lowered
            or "not provided" in lowered
        ):
            if sentence not in missing:
                missing.append(sentence)
    return missing


def _extract_contacts(text: str) -> list[str]:
    contacts: list[str] = []
    for pattern in (_EMAIL_RE, _PHONE_RE):
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if value not in contacts:
                contacts.append(value)
    return contacts


def _detect_authority(text: str) -> str | None:
    authority_patterns = (
        r"Khyber\s+Pakhtunkhwa\s+Revenue\s+Authority",
        r"Government\s+Gazette\s+Khyber\s+Pakhtunkhwa",
        r"Director\s+General\s+Khyber\s+Pakhtunkhwa\s+Revenue\s+Authority",
    )
    for pattern in authority_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(0).split()).title()
    return None


def _analysis_diagnostics(
    *,
    classification: ClassificationResult,
    dates: list[ExtractedItem],
    required_documents: list[str],
    action_items: list[str],
    amounts: list[ExtractedItem],
    risks: list[RiskInsight],
    has_official_notice: bool,
) -> DocumentAnalysisDiagnostics:
    signal_count = len(dates) + len(required_documents) + len(action_items) + len(amounts)
    grounded_field_count = sum(
        bool(items)
        for items in (dates, required_documents, action_items, amounts, risks)
    ) + int(has_official_notice)
    classification_score = {
        "high": 0.9,
        "medium": 0.62,
        "low": 0.25,
    }.get(classification.confidence, 0.25)
    score = (
        classification_score * 0.4
        + min(signal_count / 6, 1.0) * 0.4
        + min(grounded_field_count / 4, 1.0) * 0.2
    )
    if classification.document_type == UNKNOWN_DOCUMENT_TYPE:
        score = min(score, 0.44)

    reasons = [
        f"Classification confidence is {classification.confidence}.",
        f"{signal_count} structured signal(s) were extracted.",
        f"{grounded_field_count} finding group(s) contain evidence.",
    ]
    if classification.evidence:
        reasons.append(
            f"Classification is supported by {len(classification.evidence)} source snippet(s)."
        )
    if has_official_notice:
        reasons.append("A domain-specific official-notice structure was recovered.")
    if classification.document_type == UNKNOWN_DOCUMENT_TYPE:
        reasons.append("The document type could not be identified confidently.")

    return DocumentAnalysisDiagnostics(
        confidence_score=round(score, 3),
        classification_confidence=classification.confidence,
        extracted_signal_count=signal_count,
        grounded_field_count=grounded_field_count,
        reasons=reasons,
    )


def _confidence_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _snippet(text: str, start: int, end: int, radius: int = 80) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return " ".join(text[left:right].split())


def _clean_list_item(item: str) -> str:
    return item.strip(" .;:-").strip()


def _looks_like_requirement(item: str) -> bool:
    if not item or len(item) < 3:
        return False
    lowered = item.lower()
    stop_fragments = ("required documents", "documents include", "deadline")
    return not any(fragment in lowered for fragment in stop_fragments)


def _action_from_sentence(sentence: str) -> str:
    cleaned = sentence.strip(" .")
    lowered = cleaned.lower()
    if "liability to pay tax shall be on" in lowered:
        return "verify who is liable to pay tax under the notification"
    if "shall ensure" in lowered and "collection and payment" in lowered:
        timing = ""
        timing_match = re.search(
            r"not later than the \d{1,2}(?:st|nd|rd|th)?\s+day of the following tax period",
            cleaned,
            flags=re.IGNORECASE,
        )
        if timing_match:
            timing = f" {timing_match.group(0)}"
        return f"ensure timely collection and payment of sales tax{timing}".strip()
    if "e-filing of return" in lowered or "maintenance of record" in lowered:
        return "review return filing, record maintenance, penalty, surcharge, and tax recovery provisions"
    for marker in (
        "must ",
        "shall ensure",
        "shall ",
        "submit ",
        "pay ",
        "accept ",
        "deliver ",
        "provide ",
        "complete ",
        "please ",
        "make sure",
        "prepare ",
        "ensure ",
        "open ",
        "download ",
        "write down",
        "listen carefully",
        "do not ",
        "show ",
        "liable to pay",
        "liability to pay",
        "payment of",
        "collection and payment",
        "e-filing",
        "maintenance of record",
    ):
        index = lowered.find(marker)
        if index >= 0:
            return cleaned[index:]
    return cleaned


def _first_sentence_matching(sentences: list[str], markers: tuple[str, ...]) -> str | None:
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in markers):
            return sentence
    return None


def _normalize_extracted_value(value: str) -> str:
    normalized = " ".join(value.split())
    normalized = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th)\s+", r"\1 ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})\b", r"\1 \2, \3", normalized)
    normalized = re.sub(r"\bRs\.?\s*([\d]+)\.([\d]{3})(/-)?", r"Rs. \1,\2\3", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^(\d{1,3})[,.](\d{3})(/-)", r"Rs. \1,\2\3", normalized)
    normalized = normalized.replace("/-per", "/- per")
    normalized = re.sub(
        r"per goods\s+House Agents\s+declaration",
        "per goods declaration",
        normalized,
        flags=re.IGNORECASE,
    )
    if normalized.lower().endswith("per goods"):
        normalized = f"{normalized} declaration"
    return normalized.strip(" .;")


def _looks_like_ocr_table_artifact(value: str, snippet: str) -> bool:
    return bool(
        re.fullmatch(r"Rs\.?\s*\d{1,2}", value, flags=re.IGNORECASE)
        and "/-" in snippet
    )
