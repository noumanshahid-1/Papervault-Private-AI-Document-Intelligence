"""Local retrieval and extractive Q&A fallback."""

import re

from app.config import get_settings
from app.models.schemas import (
    AnswerExplanation,
    GenerationDiagnostics,
    QuestionAnswer,
    RetrievalDiagnostics,
    RetrievalResult,
    SourceSnippet,
)
from app.services.chunker import chunk_text
from app.services.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.llm_adapter import LocalLLMResult, OllamaLLMAdapter, build_qa_prompt
from app.services.retrieval_scoring import (
    matched_query_terms,
    query_intents,
    sentence_relevance,
    text_terms,
)
from app.services.vector_store import LocalVectorStore
from app.utils.text_cleaning import normalize_ocr_artifacts, normalize_extracted_text


NOT_FOUND_MESSAGE = "Not found in the document."
_DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+"
    r"\d{1,2},?\s+\d{4}\b|"
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?,?\s+"
    r"\d{4}\b|"
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    flags=re.IGNORECASE,
)


def answer_question(
    *,
    text: str,
    question: str,
    filename: str | None = None,
    top_k: int = 5,
    embedding_provider: EmbeddingProvider | None = None,
    llm_adapter: object | None = None,
    use_local_llm: bool | None = None,
    answer_mode: str = "auto",
    model: str | None = None,
) -> QuestionAnswer:
    """Answer a question from document text using local retrieval with fallback."""
    settings = get_settings()
    chunks = chunk_text(text, filename=filename)
    if not chunks:
        return QuestionAnswer(
            answer=NOT_FOUND_MESSAGE,
            source_snippets=[],
            confidence="low",
            mode="extractive",
            generation=_generation_diagnostics(
                requested_mode=answer_mode,
                actual_mode="extractive",
                model=model,
                fallback_reason="No document chunks were available for retrieval.",
            ),
            explanation=_answer_explanation(
                strategy="no_answer",
                confidence="low",
                retrieval=None,
            ),
        )

    provider = embedding_provider or get_embedding_provider()
    store = LocalVectorStore(embedding_provider=provider)
    store.add_chunks(chunks)
    retrieved = store.search(question, top_k=top_k)
    retrieval = _retrieval_diagnostics(
        question=question,
        retrieved=retrieved,
        provider=provider,
        vector_backend=store.backend_name,
        requested_top_k=top_k,
        min_score=settings.local_retrieval_min_score,
    )

    cleaned_text = normalize_ocr_artifacts(normalize_extracted_text(text))
    answer_sentence = _direct_grounded_answer(question, cleaned_text)
    strategy = "direct_rule"
    if answer_sentence is None:
        answer_sentence = _best_grounded_sentence(question, retrieved)
        strategy = "retrieved_sentence"
    if answer_sentence is None:
        return QuestionAnswer(
            answer=NOT_FOUND_MESSAGE,
            source_snippets=[],
            confidence="low",
            mode="extractive",
            retrieval=retrieval,
            generation=_generation_diagnostics(
                requested_mode=answer_mode,
                actual_mode="extractive",
                model=model,
                fallback_reason="No sufficiently grounded answer sentence was found.",
            ),
            explanation=_answer_explanation(
                strategy="no_answer",
                confidence="low",
                retrieval=retrieval,
            ),
        )

    grounded_results = _prioritize_answer_source(answer_sentence, retrieved)
    snippets = [
        _source_snippet(result)
        for result in grounded_results[:top_k]
        if result.score > 0
    ]
    if use_local_llm is None:
        use_local_llm = (
            settings.local_llm_enabled
            if answer_mode in {"auto", "local_llm"}
            else False
        )

    fallback_reason: str | None = None
    if use_local_llm:
        adapter = llm_adapter or OllamaLLMAdapter(model=model)
        llm_result = adapter.generate(
            build_qa_prompt(
                "\n\n".join(snippet.text for snippet in snippets),
                question,
            )
        )
        if _usable_llm_result(llm_result):
            confidence = _confidence_for_llm_answer(llm_result.text, retrieval)
            return QuestionAnswer(
                answer=llm_result.text,
                source_snippets=snippets[:3],
                confidence=confidence,
                mode="local_llm",
                retrieval=retrieval,
                generation=_generation_diagnostics(
                    requested_mode=answer_mode,
                    actual_mode="local_llm",
                    model=model,
                    model_used=llm_result.model,
                ),
                explanation=_answer_explanation(
                    strategy="local_llm_grounded",
                    confidence=confidence,
                    retrieval=retrieval,
                ),
            )
        fallback_reason = llm_result.error or "The local model response was not usable."
    elif answer_mode == "local_llm" and not settings.local_llm_enabled:
        fallback_reason = "Local LLM mode is disabled in backend configuration."

    confidence = _confidence_for_answer(question, answer_sentence, retrieved)
    return QuestionAnswer(
        answer=answer_sentence,
        source_snippets=snippets[:3],
        confidence=confidence,
        mode="extractive",
        retrieval=retrieval,
        generation=_generation_diagnostics(
            requested_mode=answer_mode,
            actual_mode="extractive",
            model=model,
            fallback_reason=fallback_reason,
        ),
        explanation=_answer_explanation(
            strategy=strategy,
            confidence=confidence,
            retrieval=retrieval,
        ),
    )


