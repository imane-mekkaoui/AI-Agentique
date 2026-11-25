"""Incertitude et demande de clarification (sortie structurée)."""

from __future__ import annotations

from maintidoc.models import Passage
from maintidoc.rag.prompts import UNKNOWN

CLARIFY = (
    "Aucun passage du manuel ne décrit ce voyant / cette LED. "
    "Indiquez la page du guide ou envoyez une photo nette du panneau."
)


def is_unknown(answer: str) -> bool:
    texte = answer.strip().casefold()
    return texte == UNKNOWN.casefold() or texte.startswith("je ne sais pas")


def assess(question: str, passages: list[Passage], answer: str) -> tuple[str, str | None]:
    """Retourne (uncertainty, clarification)."""
    if not passages or is_unknown(answer):
        return "high", CLARIFY
    if any(p.modality == "image" for p in passages) and len(passages) <= 2:
        return "medium", None
    if len(question.split()) < 4:
        return "medium", "Vous pouvez préciser l'équipement pour une citation plus ciblée."
    return "low", None
