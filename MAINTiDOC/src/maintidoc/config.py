"""Configuration chargée depuis l'environnement (fichier .env)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Paramètres runtime de MAINTiDOC."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "maintidoc_passages"
    qdrant_clip_collection: str = "maintidoc_clip_images"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_device: str = "cpu"

    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "qwen2.5:3b"
    llm_api_key: str = "ollama"
    vlm_model: str = "qwen2.5vl:3b"
    ollama_url: str = "http://127.0.0.1:11434"

    reranker_mode: str = "base"
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    reranker_adapted_path: Path = ROOT / "models" / "reranker-adapted"

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_k: int = 5

    catalog_path: Path = ROOT / "data" / "catalog.yaml"
    corpus_dir: Path = ROOT / "data" / "corpus"
    images_dir: Path = ROOT / "data" / "extracted_images"
    clip_model: str = "clip-ViT-B-32"
    max_images_per_doc: int = 30
    mcp_url: str = "http://127.0.0.1:8767/mcp"
    mcp_secret: str = "maintidoc-dev-secret"

    def resolve_images(self) -> Path:
        path = Path(self.images_dir)
        return path if path.is_absolute() else ROOT / path

    def resolve_catalog(self) -> Path:
        path = Path(self.catalog_path)
        return path if path.is_absolute() else ROOT / path

    def resolve_corpus(self) -> Path:
        path = Path(self.corpus_dir)
        return path if path.is_absolute() else ROOT / path

    log_level: str = "INFO"


def get_settings() -> Settings:
    """Retourne les settings (nouvelle instance, utile pour les tests)."""
    return Settings()
