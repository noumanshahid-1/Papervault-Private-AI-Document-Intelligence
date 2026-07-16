"""Domain-specific extraction for official notices and gazette notifications."""

import re

from app.models.schemas import OfficialNoticeBreakdown, OfficialNoticeTableRow
from app.utils.text_cleaning import normalize_ocr_artifacts, normalize_extracted_text


_MONTH_PATTERN = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
_DATE_RE = re.compile(
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH_PATTERN})\.?,?\s+\d{{4}}\b|"
    rf"\b(?:{_MONTH_PATTERN})\.?\s+\d{{1,2}},\s+\d{{4}}\b",
    re.IGNORECASE,
)
_NOTICE_NUMBER_RE = re.compile(r"\bNo(?:\.|\s)+([A-Z0-9][A-Z0-9/-]{6,})", re.IGNORECASE)
_HEADING_RE = re.compile(r"\b\d{4}\.\d{4}\b")
_RATE_RE = re.compile(
    r"\bRs\.?\s?\d[\d,.]*(?:/-)?(?:\s*(?:per|/)\s*[A-Za-z\s]{2,80})?|"
    r"\b\d[\d,.]+/-\s*per\s+[A-Za-z\s]{2,80}",
    re.IGNORECASE,
)
_PAYMENT_TIMING_RE = re.compile(
    r"not later than the \d{1,2}(?:st|nd|rd|th)?\s+day of the following tax period",
    re.IGNORECASE,
)


def extract_official_notice(text: str) -> OfficialNoticeBreakdown | None:
    """Extract a structured breakdown when text appears to be an official notice."""
    cleaned = normalize_ocr_artifacts(normalize_extracted_text(text))
    lowered = cleaned.lower()
    if not _looks_like_official_notice(lowered):
        return None

    sentences = _sentences(cleaned)
    table_rows = _extract_table_rows(cleaned)
    authority = _extract_authority(cleaned)
    notice_number = _extract_notice_number(cleaned)
    gazette_date, issue_date = _extract_notice_dates(cleaned)
    legal_basis = _extract_legal_basis(sentences)
    subject = _extract_subject(sentences)
    payment_timing = _extract_payment_timing(cleaned)
    compliance_duties = _extract_compliance_duties(sentences, payment_timing)
    consequences = _extract_consequences(sentences)

    signal_count = sum(
        bool(value)
        for value in (
            authority,
            notice_number,
            gazette_date,
            issue_date,
            legal_basis,
            subject,
            payment_timing,
        )
    ) + len(table_rows)

    return OfficialNoticeBreakdown(
        issuing_authority=authority,
        notice_type="notification" if "notification" in lowered else "official notice",
        notice_number=notice_number,
        gazette_date=gazette_date,
        issue_date=issue_date,
        legal_basis=legal_basis,
        subject=subject,
        effective_timing="immediate effect" if "immediate effect" in lowered else None,
        payment_timing=payment_timing,
        table_rows=table_rows,
        compliance_duties=compliance_duties,
        consequences=consequences,
        confidence="high" if signal_count >= 6 else "medium" if signal_count >= 3 else "low",
        limitations=[
            "Official notice extraction is rule-based and may miss table structure in poor OCR scans."
        ],
    )


def _looks_like_official_notice(lowered_text: str) -> bool:
    signals = (
        "government gazette",
        "notification",
        "revenue authority",
        "official gazette",
        "published by authority",
    )
    return sum(signal in lowered_text for signal in signals) >= 2


def _extract_authority(text: str) -> str | None:
    authority_patterns = (
        r"Khyber\s+Pakhtunkhwa\s+Revenue\s+Authority",
        r"Government\s+Gazette\s+Khyber\s+Pakhtunkhwa",
        r"Director\s+General\s+Khyber\s+Pakhtunkhwa\s+Revenue\s+Authority",
    )
    for pattern in authority_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _title_preserving_acronyms(match.group(0))
    return None


def _extract_notice_number(text: str) -> str | None:
    match = _NOTICE_NUMBER_RE.search(text)
    if not match:
        return None
    return match.group(1).strip(" .")


def _extract_notice_dates(text: str) -> tuple[str | None, str | None]:
    matches = [_normalize_date(match.group(0)) for match in _DATE_RE.finditer(text)]
    unique = []
    for value in matches:
        if value not in unique:
            unique.append(value)
    gazette_date = unique[0] if unique else None
    issue_date = unique[1] if len(unique) > 1 else None
    return gazette_date, issue_date


def _extract_legal_basis(sentences: list[str]) -> str | None:
    for sentence in sentences:
        lowered = sentence.lower()
        if "section" in lowered and "act" in lowered:
            return _clip(sentence, 420)
    return None


