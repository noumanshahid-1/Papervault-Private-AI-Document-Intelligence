"""Dependency-free hybrid scoring for local document retrieval."""

from __future__ import annotations

import re


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "would",
    "should",
}

_INTENT_MARKERS: dict[str, tuple[str, ...]] = {
    "deadline": (
        "deadline",
        "due",
        "expire",
        "respond",
        "accept",
        "submit",
        "latest",
        "last date",
        "how long",
    ),
    "start": ("start", "begin", "commence", "opening date"),
    "payment": ("pay", "payment", "fee", "deposit", "amount", "cost", "rate", "tax"),
    "documents": (
        "document",
        "paperwork",
        "passport",
        "transcript",
        "certificate",
        "attachment",
    ),
    "contact": ("contact", "email", "phone", "telephone", "reach"),
    "obligation": ("must", "shall", "required", "obligation", "liable", "need to"),
}

_EVIDENCE_MARKERS: dict[str, tuple[str, ...]] = {
    "deadline": (
        "deadline",
        "due",
        "by ",
        "before ",
        "no later than",
        "not later than",
        "within ",
        "must accept",
        "must submit",
        "shall submit",
    ),
    "start": ("start", "begin", "commence", "programme", "program"),
    "payment": (
        "pay",
        "payment",
        "fee",
        "deposit",
        "amount",
        "rate",
        "tax",
        "usd",
        "gbp",
        "pkr",
        "rs.",
        "$",
        "£",
    ),
    "documents": (
        "required document",
        "documents include",
        "passport",
        "transcript",
        "certificate",
        "evidence",
        "copy",
        "attachment",
    ),
    "contact": ("contact", "email", "phone", "telephone", "@", "address"),
    "obligation": ("must", "shall", "required", "ensure", "liable", "obligation"),
}


def text_terms(text: str) -> set[str]:
    """Return normalized meaningful terms for lexical comparison."""
    terms: set[str] = set()
    for match in re.finditer(r"[a-zA-Z0-9]+", text.lower()):
        term = match.group(0)
        if len(term) > 3 and term.endswith("s"):
            term = term[:-1]
        if term not in _STOP_WORDS and len(term) > 1:
            terms.add(term)
    return terms


def query_intents(query: str) -> set[str]:
    """Detect common document-review intents from a user question."""
    lowered = query.lower()
    return {
        intent
        for intent, markers in _INTENT_MARKERS.items()
        if any(marker in lowered for marker in markers)
    }


def expanded_query_terms(query: str) -> set[str]:
    """Expand query terms with a small transparent document-domain vocabulary."""
    terms = text_terms(query)
    for intent in query_intents(query):
        terms.update(text_terms(" ".join(_EVIDENCE_MARKERS[intent])))
    return terms


def matched_query_terms(query: str, text: str) -> set[str]:
    """Return original or expanded query terms found in candidate evidence."""
    return expanded_query_terms(query).intersection(text_terms(text))


def lexical_relevance(query: str, text: str) -> float:
    """Score direct term coverage while giving smaller weight to expansions."""
    original = text_terms(query)
    expanded = expanded_query_terms(query) - original
    candidate = text_terms(text)
    original_coverage = len(original.intersection(candidate)) / max(len(original), 1)
    expansion_coverage = len(expanded.intersection(candidate)) / max(
        min(len(expanded), 6),
        1,
    )
    return min(original_coverage * 0.78 + expansion_coverage * 0.22, 1.0)


def intent_relevance(query: str, text: str) -> float:
    """Return a bounded bonus when candidate text satisfies query intent."""
    lowered = text.lower()
    intents = query_intents(query)
    if not intents:
        return 0.0
    matched = sum(
        any(marker in lowered for marker in _EVIDENCE_MARKERS[intent])
        for intent in intents
    )
    return min(matched / len(intents), 1.0)


def hybrid_retrieval_score(query: str, text: str, vector_score: float) -> float:
    """Blend vector similarity, lexical coverage, and document-review intent."""
    lexical = lexical_relevance(query, text)
    intent = intent_relevance(query, text)
    score = max(vector_score, 0.0) * 0.45 + lexical * 0.4 + intent * 0.15
    return min(max(score, 0.0), 1.0)


def sentence_relevance(query: str, sentence: str, chunk_score: float) -> float:
    """Rank candidate answer sentences inside retrieved chunks."""
    lexical = lexical_relevance(query, sentence)
    intent = intent_relevance(query, sentence)
    return lexical * 0.55 + intent * 0.3 + max(chunk_score, 0.0) * 0.15
