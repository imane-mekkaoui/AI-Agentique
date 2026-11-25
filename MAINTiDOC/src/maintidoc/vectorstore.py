"""Index Qdrant : création de collection et upsert des passages."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from maintidoc.embeddings import DEFAULT_EMBEDDING_DIM
from maintidoc.models import AccessLevel, Passage

PAYLOAD_FIELDS = (
    "document_id",
    "title",
    "version",
    "page",
    "equipment_family",
    "access_level",
    "content_hash",
    "text",
    "modality",
    "image_path",
)


def connect(url: str) -> QdrantClient:
    """Client Qdrant HTTP."""
    return QdrantClient(url=url, check_compatibility=False)


def ensure_collection(
    client: QdrantClient, name: str, vector_size: int = DEFAULT_EMBEDDING_DIM
) -> None:
    """Crée ou recrée la collection (cosine) si la dimension ne correspond pas."""
    existing = {c.name for c in client.get_collections().collections}
    if name in existing:
        info = client.get_collection(name)
        vectors = info.config.params.vectors
        current = getattr(vectors, "size", None)
        if current == vector_size:
            return
        client.delete_collection(name)
    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
    )


def _point_id(passage: Passage) -> str:
    return str(uuid5(NAMESPACE_URL, passage.content_hash + passage.document_id + str(passage.page)))


def upsert_passages(
    client: QdrantClient,
    collection: str,
    passages: Sequence[Passage],
    vectors: Sequence[Sequence[float]],
) -> int:
    """Indexe les passages avec leurs métadonnées en payload."""
    if len(passages) != len(vectors):
        raise ValueError("passages et vecteurs de longueurs différentes")
    points = [
        qm.PointStruct(
            id=_point_id(passage),
            vector=list(vector),
            payload=passage.model_dump(mode="json"),
        )
        for passage, vector in zip(passages, vectors, strict=True)
    ]
    client.upsert(collection_name=collection, points=points)
    return len(points)


def search(
    client: QdrantClient,
    collection: str,
    query_vector: Sequence[float],
    allowed_levels: Sequence[AccessLevel],
    limit: int,
    modality: str | None = None,
) -> list[Passage]:
    """Recherche dense filtrée par droits d'accès (avant génération)."""
    if not allowed_levels:
        return []
    values = [level.value for level in allowed_levels]
    must: list[qm.FieldCondition] = []
    if modality:
        must.append(
            qm.FieldCondition(key="modality", match=qm.MatchValue(value=modality))
        )
    results = client.query_points(
        collection_name=collection,
        query=list(query_vector),
        query_filter=qm.Filter(
            should=[
                qm.FieldCondition(
                    key="access_level",
                    match=qm.MatchValue(value=value),
                )
                for value in values
            ],
            must=must or None,
        ),
        limit=limit,
        with_payload=True,
    )
    passages: list[Passage] = []
    for hit in results.points:
        payload = hit.payload or {}
        raw = {key: payload.get(key) for key in PAYLOAD_FIELDS}
        if not raw.get("modality"):
            raw["modality"] = "text"
        passages.append(Passage.model_validate(raw))
    return passages
