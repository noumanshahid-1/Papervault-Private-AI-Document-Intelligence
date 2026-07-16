"""Smoke tests for the Phase 0 project scaffold."""

import importlib


MODULES = [
    "app.config",
    "app.main",
    "app.models.schemas",
    "app.services.document_loader",
    "app.services.text_extractor",
    "app.services.extraction_quality",
    "app.services.classifier",
    "app.services.chunker",
    "app.services.embeddings",
    "app.services.retrieval_scoring",
    "app.services.vector_store",
    "app.services.llm_adapter",
    "app.services.intelligence_runtime",
    "app.services.insight_engine",
    "app.services.official_notice_engine",
    "app.services.checklist_engine",
    "app.services.qa_engine",
    "app.storage.database",
    "app.utils.text_cleaning",
]


def test_core_modules_import() -> None:
    """All public Phase 0 modules should import without side effects."""
    for module_name in MODULES:
        assert importlib.import_module(module_name)


def test_fastapi_app_health_metadata() -> None:
    """The backend app should expose basic project metadata."""
    from app.main import app

    assert app.title == "Papervault"
