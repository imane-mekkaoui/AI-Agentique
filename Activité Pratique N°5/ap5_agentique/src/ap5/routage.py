from __future__ import annotations

import unicodedata

MOTS_GARANTIE = {
    "garantie",
    "garanties",
    "serie",
    "serial",
    "numero",
    "nserie",
}


def _ascii(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte.casefold())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def classer_demande(question: str, photo: str | None = None) -> str:
    """Une seule catégorie : documentation ou garantie."""
    texte = _ascii(question)
    if photo:
        return "documentation"
    if "garantie" in texte or "numero de serie" in texte or "n de serie" in texte:
        return "garantie"
    if any(mot in texte.split() for mot in MOTS_GARANTIE) and "px" in texte:
        return "garantie"
    if "garantie" in texte:
        return "garantie"
    return "documentation"
