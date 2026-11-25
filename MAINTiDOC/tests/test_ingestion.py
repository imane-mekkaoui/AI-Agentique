"""Tests d'extraction et de découpage."""

from __future__ import annotations

from pathlib import Path

from maintidoc.ingestion.chunking import passages_from_pages
from maintidoc.ingestion.pdf_extract import extract_pages
from maintidoc.models import AccessLevel, DocumentRecord


def test_extract_pages_contains_expected_text(fixture_dir: Path) -> None:
    pages = extract_pages(fixture_dir / "secheur_securite_public.pdf")
    assert len(pages) == 1
    assert pages[0].page == 1
    assert "SD-100" in pages[0].text
    assert "8 bar" in pages[0].text


def test_chunking_keeps_page_and_hash(fixture_dir: Path) -> None:
    record = DocumentRecord(
        document_id="FIX-SEC-001",
        title="Procédure SD-100",
        version="1.0",
        equipment_family="pompes",
        access_level=AccessLevel.PUBLIC,
        filename="secheur_securite_public.pdf",
    )
    pages = extract_pages(fixture_dir / record.filename)
    passages = passages_from_pages(record, [(p.page, p.text) for p in pages], 800, 120)
    assert passages
    assert all(p.page == 1 for p in passages)
    assert all(len(p.content_hash) == 64 for p in passages)
    assert any("alimentation électrique" in p.text or "alimentation" in p.text for p in passages)


def test_document_record_roundtrip() -> None:
    rec = DocumentRecord(
        document_id="X",
        title="T",
        version="1",
        equipment_family="pompes",
        access_level="public",
        filename="a.pdf",
    )
    assert rec.document_id == "X"