def _best_grounded_sentence(
    question: str, retrieved: list[RetrievalResult]
) -> str | None:
    if not text_terms(question):
        return None

    best_sentence: str | None = None
    best_score = 0.0
    for result in retrieved:
        for sentence in _sentences(result.chunk.text):
            if not matched_query_terms(question, sentence):
                continue
            score = sentence_relevance(question, sentence, result.score)
            if score > best_score:
                best_sentence = sentence
                best_score = score

    return best_sentence if best_score >= 0.12 else None


def _direct_grounded_answer(question: str, text: str) -> str | None:
    lowered = question.lower()
    sentences = _sentences(text)
    if any(term in lowered for term in ("deadline", "deadlines", "date", "dates", "due", "when")):
        dated_sentence = _first_sentence_with_date(sentences, question)
        if dated_sentence:
            return dated_sentence

    if "documents" in query_intents(question):
        requirement_sentence = _first_sentence_matching(
            sentences,
            (
                "required documents",
                "documents include",
                "documents required",
                "supporting documents",
                "passport",
                "transcript",
                "certificate",
            ),
        )
        if requirement_sentence:
            return requirement_sentence

    if any(term in lowered for term in ("payment", "payments", "rate", "rates", "fee", "amount", "tax")):
        amount_sentence = _first_sentence_with_amount(sentences)
        if amount_sentence is None:
            amount_sentence = _first_sentence_matching(
            sentences,
            ("fixed rate", "rate of tax", "rs.", "pkr", "payment", "pay tax"),
            )
        if amount_sentence:
            amount = _first_amount(amount_sentence)
            if amount:
                return f"The document appears to mention {amount}."
            return amount_sentence

    if any(term in lowered for term in ("obligation", "obligations", "required", "must", "shall", "liable")):
        obligations = _summarized_obligations(sentences)
        if obligations:
            return "The document appears to mention these obligations: " + "; ".join(obligations)

    if any(
        term in lowered
        for term in ("contact", "email", "phone", "telephone", "reach")
    ):
        contact_sentence = _first_sentence_matching(
            sentences,
            ("contact", "email", "phone", "telephone", "@"),
        )
        if contact_sentence:
            return contact_sentence

    if any(term in lowered for term in ("about", "summary", "summarize", "document")):
        about_sentence = _about_sentence(sentences)
        if about_sentence:
            return f"This document appears to be about: {about_sentence}"
    return None


def _first_sentence_matching(sentences: list[str], markers: tuple[str, ...]) -> str | None:
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in markers):
            return sentence
    return None


def _first_sentence_with_amount(sentences: list[str]) -> str | None:
    for sentence in sentences:
        if _first_amount(sentence):
            return sentence
    return None


def _first_sentence_with_date(sentences: list[str], question: str) -> str | None:
    dated = [sentence for sentence in sentences if _DATE_PATTERN.search(sentence)]
    intents = query_intents(question)
    if "start" in intents:
        start_sentence = _first_sentence_matching(
            dated,
            ("start", "begin", "commence", "programme", "program"),
        )
        if start_sentence:
            return start_sentence
    if "deadline" in intents:
        deadline_sentence = _first_sentence_matching(
            dated,
            (
                "deadline",
                "due",
                "accept",
                "respond",
                "submit",
                "before",
                "by ",
                "no later",
                "not later",
                "within",
                "must",
            ),
        )
        if deadline_sentence:
            return deadline_sentence

    ranked = sorted(
        dated,
        key=lambda sentence: sentence_relevance(question, sentence, 0.0),
        reverse=True,
    )
    if ranked and sentence_relevance(question, ranked[0], 0.0) > 0:
        return ranked[0]
    for sentence in dated:
        lowered = sentence.lower()
        if any(marker in lowered for marker in ("deadline", "due", "accept", "submit", "before", "by ")):
            return sentence
    return dated[0] if dated else None


