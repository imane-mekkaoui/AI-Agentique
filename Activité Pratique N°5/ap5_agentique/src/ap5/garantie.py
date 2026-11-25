from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
REGISTRE = RACINE / "data" / "registre_garantie.json"


def charger_registre() -> dict:
    return json.loads(REGISTRE.read_text(encoding="utf-8"))


def extraire_numero_serie(texte: str) -> str | None:
    match = re.search(r"\bPX\d{3}-\d{4}\b", texte, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def consulter_garantie(numero_serie: str, aujourdhui: date | None = None) -> str:
    """Interroge le registre SAV en lecture seule."""
    jour = aujourdhui or date.today()
    fiche = charger_registre().get(numero_serie.strip().upper())
    if not fiche:
        return (
            f"Numéro {numero_serie} introuvable dans le registre. "
            "Vérifiez le format (ex. PX200-0042)."
        )
    fin = date.fromisoformat(fiche["fin_garantie"])
    statut = "sous_garantie" if jour <= fin else "expiree"
    return (
        f"Modèle {fiche['modele']} — client {fiche['client']}. "
        f"Achat {fiche['date_achat']}, durée {fiche['duree_mois']} mois, "
        f"fin de garantie {fiche['fin_garantie']}. Statut : {statut}."
    )
