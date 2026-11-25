"""Recherche de passages filtrée par rôle."""

from __future__ import annotations

import re

from qdrant_client import QdrantClient

from maintidoc.access import allowed_levels
from maintidoc.config import Settings, get_settings
from maintidoc.embeddings import EmbeddingClient
from maintidoc.ingestion.clip_describe import ClipDescriber
from maintidoc.models import Passage, UserRole
from maintidoc.rag.rerank import fuse_passages, rerank
from maintidoc.vectorstore import search

MIN_PASSAGE_CHARS = 220
COVER_OVERFETCH = 4
VISUAL_RE = re.compile(
    r"\b(figure|schema|schéma|photo|image|drawing|show|affiche|exploded|diagram)\b",
    re.I,
)
LED_QUESTION = re.compile(
    r"voyant|voiant|voient|led|indicateur|warning light|status light",
    re.I,
)
LED_PASSAGE = re.compile(
    r"voyant|led\b|indicator|warning light|status light|lampe|lmp",
    re.I,
)


def _keywords(question: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]{2,}", question.upper())
    stop = {"HOW", "DO", "I", "THE", "A", "AN", "FOR", "AND", "TO", "OF", "IN", "ON", "SHOW"}
    return {token for token in tokens if token not in stop}


def _rank(question: str, passages: list[Passage]) -> list[Passage]:
    keys = _keywords(question)
    scored: list[tuple[int, int, Passage]] = []
    for passage in passages:
        if passage.modality != "image" and len(passage.text) < MIN_PASSAGE_CHARS:
            continue
        haystack = f"{passage.document_id} {passage.title} {passage.text[:400]}".upper()
        overlap = sum(1 for key in keys if key in haystack)
        scored.append((overlap, len(passage.text), passage))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in scored]


def _filtre_voyant(question: str, passages: list[Passage]) -> list[Passage]:
    """Si la question porte sur un voyant, écarte les schémas électriques hors sujet."""
    if not LED_QUESTION.search(question):
        return passages
    return [p for p in passages if LED_PASSAGE.search(p.text)]


def _dedupe(passages: list[Passage]) -> list[Passage]:
    seen: set[str] = set()
    unique: list[Passage] = []
    for passage in passages:
        key = passage.content_hash + passage.document_id + str(passage.page)
        if key in seen:
            continue
        seen.add(key)
        unique.append(passage)
    return unique


class PassageRetriever:
    """Retrieves passages visibles pour le rôle, uniquement."""

    def __init__(
        self,
        client: QdrantClient,
        collection: str,
        embeddings: EmbeddingClient,
        k: int,
        clip_collection: str | None = None,
        clip: ClipDescriber | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.client = client
        self.collection = collection
        self.embeddings = embeddings
        self.k = k
        self.clip_collection = clip_collection
        self.clip = clip
        self.settings = settings or get_settings()

    def retrieve(
        self,
        question: str,
        role: UserRole,
        *,
        photo_vector: list[float] | None = None,
        photo_caption: str | None = None,
    ) -> list[Passage]:
        """Filtre les droits, fusionne texte BGE + CLIP, puis rerank."""
        levels = list(allowed_levels(role))
        vector = self.embeddings.embed([question], is_query=True)[0]
        raw = search(
            client=self.client,
            collection=self.collection,
            query_vector=vector,
            allowed_levels=levels,
            limit=max(self.k * COVER_OVERFETCH, 16),
        )
        ranked = _rank(question, raw)
        clip_hits: list[Passage] = []
        query_for_clip = photo_caption or question
        clip_vec = photo_vector
        if clip_vec is None and self.clip is not None:
            clip_vec = self.clip.encode_texts([query_for_clip])[0]
        if clip_vec is not None and self.clip_collection:
            clip_hits = search(
                client=self.client,
                collection=self.clip_collection,
                query_vector=clip_vec,
                allowed_levels=levels,
                limit=8,
            )
        if VISUAL_RE.search(question) or photo_vector is not None:
            img_query = f"Figure coupling alignment pump motor shaft {question}"
            img_vector = self.embeddings.embed([img_query], is_query=True)[0]
            images = search(
                client=self.client,
                collection=self.collection,
                query_vector=img_vector,
                allowed_levels=levels,
                limit=8,
                modality="image",
            )
            doc_ids = {p.document_id for p in ranked[:4]}
            near = [p for p in images if p.document_id in doc_ids] or images
            text_hits = [p for p in ranked if p.modality != "image"]
            n_img = min(3, max(2, self.k // 2))
            fused = fuse_passages(near[:n_img], clip_hits, text_hits, limit=self.k * 3)
        else:
            fused = fuse_passages(ranked, clip_hits, limit=self.k * 3)
        fused = _dedupe(fused)
        query = question if not photo_caption else f"{question} {photo_caption}"
        reranked = rerank(
            query,
            fused,
            mode=self.settings.reranker_mode,
            base_model=self.settings.reranker_model,
            adapted_path=self.settings.reranker_adapted_path,
        )
        return _filtre_voyant(question, reranked)[: self.k]
