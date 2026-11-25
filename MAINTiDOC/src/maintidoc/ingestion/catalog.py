"""Lecture du catalogue YAML des documents autorisés."""

from __future__ import annotations

from pathlib import Path

import yaml

from maintidoc.models import DocumentRecord


def load_catalog(path: Path) -> list[DocumentRecord]:
    """Charge la liste des documents décrits dans le catalogue."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not payload or "documents" not in payload:
        raise ValueError(f"Catalogue invalide : {path}")
    return [DocumentRecord.model_validate(item) for item in payload["documents"]]


def resolve_pdf(corpus_dir: Path, record: DocumentRecord) -> Path:
    """Retourne le chemin du PDF associé à une entrée de catalogue."""
    pdf = corpus_dir / record.filename
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF introuvable : {pdf}")
    return pdf
