"""Tests for local vector retrieval and extractive Q&A fallback."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.chunker import chunk_text
from app.services.embeddings import HashingEmbeddingProvider
from app.services.llm_adapter import LocalLLMResult
from app.services.qa_engine import NOT_FOUND_MESSAGE, answer_question
from app.services.vector_store import LocalVectorStore


DOCUMENT_TEXT = """
Admission Offer Letter

Required documents include passport copy and official transcript.
The acceptance deadline is July 15, 2026.
Students must pay the enrollment deposit of $500 before registration.
Contact admissions@example.edu for questions.
"""


GOVERNMENT_NOTICE_TEXT = """
KHYBER PAKHTUNKHWA REVENUE AUTHORITY NOTIFICATION
Peshawar Dated,the 16 June, 2025.
The liability to pay tax shall be on the person other than the service provider.
Custom House Agents Pakistan Single Window Fixed rate of Rs. 3.000/-per goods declaration.
The person made liable to pay tax shall ensure timely collection and payment of sales tax on services
not later than the 15 day of the following tax period.
Non-payment or short-payment may result in penalty, default surcharge and recovery of tax.
"""


def test_hashing_embeddings_are_deterministic_and_normalized() -> None:
    provider = HashingEmbeddingProvider(dimensions=32)

    first = provider.encode(["passport deadline"])[0]
    second = provider.encode(["passport deadline"])[0]

    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 0.0001


def test_vector_store_retrieves_relevant_chunk() -> None:
    provider = HashingEmbeddingProvider(dimensions=64)
    chunks = chunk_text(DOCUMENT_TEXT, filename="admission.txt", chunk_size=80, chunk_overlap=10)
    store = LocalVectorStore(embedding_provider=provider)
    store.add_chunks(chunks)

    results = store.search("What is the acceptance deadline?", top_k=2)

    assert results
    assert "deadline" in results[0].chunk.text.lower()
    assert results[0].score > 0
    assert results[0].chunk.source_filename == "admission.txt"


def test_vector_store_hybrid_ranking_prefers_intent_evidence() -> None:
    provider = HashingEmbeddingProvider(dimensions=64)
    text = """
    The admissions team reviews each accepted application before registration.

    You must respond to the offer no later than July 15, 2026.
    """
    chunks = chunk_text(
        text,
        filename="offer.txt",
        chunk_size=75,
        chunk_overlap=0,
    )
    store = LocalVectorStore(embedding_provider=provider)
    store.add_chunks(chunks)

    results = store.search("When do I need to accept the offer?", top_k=2)

    assert results
    assert "July 15, 2026" in results[0].chunk.text


def test_answer_question_uses_extractive_fallback_with_snippets() -> None:
    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="What is the acceptance deadline?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "July 15, 2026" in answer.answer
    assert answer.confidence in {"medium", "high"}
    assert answer.source_snippets
    assert answer.mode == "extractive"
    assert answer.retrieval.retrieved_count > 0
    assert answer.retrieval.embedding_provider == "hashing"
    assert answer.explanation.strategy == "direct_rule"
    assert answer.explanation.confidence_reasons


def test_deadline_review_question_returns_date_and_matching_evidence() -> None:
    text = """
    University of Northbridge
    Admission Offer Letter
    Congratulations, you have been admitted to the MSc Data Science program.
    You must accept this offer by July 15, 2026.
    Failure to submit documents by the deadline may delay your enrollment.
    """
    answer = answer_question(
        text=text,
        question="What deadlines should I verify?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "July 15, 2026" in answer.answer
    assert answer.confidence in {"medium", "high"}
    assert answer.source_snippets
    assert "July 15, 2026" in answer.source_snippets[0].text


def test_deadline_question_supports_day_month_year_dates() -> None:
    text = """
    The programme begins on 15 September 2026.
    You must accept this offer through the portal by 15 July 2026.
    Failure to accept by the deadline may cause the place to be withdrawn.
    """

    answer = answer_question(
        text=text,
        question="What is the most important deadline?",
        filename="offer.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "15 July 2026" in answer.answer
    assert answer.explanation.strategy == "direct_rule"


def test_start_date_question_does_not_return_acceptance_deadline() -> None:
    text = """
    The programme begins on 15 September 2026.
    You must accept this offer through the portal by 15 July 2026.
    """

    answer = answer_question(
        text=text,
        question="When does the programme begin?",
        filename="offer.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "15 September 2026" in answer.answer
    assert "15 July 2026" not in answer.answer


def test_paraphrased_deadline_question_returns_response_date() -> None:
    text = """
    The programme begins on 15 September 2026.
    You must respond to the offer no later than 15 July 2026.
    """

    answer = answer_question(
        text=text,
        question="When do I need to respond to the offer?",
        filename="offer.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "15 July 2026" in answer.answer


def test_paperwork_question_returns_required_documents() -> None:
    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="What paperwork should I prepare?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "passport copy" in answer.answer.lower()
    assert "official transcript" in answer.answer.lower()


def test_contact_question_returns_contact_evidence() -> None:
    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="How can I contact admissions?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "admissions@example.edu" in answer.answer


def test_answer_question_returns_not_found_when_context_missing() -> None:
    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="What is the campus housing address?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert answer.answer == NOT_FOUND_MESSAGE
    assert answer.confidence == "low"
    assert answer.source_snippets == []
    assert answer.explanation.strategy == "no_answer"


def test_answer_question_uses_local_llm_when_available() -> None:
    class FakeLLMAdapter:
        def generate(self, prompt: str) -> LocalLLMResult:
            assert "Only use the provided context" in prompt
            assert "Required documents include passport copy" in prompt
            return LocalLLMResult(
                text="The required documents are passport copy and official transcript.",
                available=True,
                model="fake-local-model",
            )

    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="Which documents are required?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
        llm_adapter=FakeLLMAdapter(),
        use_local_llm=True,
    )

    assert "passport copy" in answer.answer.lower()
    assert answer.mode == "local_llm"
    assert answer.source_snippets
    assert answer.generation.actual_mode == "local_llm"
    assert answer.generation.model_used == "fake-local-model"


def test_answer_question_falls_back_when_local_llm_unavailable() -> None:
    class FakeLLMAdapter:
        def generate(self, prompt: str) -> LocalLLMResult:
            return LocalLLMResult(
                text="",
                available=False,
                error="Local LLM unavailable; using extractive mode.",
            )

    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="What is the acceptance deadline?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
        llm_adapter=FakeLLMAdapter(),
        use_local_llm=True,
    )

    assert "July 15, 2026" in answer.answer
    assert answer.mode == "extractive"
    assert answer.generation.fallback_reason


def test_requested_local_model_is_reported_when_backend_falls_back() -> None:
    answer = answer_question(
        text=DOCUMENT_TEXT,
        question="What is the acceptance deadline?",
        filename="admission.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
        answer_mode="local_llm",
        model="qwen2.5:7b",
    )

    assert answer.mode == "extractive"
    assert answer.generation.requested_mode == "local_llm"
    assert answer.generation.configured_model == "qwen2.5:7b"
    assert answer.generation.fallback_reason


def test_ask_endpoint_returns_grounded_answer() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/ask",
        json={
            "text": DOCUMENT_TEXT,
            "question": "Which documents are required?",
            "filename": "admission.txt",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "passport copy" in payload["answer"].lower()
    assert payload["source_snippets"]
    assert payload["mode"] == "extractive"
    assert payload["retrieval"]["retrieved_count"] > 0
    assert payload["generation"]["actual_mode"] == "extractive"
    assert payload["explanation"]["confidence_reasons"]


def test_government_notice_question_answers_common_review_questions() -> None:
    payment_answer = answer_question(
        text=GOVERNMENT_NOTICE_TEXT,
        question="What payments or rates are mentioned?",
        filename="notice.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )
    obligation_answer = answer_question(
        text=GOVERNMENT_NOTICE_TEXT,
        question="What obligations are mentioned?",
        filename="notice.txt",
        embedding_provider=HashingEmbeddingProvider(dimensions=64),
    )

    assert "Rs. 3,000/- per goods declaration" in payment_answer.answer
    assert "collection and payment of sales tax" in obligation_answer.answer
    assert payment_answer.source_snippets
    assert obligation_answer.source_snippets


def test_ask_endpoint_rejects_empty_question() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/ask",
        json={"text": DOCUMENT_TEXT, "question": "   "},
    )

    assert response.status_code == 400
    assert "No question" in response.json()["detail"]
