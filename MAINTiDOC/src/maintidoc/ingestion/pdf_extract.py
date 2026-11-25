"""Extraction page par page : PyMuPDF, OCR Tesseract en repli."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pymupdf

logger = logging.getLogger("maintidoc.ingestion")

MIN_TEXT_CHARS = 40
_OCR_READY: bool | None = None


@dataclass(frozen=True)
class PageText:
    """Texte d'une page PDF."""

    page: int
    text: str
    used_ocr: bool


def _tesseract_ready() -> bool:
    """Vérifie une seule fois si Tesseract est réellement utilisable."""
    global _OCR_READY
    if _OCR_READY is not None:
        return _OCR_READY
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        _OCR_READY = True
    except Exception:
        logger.info("ocr_desactive tesseract_absent")
        _OCR_READY = False
    return _OCR_READY


def _ocr_page(page: pymupdf.Page) -> str:
    """Rend la page en image et applique Tesseract si disponible."""
    if not _tesseract_ready():
        return ""
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return pytesseract.image_to_string(image, lang="fra+eng")
    except Exception:
        logger.warning("ocr_echec page=%s", page.number + 1)
        return ""


def extract_pages(pdf_path: Path) -> list[PageText]:
    """Extrait le texte de chaque page, avec OCR si la couche texte est vide."""
    pages: list[PageText] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text = (page.get_text("text") or "").strip()
            used_ocr = False
            if len(text) < MIN_TEXT_CHARS:
                ocr = _ocr_page(page).strip()
                if len(ocr) > len(text):
                    text = ocr
                    used_ocr = True
            pages.append(PageText(page=page.number + 1, text=text, used_ocr=used_ocr))
    logger.info("extraction_ok fichier=%s pages=%s", pdf_path.name, len(pages))
    return pages