def _extract_subject(sentences: list[str]) -> str | None:
    for sentence in sentences:
        lowered = sentence.lower()
        if "liability to pay tax" in lowered or "sales tax on services" in lowered:
            return _clip(sentence, 420)
    for sentence in sentences:
        if "taxable service" in sentence.lower():
            return _clip(sentence, 420)
    return None


def _extract_payment_timing(text: str) -> str | None:
    match = _PAYMENT_TIMING_RE.search(text)
    if match:
        return _normalize_date(match.group(0).strip(" .;"))
    return None


def _extract_table_rows(text: str) -> list[OfficialNoticeTableRow]:
    rows: list[OfficialNoticeTableRow] = []
    for heading_match in _HEADING_RE.finditer(text):
        snippet = _snippet(text, heading_match.start(), heading_match.end(), radius=160)
        rate = _extract_rate(snippet)
        service = _extract_service(snippet)
        liable_party = _extract_liable_party(snippet)
        if not any((rate, service, liable_party)):
            continue
        rows.append(
            OfficialNoticeTableRow(
                service=service,
                heading=heading_match.group(0),
                liable_party=liable_party,
                rate_or_amount=rate,
                source_snippet=snippet,
            )
        )
    return rows[:5]


def _extract_rate(text: str) -> str | None:
    matches = [_normalize_amount(match.group(0)) for match in _RATE_RE.finditer(text)]
    matches = [value for value in matches if not re.fullmatch(r"Rs\.?\s*\d{1,2}", value, flags=re.IGNORECASE)]
    if matches:
        return matches[-1]
    return None


def _extract_service(text: str) -> str | None:
    if re.search(r"Custom\s+House\s+Agents", text, flags=re.IGNORECASE):
        return "Custom House Agents"
    if re.search(r"\bCustom\b", text, flags=re.IGNORECASE) and re.search(
        r"House\s+Agents", text, flags=re.IGNORECASE
    ):
        return "Custom House Agents"
    match = re.search(r"Taxable Service\s+(.{3,80}?)\s+(?:Person|Rate|Fixed)", text, flags=re.IGNORECASE)
    if match:
        return _clean_phrase(match.group(1))
    return None


def _extract_liable_party(text: str) -> str | None:
    if re.search(r"Pakistan\s+Single\s+Window", text, flags=re.IGNORECASE):
        return "Pakistan Single Window"
    match = re.search(r"Person[^)]*\)?\s+([A-Z][A-Za-z\s]{3,80}?)\s+(?:Fixed|Rs\.|\d[\d,.]+/-)", text)
    if match:
        return _clean_phrase(match.group(1))
    return None


def _extract_compliance_duties(sentences: list[str], payment_timing: str | None) -> list[str]:
    duties: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        duty: str | None = None
        if "liability to pay tax shall be on" in lowered:
            duty = "Verify who is liable to pay tax under the notification."
        elif "shall ensure" in lowered and "collection and payment" in lowered:
            timing = f" {payment_timing}" if payment_timing else ""
            duty = f"Ensure timely collection and payment of sales tax{timing}."
        elif "e-filing of return" in lowered or "maintenance of record" in lowered:
            duty = "Review e-filing, record maintenance, penalty, surcharge, and recovery provisions."
        if duty and duty not in duties:
            duties.append(duty)
    return duties


def _extract_consequences(sentences: list[str]) -> list[str]:
    consequences: list[str] = []
    markers = ("non-payment", "short-payment", "penalty", "default surcharge", "recovery of tax")
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in markers):
            consequences.append(_clip(sentence, 360))
    return consequences


def _sentences(text: str) -> list[str]:
    joined_lines = re.sub(r"(?<![.!?])\n(?!\n)", " ", text)
    return [
        " ".join(sentence.split())
        for sentence in re.split(r"(?<=[.!?])\s+|\n{2,}", joined_lines)
        if sentence.strip()
    ]


def _normalize_date(value: str) -> str:
    normalized = " ".join(value.split())
    normalized = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th)\s+", r"\1 ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})\b", r"\1 \2, \3", normalized)
    return normalized.strip(" .;")


def _normalize_amount(value: str) -> str:
    normalized = " ".join(value.split())
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


def _snippet(text: str, start: int, end: int, radius: int) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return " ".join(text[left:right].split())


def _clean_phrase(value: str) -> str:
    return " ".join(value.strip(" .;:-").split())


def _clip(value: str, limit: int) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def _title_preserving_acronyms(value: str) -> str:
    words = []
    for word in " ".join(value.split()).split(" "):
        words.append(word if word.isupper() and len(word) <= 4 else word.capitalize())
    return " ".join(words)
