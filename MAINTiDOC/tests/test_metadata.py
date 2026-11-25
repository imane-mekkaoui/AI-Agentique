"""Les passages conservent toutes les métadonnées exigées."""

from __future__ import annotations

from pathlib import Path

from maintidoc.ingestion.catalog import load_catalog
from maintidoc.ingestion.chunking import passages_from_pages
from maintidoc.ingestion.pdf_extract import extract_pages
from maintidoc.models import AccessLevel, DocumentRecord

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "document_id",
    "title",
    "version",
    "page",
    "equipment_family",
    "access_level",
    "content_hash",
    "text",
}


def test_catalog_has_two_families() -> None:
    records = load_catalog(ROOT / "data" / "catalog.yaml")
    families = {r.equipment_family for r in records}
    assert families == {"pompes", "variateurs"}
    assert any(r.filename.endswith(".pdf") for r in records)
    assert (ROOT / "data" / "corpus" / records[0].filename).is_file()


def test_passage_payload_fields(fixture_dir: Path) -> None:
    record = DocumentRecord(
        document_id="FIX-CMP-002",
        title="Procédure interne superviseur",
        version="3.0",
        equipment_family="variateurs",
        access_level=AccessLevel.SUPERVISEUR,
        filename="compresseur_vanne_superviseur.pdf",
    )
    pages = extract_pages(fixture_dir / record.filename)
    passages = passages_from_pages(record, [(p.page, p.text) for p in pages], 800, 120)
    dumped = passages[0].model_dump()
    assert REQUIRED <= set(dumped)
    assert dumped["access_level"] == "superviseur"
    assert dumped["version"] == "3.0"
    assert dumped["page"] == 1
