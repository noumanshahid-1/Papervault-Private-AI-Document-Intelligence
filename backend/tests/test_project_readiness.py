"""Repository readiness checks for GitHub presentation."""

from pathlib import Path


PROHIBITED_REQUIREMENT_FRAGMENTS = {
    "openai",
    "anthropic",
    "google-generative",
    "gemini",
    "cohere",
    "pinecone",
    "weaviate",
}


def test_requirements_do_not_include_hosted_ai_sdks() -> None:
    requirements = Path("requirements.txt").read_text(encoding="utf-8").lower()

    for fragment in PROHIBITED_REQUIREMENT_FRAGMENTS:
        assert fragment not in requirements


def test_gitignore_protects_local_runtime_and_private_files() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    for pattern in [
        ".env",
        ".docsense_data/",
        "uploads/",
        "uploaded_documents/",
        "vector_store/",
        "*.sqlite3",
    ]:
        assert pattern in gitignore


def test_readme_contains_github_readiness_sections() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for heading in [
        "## Setup",
        "## Endpoints",
        "## Privacy",
        "## Optional local model",
        "## Data location",
    ]:
        assert heading in readme


def test_requirements_do_not_include_removed_streamlit_stack() -> None:
    requirements = Path("requirements.txt").read_text(encoding="utf-8").lower()

    assert "streamlit" not in requirements
    assert "httpx2" not in requirements
    assert "httpx" in requirements