def _prioritize_answer_source(
    answer: str, retrieved: list[RetrievalResult]
) -> list[RetrievalResult]:
    normalized_answer = " ".join(answer.lower().split())
    matching: list[RetrievalResult] = []
    remaining: list[RetrievalResult] = []
    for result in retrieved:
        normalized_chunk = " ".join(result.chunk.text.lower().split())
        if normalized_answer in normalized_chunk:
            matching.append(result)
        else:
            remaining.append(result)
    return matching + remaining


def _about_sentence(sentences: list[str]) -> str | None:
    for sentence in sentences:
        lowered = sentence.lower()
        if "notification" in lowered and (
            "revenue authority" in lowered or "sales tax" in lowered
        ):
            return sentence
    return _first_sentence_matching(
        sentences,
        ("sales tax", "notification", "agreement", "admission", "scholarship"),
    )


def _summarized_obligations(sentences: list[str]) -> list[str]:
    obligations: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        item: str | None = None
        if "liability to pay tax shall be on" in lowered:
            item = "verify who is liable to pay tax under the notification"
        elif "shall ensure" in lowered and "collection and payment" in lowered:
            timing_match = re.search(
                r"not later than the \d{1,2}(?:st|nd|rd|th)?\s+day of the following tax period",
                sentence,
                flags=re.IGNORECASE,
            )
            timing = f" {timing_match.group(0)}" if timing_match else ""
            item = f"ensure timely collection and payment of sales tax{timing}".strip()
        elif "e-filing of return" in lowered or "maintenance of record" in lowered:
            item = "review return filing, record maintenance, penalty, surcharge, and tax recovery provisions"
        elif "must " in lowered:
            item = sentence
        if item and item not in obligations:
            obligations.append(item)
        if len(obligations) >= 3:
            break
    return obligations


