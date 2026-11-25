"""Embeddings via sentence-transformers (BGE-small par défaut, CPU)."""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_DIM = 384
BGE_M3_DIM = DEFAULT_EMBEDDING_DIM
logger = logging.getLogger("maintidoc.embeddings")


class EmbeddingClient:
    """Encode des textes avec le modèle d'embedding configuré."""

    def __init__(self, model_name: str, device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        logger.info("chargement_modele name=%s device=%s", model_name, device)
        self._model = SentenceTransformer(model_name, device=device)
        dim = self._model.get_embedding_dimension()
        self.dim = int(dim or DEFAULT_EMBEDDING_DIM)
        logger.info("modele_pret name=%s dim=%s", model_name, self.dim)

    def embed(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        """Retourne une liste de vecteurs dense."""
        payload = texts
        if is_query:
            payload = [
                f"Represent this sentence for searching relevant passages: {text}"
                for text in texts
            ]
        logger.info("encodage_debut n=%s query=%s", len(payload), is_query)
        vectors = self._model.encode(
            payload,
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        logger.info("encodage_ok n=%s", len(texts))
        return [row.tolist() for row in vectors]


@lru_cache(maxsize=1)
def get_embedding_client(model_name: str, device: str) -> EmbeddingClient:
    """Client singleton pour éviter de recharger le modèle."""
    return EmbeddingClient(model_name, device)
