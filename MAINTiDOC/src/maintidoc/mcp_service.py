"""Service maintenance simulé (cœur du serveur MCP)."""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
from datetime import date
from pathlib import Path

from maintidoc.config import ROOT, get_settings
from maintidoc.models import UserRole

EQUIPEMENTS = ROOT / "data" / "mcp" / "equipements.json"
TICKETS = ROOT / "data" / "mcp" / "tickets.json"
_LOCK = threading.Lock()

ROLES_TICKET = {UserRole.TECHNICIEN.value, UserRole.SUPERVISEUR.value}


def _secret() -> str:
    return get_settings().mcp_secret


def charger_equipements() -> dict:
    return json.loads(EQUIPEMENTS.read_text(encoding="utf-8"))


def _tickets() -> dict:
    if not TICKETS.is_file():
        return {"ouverts": [], "cles": {}}
    return json.loads(TICKETS.read_text(encoding="utf-8"))


def _sauver(data: dict) -> None:
    TICKETS.parent.mkdir(parents=True, exist_ok=True)
    TICKETS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def extraire_equipment_id(question: str, fourni: str = "") -> str:
    if fourni.strip():
        return fourni.strip().upper()
    q = question.upper()
    if "FC" in q and "302" in q:
        return "VLT-FC302-01"
    if "NK" in q:
        return "GF-NK-01"
    if "SD-100" in q or "SD100" in q or "SECHEUR" in q or "SÉCHEUR" in q:
        return "SD-100"
    return "VLT-FC302-01"


def jeton_approbation(
    user_id: str,
    role: str,
    equipment_id: str,
    title: str,
    description: str,
) -> str:
    corps = "|".join([user_id, role, equipment_id, title.strip(), description.strip()])
    digest = hashlib.sha256((_secret() + corps).encode()).hexdigest()
    return f"{user_id}:{role}:{digest}"


def verifier_jeton(
    token: str,
    equipment_id: str,
    title: str,
    description: str,
) -> tuple[str, str]:
    try:
        user_id, role, digest = token.split(":", 2)
    except ValueError as exc:
        raise PermissionError("Jeton d'approbation mal formé.") from exc
    attendu = jeton_approbation(user_id, role, equipment_id, title, description)
    if not hmac.compare_digest(token, attendu):
        raise PermissionError("Jeton d'approbation invalide (contenu ou utilisateur).")
    if role not in ROLES_TICKET:
        raise PermissionError("L'opérateur ne peut pas créer de ticket.")
    return user_id, role


def get_equipment_history(equipment_id: str) -> str:
    """Historique d'interventions (lecture)."""
    fiche = charger_equipements().get(equipment_id)
    if not fiche:
        return f"Équipement {equipment_id} inconnu du GMAO de démo."
    lignes = [f"{fiche['modele']} — {fiche['site']}"]
    for ev in fiche.get("historique", []):
        lignes.append(f"- {ev['date']} [{ev['type']}] {ev['texte']}")
    return "\n".join(lignes)


def get_open_tickets(equipment_id: str) -> str:
    """Tickets encore ouverts pour cet équipement."""
    with _LOCK:
        data = _tickets()
    ouverts = [t for t in data["ouverts"] if t["equipment_id"] == equipment_id]
    if not ouverts:
        return f"Aucun ticket ouvert pour {equipment_id}."
    return "\n".join(
        f"- {t['id']} [{t['statut']}] {t['title']} (par {t['user_id']})"
        for t in ouverts
    )


def create_ticket(
    equipment_id: str,
    title: str,
    description: str,
    approval_token: str,
) -> str:
    """Crée le ticket seulement si le jeton correspond au contenu exact."""
    user_id, role = verifier_jeton(approval_token, equipment_id, title, description)
    cle = hashlib.sha256(
        f"{equipment_id}|{title.strip()}|{description.strip()}".encode()
    ).hexdigest()
    with _LOCK:
        data = _tickets()
        if cle in data["cles"]:
            existant = data["cles"][cle]
            return f"Idempotence : ticket déjà créé ({existant})."
        ident = f"TCK-{len(data['ouverts']) + 1:04d}"
        ticket = {
            "id": ident,
            "equipment_id": equipment_id,
            "title": title.strip(),
            "description": description.strip(),
            "user_id": user_id,
            "role": role,
            "statut": "ouvert",
            "date": date.today().isoformat(),
        }
        data["ouverts"].append(ticket)
        data["cles"][cle] = ident
        _sauver(data)
    return f"Ticket {ident} créé pour {equipment_id} par {user_id}."
