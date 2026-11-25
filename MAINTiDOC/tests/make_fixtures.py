"""Génère les mini-PDF de démonstration / tests."""

from __future__ import annotations

from pathlib import Path

import pymupdf

FIXTURES = {
    "secheur_securite_public.pdf": (
        "Procédure de mise en sécurité du sécheur SD-100 — version 1.0\n\n"
        "Couper l'alimentation électrique avant d'ouvrir le capot du sécheur SD-100.\n"
        "La pression maximale admissible est de 8 bar.\n"
        "Vérifier que le voyant vert est éteint avant toute intervention."
    ),
    "secheur_maintenance_technicien.pdf": (
        "Maintenance technique du sécheur SD-100 — version 2.1 — accès technicien\n\n"
        "Remplacer le filtre déshydrateur toutes les 2000 heures de fonctionnement.\n"
        "Couple de serrage du boulon de bride : 25 N.m.\n"
        "Utiliser uniquement la cartouche référence FIL-SD-100-A."
    ),
    "compresseur_exploitation_public.pdf": (
        "Notice d'exploitation du compresseur CP-40 — version 1.0\n\n"
        "Démarrer le compresseur CP-40 uniquement si la vanne d'aspiration est ouverte.\n"
        "Arrêt d'urgence : appuyer sur le bouton rouge situé en façade.\n"
        "La température d'huile nominale est de 70 degrés Celsius."
    ),
    "compresseur_vanne_superviseur.pdf": (
        "Procédure interne superviseur — vanne de décharge CP-40 — version 3.0\n\n"
        "Le code de déverrouillage de la vanne de décharge est SUPER-LOCK-40.\n"
        "Cette information est réservée aux superviseurs habilités.\n"
        "Après déverrouillage, consigner l'opération dans le registre d'atelier."
    ),
    "hors_sujet_public.pdf": (
        "Recette de cuisine hors périmètre\n\n"
        "Pour réussir un gâteau au chocolat, préchauffer le four à 180 degrés.\n"
        "Ce document n'est pas une procédure de maintenance."
    ),
}


def write_pdf(path: Path, text: str) -> None:
    """Écrit un PDF d'une page contenant le texte fourni."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()


def generate(directory: Path) -> list[Path]:
    """Génère tous les PDF fixtures dans directory."""
    written: list[Path] = []
    for name, text in FIXTURES.items():
        dest = directory / name
        write_pdf(dest, text)
        written.append(dest)
    return written


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate(root / "tests" / "fixtures")
    generate(root / "data" / "corpus")
    print("fixtures générées")
