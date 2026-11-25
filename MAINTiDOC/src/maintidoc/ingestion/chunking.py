"""Découpage des pages en passages avec chevauchement et hash."""

from __future__ import annotations

import hashlib
import re

from maintidoc.models import DocumentRecord, Passage


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_window(text: str, size: int, overlap: int) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    if len(words) <= size:
        return [" ".join(words)]
    step = max(size - overlap, 1)
    chunks: list[str] = []
    start = 0
    while start < len(words):
        piece = words[start : start + size]
        chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
        start += step
    return chunks


def passages_from_pages(
    record: DocumentRecord,
    pages: list[tuple[int, str]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Passage]:
    """Construit les passages indexables à partir des pages extraites."""
    results: list[Passage] = []
    for page_number, page_text in pages:
        cleaned = " ".join(page_text.split())
        if not cleaned:
            continue
        for chunk in _split_window(cleaned, chunk_size, chunk_overlap):
            results.append(
                Passage(
                    document_id=record.document_id,
                    title=record.title,
                    version=record.version,
                    page=page_number,
                    equipment_family=record.equipment_family,
                    access_level=record.access_level,
                    content_hash=_hash_text(chunk),
                    text=chunk,
                )
            )
    return results
