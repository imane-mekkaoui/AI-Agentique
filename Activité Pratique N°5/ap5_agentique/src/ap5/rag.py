from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
MANUEL = RACINE / "data" / "manuels" / "px200.md"
FIGURES = RACINE / "data" / "figures.json"


def _normaliser(texte: str) -> set[str]:
    nfkd = unicodedata.normalize("NFKD", texte.casefold())
    ascii_txt = "".join(c for c in nfkd if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", ascii_txt))


def charger_passages() -> list[dict]:
    texte = MANUEL.read_text(encoding="utf-8")
    blocs = [b.strip() for b in re.split(r"\n(?=## )", texte) if b.strip()]
    passages = []
    for i, bloc in enumerate(blocs, start=1):
        passages.append(
            {
                "type": "texte",
                "id": f"px200-sec-{i}",
                "contenu": bloc,
            }
        )
    figures = json.loads(FIGURES.read_text(encoding="utf-8"))
    for fig in figures:
        passages.append(
            {
                "type": "figure",
                "id": fig["id"],
                "contenu": (
                    f"Figure {fig['id']} ({fig['modele']}) : {fig['legende']} "
                    f"Action : {fig['action']}"
                ),
            }
        )
    return passages


def rag_multimodal(question: str, image_ref: str | None = None, k: int = 4) -> str:
    """Recherche passages et figures du manuel (outil distant MCP)."""
    passages = charger_passages()
    if image_ref:
        cibles = [p for p in passages if p["id"].lower() == image_ref.lower()]
        if cibles:
            extra = [
                p
                for p in passages
                if p["type"] == "texte" and "voyant" in p["contenu"].casefold()
            ]
            choisis = cibles + extra[:2]
            return _formater(choisis, question)

    mots = _normaliser(question)
    scores = []
    for p in passages:
        overlap = len(mots & _normaliser(p["contenu"]))
        if p["type"] == "figure" and "photo" in mots:
            overlap += 2
        scores.append((overlap, p))
    scores.sort(key=lambda x: x[0], reverse=True)
    choisis = [p for s, p in scores if s > 0][:k]
    if not choisis:
        return "Aucun passage pertinent dans les manuels."
    return _formater(choisis, question)


def _formater(passages: list[dict], question: str) -> str:
    lignes = [f"Question : {question}", "Sources :"]
    for i, p in enumerate(passages, start=1):
        lignes.append(f"[{i}] ({p['type']}, {p['id']}) {p['contenu']}")
    return "\n".join(lignes)
