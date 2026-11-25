"""Passages image : chemin en métadonnée."""

from __future__ import annotations

from pathlib import Path

from maintidoc.ingestion.images import ExtractedImage, passages_from_images
from maintidoc.models import AccessLevel, DocumentRecord
from maintidoc.rag.chain import passages_to_citations


def test_image_passage_keeps_relative_path(tmp_path: Path) -> None:
    image = tmp_path / "fig.png"
    image.write_bytes(b"fake")
    record = DocumentRecord(
        document_id="GF-NK-IEC-001",
        title="NK",
        version="1",
        equipment_family="pompes",
        access_level=AccessLevel.PUBLIC,
        filename="nk.pdf",
    )
    extracted = [ExtractedImage(page=12, path=image, width=400, height=300)]
    passages = passages_from_images(record, extracted, ["pump installation drawing"], tmp_path)
    assert len(passages) == 1
    assert passages[0].modality == "image"
    assert passages[0].page == 12
    assert passages[0].image_path == "fig.png"
    cite = passages_to_citations(passages)[0]
    assert cite.image_path == "fig.png"
    assert cite.modality == "image"
