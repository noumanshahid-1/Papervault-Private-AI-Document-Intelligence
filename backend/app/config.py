"""Application configuration for the local-first Papervault runtime."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or .env files."""

    app_name: str = "Papervault"
    data_dir: Path = Field(default=Path(".docsense_data"), alias="DOCUSENSE_DATA_DIR")
    store_extracted_text: bool = Field(
        default=False,
        alias="PAPERVAULT_STORE_EXTRACTED_TEXT",
    )
    local_llm_enabled: bool = Field(default=False, alias="LOCAL_LLM_ENABLED")
    local_llm_base_url: str = Field(
        default="http://localhost:11434", alias="LOCAL_LLM_BASE_URL"
    )
    local_llm_model: str = Field(default="llama3.2", alias="LOCAL_LLM_MODEL")
    local_llm_timeout: float = Field(default=30.0, alias="LOCAL_LLM_TIMEOUT")
    local_llm_discovery_timeout: float = Field(
        default=2.0,
        alias="LOCAL_LLM_DISCOVERY_TIMEOUT",
    )
    local_embedding_provider: str = Field(
        default="hashing",
        alias="LOCAL_EMBEDDING_PROVIDER",
    )
    local_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="LOCAL_EMBEDDING_MODEL",
    )
    local_retrieval_min_score: float = Field(
        default=0.08,
        alias="LOCAL_RETRIEVAL_MIN_SCORE",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return cached local runtime settings."""
    return Settings()
