"""Text normalization helpers shared by extraction and analysis services."""

import re


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace into single spaces."""
    return " ".join(text.split())


def normalize_extracted_text(text: str) -> str:
    """Clean extracted document text while preserving paragraph structure."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines: list[str] = []
    blank_pending = False

    for raw_line in normalized.split("\n"):
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if not line:
            if cleaned_lines:
                blank_pending = True
            continue
        if blank_pending and cleaned_lines and cleaned_lines[-1] != "":
            cleaned_lines.append("")
        cleaned_lines.append(line)
        blank_pending = False

    return "\n".join(cleaned_lines).strip()


def normalize_ocr_artifacts(text: str) -> str:
    """Reduce common OCR spacing artifacts without changing document meaning."""
    normalized = text
    replacements = [
        ("KHYBERPAKHTUNKHWAREVENUEAUTHORITY", "KHYBER PAKHTUNKHWA REVENUE AUTHORITY"),
        ("PublishedbyAuthority", "Published by Authority"),
        ("REGISTEREDNO", "REGISTERED NO"),
        ("KHYBERPAKHTUNKHWA", "KHYBER PAKHTUNKHWA"),
        ("PeshawarDated", "Peshawar Dated"),
        ("asmentioned", "as mentioned"),
        ("inrespect", "in respect"),
        ("underTable", "under Table"),
        ("ofs ales", "of sales"),
        ("ofsales", "of sales"),
        ("andpayment", "and payment"),
        ("anddefault", "and default"),
        ("andrecovery", "and recovery"),
        ("short-payment", "short-payment"),
        ("Staty.&Ptg", "Stationery and Printing"),
    ]
    for source, target in replacements:
        normalized = normalized.replace(source, target)

    normalized = normalized.replace("，", ",").replace("（", "(").replace("）", ")")
    field_words = (
        "APPLICATION",
        "APPOINTMENT",
        "CATEGORY",
        "CONTACT",
        "DEADLINE",
        "DEPOSIT",
        "DOCUMENTS",
        "FEE",
        "LICENSE",
        "METHOD",
        "OFFICE",
        "RECORD",
        "REFERENCE",
        "RENEWAL",
        "START",
        "DATE",
        "AMOUNT",
        "DUE",
    )
    for field_word in field_words:
        normalized = re.sub(
            rf"(?<=[A-Z])(?={field_word}\b)",
            " ",
            normalized,
        )
    month_names = (
        "January|February|March|April|May|June|July|August|September|October|"
        "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    )
    normalized = re.sub(rf"(?i)(\d{{1,2}})(?:st|nd|rd|th|t)(?=({month_names}))", r"\1 ", normalized)
    normalized = re.sub(rf"(?i)(\d{{1,2}})(?=({month_names}))", r"\1 ", normalized)
    normalized = re.sub(rf"(?i)({month_names})(?=\d{{4}})", r"\1 ", normalized)
    normalized = re.sub(r"(?<=\d{4})(?=[A-Za-z])", " ", normalized)
    normalized = re.sub(r"\b(USD|EUR|GBP|PKR)(?=\d)", r"\1 ", normalized)
    normalized = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th|t)\s+([A-Z][a-z]+|[A-Z]+)\b", r"\1 \2", normalized)
    normalized = re.sub(r"\b([A-Za-z]+),(\d{4})\b", r"\1, \2", normalized)
    normalized = re.sub(r"\b([A-Za-z]+)(\d{1,2})\b", r"\1 \2", normalized)
    normalized = re.sub(r"(the)(\d{1,2})", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(\d{1,2})(day)\b", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(section)(\d+)", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(sub-section)(\d+)", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(Act|No)\.?\s*([A-Z0-9]+)", r"\1. \2", normalized)
    normalized = re.sub(r"\s+([,.;:])", r"\1", normalized)
    normalized = re.sub(r"(?<=[A-Za-z]),(?=\d)", ", ", normalized)
    normalized = re.sub(r"([;:])(?=\S)", r"\1 ", normalized)
    normalized = re.sub(r"(?<=[0-9a-z])\.(?=[A-Z][a-z])", ". ", normalized)
    return normalize_extracted_text(normalized)