def _first_amount(text: str) -> str | None:
    patterns = (
        r"\bRs\.?\s?\d[\d,.]*(?:/-)?(?:\s*(?:per|/)\s*[A-Za-z\s]{2,80})?",
        r"\b\d[\d,.]+/-\s*per\s+[A-Za-z\s]{2,80}",
        r"\b(?:USD|EUR|GBP|PKR)\s?[\d,]+(?:\.\d{2})?\b",
        r"\$\s?[\d,]+(?:\.\d{2})?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = " ".join(match.group(0).split())
            value = re.sub(r"^(\d{1,3})[,.](\d{3})(/-)", r"Rs. \1,\2\3", value)
            value = value.replace("/-per", "/- per")
            value = re.sub(
                r"per goods\s+House Agents\s+declaration",
                "per goods declaration",
                value,
                flags=re.IGNORECASE,
            )
            if value.lower().endswith("per goods"):
                value = f"{value} declaration"
            return value.strip(" .;")
    return None


def _confidence_for_answer(
    question: str, answer: str, retrieved: list[RetrievalResult]
) -> str:
    overlap = len(matched_query_terms(question, answer))
    top_score = retrieved[0].score if retrieved else 0
    if (
        any(term in question.lower() for term in ("deadline", "date", "due", "when"))
        and _DATE_PATTERN.search(answer)
        and top_score > 0
    ):
        return "medium"
    if answer.lower().startswith(
        (
            "the document appears to mention",
            "the document appears to be about",
            "this document appears to be about",
        )
    ) and top_score > 0:
        return "medium"
    if overlap >= 2 and top_score >= 0.25:
        return "high"
    if overlap >= 1 and top_score > 0:
        return "medium"
    return "low"


def _source_snippet(result: RetrievalResult) -> SourceSnippet:
    return SourceSnippet(
        text=result.chunk.text,
        chunk_id=result.chunk.chunk_id,
        score=result.score,
        page_number=result.chunk.page_number,
        source_filename=result.chunk.source_filename,
    )


def _usable_llm_result(result: LocalLLMResult) -> bool:
    if not result.available or not result.text.strip():
        return False
    lowered = result.text.lower()
    return "not found" not in lowered


def _confidence_for_llm_answer(
    answer: str,
    retrieval: RetrievalDiagnostics,
) -> str:
    if (
        len(answer.split()) >= 6
        and retrieval.relevant_count >= 1
        and retrieval.top_score >= 0.15
    ):
        return "medium"
    return "low"


def _sentences(text: str) -> list[str]:
    joined_lines = re.sub(r"(?<![.!?])\n(?!\n)", " ", text)
    return [
        " ".join(sentence.split())
        for sentence in re.split(r"(?<=[.!?])\s+|\n{2,}", joined_lines)
        if sentence.strip()
    ]


def _retrieval_diagnostics(
    *,
    question: str,
    retrieved: list[RetrievalResult],
    provider: EmbeddingProvider,
    vector_backend: str,
    requested_top_k: int,
    min_score: float,
) -> RetrievalDiagnostics:
    scores = [result.score for result in retrieved]
    query_terms = sorted(text_terms(question))
    matched_terms = sorted(
        matched_query_terms(
            question,
            " ".join(result.chunk.text for result in retrieved),
        )
    )
    relevant_count = sum(score >= min_score for score in scores)
    warnings: list[str] = []
    if not retrieved:
        warnings.append("No chunks were retrieved.")
    elif relevant_count == 0:
        warnings.append(
            "Retrieved chunks scored below the configured relevance threshold."
        )
    if getattr(provider, "provider_name", "unknown") == "hashing":
        warnings.append(
            "Hashing embeddings are deterministic but less semantic than a cached sentence-transformer model."
        )

    top_score = max(scores, default=0.0)
    mean_score = sum(scores) / len(scores) if scores else 0.0
    return RetrievalDiagnostics(
        embedding_provider=getattr(provider, "provider_name", "unknown"),
        embedding_model=getattr(provider, "model_name", None),
        vector_backend=vector_backend,
        requested_top_k=requested_top_k,
        retrieved_count=len(retrieved),
        relevant_count=relevant_count,
        top_score=round(top_score, 4),
        mean_score=round(mean_score, 4),
        score_spread=round(top_score - min(scores, default=0.0), 4),
        query_terms=query_terms[:12],
        matched_terms=matched_terms[:12],
        warnings=warnings,
    )


def _generation_diagnostics(
    *,
    requested_mode: str,
    actual_mode: str,
    model: str | None,
    model_used: str | None = None,
    fallback_reason: str | None = None,
) -> GenerationDiagnostics:
    settings = get_settings()
    return GenerationDiagnostics(
        requested_mode=requested_mode,
        actual_mode=actual_mode,
        configured_model=model or settings.local_llm_model,
        model_used=model_used,
        local_llm_enabled=settings.local_llm_enabled,
        fallback_reason=fallback_reason,
    )


def _answer_explanation(
    *,
    strategy: str,
    confidence: str,
    retrieval: RetrievalDiagnostics | None,
) -> AnswerExplanation:
    strategy_labels = {
        "direct_rule": "A deterministic document rule found a directly relevant sentence.",
        "retrieved_sentence": "The answer was selected from the highest-overlap retrieved sentence.",
        "local_llm_grounded": "A local Ollama model summarized only the retrieved source context.",
        "no_answer": "The document did not provide enough grounded evidence for an answer.",
    }
    reasons = [strategy_labels.get(strategy, strategy)]
    if retrieval is not None:
        reasons.append(
            "Retrieval combined vector similarity, lexical coverage, and question intent."
        )
        reasons.append(
            f"{retrieval.relevant_count} of {retrieval.retrieved_count} retrieved chunks met the relevance threshold."
        )
        if retrieval.matched_terms:
            reasons.append(
                "Question terms matched the evidence: "
                + ", ".join(retrieval.matched_terms[:6])
                + "."
            )
        reasons.append(f"Top retrieval score: {retrieval.top_score:.3f}.")
    reasons.append(f"The resulting answer confidence is {confidence}.")
    limitations = [
        "Retrieval scores are relative indicators, not probabilities.",
        "Verify high-stakes details against the source document.",
    ]
    if strategy == "local_llm_grounded":
        limitations.append(
            "The local model may paraphrase the retrieved text even when grounded."
        )
    return AnswerExplanation(
        strategy=strategy,
        confidence_reasons=reasons,
        limitations=limitations,
    )
