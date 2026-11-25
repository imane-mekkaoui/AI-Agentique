"""Extraction des figures PDF et passages image."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from maintidoc.models import DocumentRecord, Passage

logger = logging.getLogger("maintidoc.ingestion")

MIN_SIDE = 120
MAX_SIDE = 4000


@dataclass(frozen=True)
class ExtractedImage:
    """Image extraite d'une page PDF."""

    page: int
    path: Path
    width: int
    height: int


def extract_pdf_images(
    pdf_path: Path,
    dest_dir: Path,
    max_images: int = 30,
) -> list[ExtractedImage]:
    """Enregistre les images assez grandes (icônes ignorées)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved: list[ExtractedImage] = []
    document = pymupdf.open(pdf_path)
    try:
        for page in document:
            for index, img in enumerate(page.get_images(full=True)):
                if len(saved) >= max_images:
                    return saved
                xref = img[0]
                try:
                    pix = pymupdf.Pixmap(document, xref)
                    if pix.n - pix.alpha > 3:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    if pix.width < MIN_SIDE or pix.height < MIN_SIDE:
                        continue
                    if pix.width > MAX_SIDE or pix.height > MAX_SIDE:
                        continue
                    out = dest_dir / f"p{page.number + 1}_{index}.png"
                    pix.save(out)
                    saved.append(
                        ExtractedImage(
                            page=page.number + 1,
                            path=out,
                            width=pix.width,
                            height=pix.height,
                        )
                    )
                except Exception:
                    logger.warning(
                        "image_echec fichier=%s page=%s", pdf_path.name, page.number + 1
                    )
    finally:
        document.close()
    logger.info(
        "images_extraites fichier=%s n=%s dest=%s", pdf_path.name, len(saved), dest_dir
    )
    return saved


def passages_from_images(
    record: DocumentRecord,
    images: list[ExtractedImage],
    captions: list[str],
    root: Path,
) -> list[Passage]:
    """Crée un passage par figure (texte = légende CLIP + métadonnée chemin)."""
    results: list[Passage] = []
    for image, caption in zip(images, captions, strict=True):
        try:
            relative = str(image.path.resolve().relative_to(root.resolve()))
        except ValueError:
            relative = str(image.path)
        text = (
            f"Figure page {image.page} ({image.width}x{image.height}). "
            f"Description CLIP : {caption}"
        )
        results.append(
            Passage(
                document_id=record.document_id,
                title=record.title,
                version=record.version,
                page=image.page,
                equipment_family=record.equipment_family,
                access_level=record.access_level,
                content_hash=hashlib.sha256(f"{relative}:{caption}".encode()).hexdigest(),
                text=text,
                modality="image",
                image_path=relative.replace("\\", "/"),
            )
        )
    return results
