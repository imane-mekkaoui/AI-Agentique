"""Fusion et reranking (cross-encoder). Modes : off, base, adapted."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from maintidoc.models import Passage

logger = logging.getLogger("maintidoc.rag")


def fuse_passages(*groups: list[Passage], limit: int) -> list[Passage]:
    """Concatène texte + images CLIP en dédoublonnant."""
    seen: set[str] = set()
    merged: list[Passage] = []
    for group in groups:
        for passage in group:
            key = passage.content_hash + passage.document_id + str(passage.page)
            if key in seen:
                continue
            seen.add(key)
            merged.append(passage)
            if len(merged) >= limit:
                return merged
    return merged


def ndcg_at_k(relevances: list[int], k: int = 5) -> float:
    """nDCG@k, relevances 0/1 dans l'ordre classé."""
    import math

    window = relevances[:k]
    dcg = sum((rel / math.log2(i + 2)) for i, rel in enumerate(window))
    ideal = sorted(relevances, reverse=True)[:k]
    idcg = sum((rel / math.log2(i + 2)) for i, rel in enumerate(ideal))
    return (dcg / idcg) if idcg else 0.0


def mrr_at_k(relevances: list[int], k: int = 10) -> float:
    """MRR@k."""
    for i, rel in enumerate(relevances[:k]):
        if rel:
            return 1.0 / (i + 1)
    return 0.0


@lru_cache(maxsize=2)
def _load_cross_encoder(name_or_path: str):
    from sentence_transformers import CrossEncoder

    logger.info("chargement_reranker path=%s", name_or_path)
    return CrossEncoder(name_or_path)


def rerank(
    query: str,
    passages: list[Passage],
    *,
    mode: str = "base",
    base_model: str,
    adapted_path: Path,
) -> list[Passage]:
    """Reclasse les passages. `off` conserve l'ordre de fusion."""
    if mode == "off" or len(passages) <= 1:
        return passages
    path = Path(adapted_path)
    model_id = str(path) if mode == "adapted" and path.exists() else base_model
    if mode == "adapted" and not path.exists():
        logger.warning("reranker_adapte_absent fallback_base")
        model_id = base_model
    encoder = _load_cross_encoder(model_id)
    pairs = [(query, passage.text[:1200]) for passage in passages]
    scores = encoder.predict(pairs, show_progress_bar=False)
    ranked = sorted(zip(scores.tolist(), passages, strict=True), key=lambda x: x[0], reverse=True)
    return [passage for _, passage in ranked]
