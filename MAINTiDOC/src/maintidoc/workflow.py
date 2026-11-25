"""Graphe LangGraph étape 3 : historique MCP + brouillon + HITL + create_ticket."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from maintidoc.mcp_client import appeler
from maintidoc.mcp_service import extraire_equipment_id, jeton_approbation
from maintidoc.models import UserRole

SAUVEGARDE = MemorySaver()


class EtatWorkflow(TypedDict, total=False):
    question: str
    user_id: str
    role: str
    equipment_id: str
    historique: str
    tickets_ouverts: str
    draft_title: str
    draft_description: str
    approval_token: str
    decision: str
    ticket: str
    message: str


def nœud_equipement(etat: EtatWorkflow) -> dict[str, Any]:
    eid = extraire_equipment_id(etat["question"], etat.get("equipment_id") or "")
    return {"equipment_id": eid}


def nœud_historique(etat: EtatWorkflow) -> dict[str, Any]:
    hist = appeler("get_equipment_history", equipment_id=etat["equipment_id"])
    ouverts = appeler("get_open_tickets", equipment_id=etat["equipment_id"])
    return {"historique": hist, "tickets_ouverts": ouverts}


def nœud_brouillon(etat: EtatWorkflow) -> dict[str, Any]:
    eid = etat["equipment_id"]
    title = f"Contrôle {eid} — {etat['question'][:60]}"
    description = (
        f"Demandeur : {etat['user_id']} ({etat['role']})\n"
        f"Question : {etat['question']}\n\n"
        f"Historique GMAO :\n{etat.get('historique', '')}\n\n"
        f"Tickets ouverts :\n{etat.get('tickets_ouverts', '')}"
    )
    token = jeton_approbation(
        etat["user_id"], etat["role"], eid, title, description
    )
    return {
        "draft_title": title,
        "draft_description": description,
        "approval_token": token,
        "message": "Brouillon prêt. Approbation humaine requise.",
    }


def nœud_hitl(etat: EtatWorkflow) -> dict[str, Any]:
    """Interrompt le graphe jusqu'à approve / refuse."""
    payload = interrupt(
        {
            "equipment_id": etat["equipment_id"],
            "title": etat["draft_title"],
            "description": etat["draft_description"],
            "approval_token": etat["approval_token"],
            "user_id": etat["user_id"],
        }
    )
    if isinstance(payload, dict):
        return {"decision": "approve" if payload.get("approved") else "refuse"}
    return {"decision": "approve" if payload else "refuse"}


def nœud_creer(etat: EtatWorkflow) -> dict[str, Any]:
    if etat.get("decision") != "approve":
        return {"ticket": "", "message": "Création annulée (pas d'approbation)."}
    try:
        resultat = appeler(
            "create_ticket",
            equipment_id=etat["equipment_id"],
            title=etat["draft_title"],
            description=etat["draft_description"],
            approval_token=etat["approval_token"],
        )
        return {"ticket": resultat, "message": resultat}
    except PermissionError as exc:
        return {"ticket": "", "message": str(exc)}


def nœud_lecture(etat: EtatWorkflow) -> dict[str, Any]:
    return {
        "message": (
            "Rôle opérateur : consultation uniquement, pas de ticket.\n"
            f"{etat.get('historique', '')}\n{etat.get('tickets_ouverts', '')}"
        )
    }


def aiguiller(etat: EtatWorkflow) -> Literal["brouillon", "lecture"]:
    if etat.get("role") == UserRole.OPERATEUR.value:
        return "lecture"
    return "brouillon"


def construire_graphe():
    graphe = StateGraph(EtatWorkflow)
    graphe.add_node("equipement", nœud_equipement)
    graphe.add_node("historique", nœud_historique)
    graphe.add_node("brouillon", nœud_brouillon)
    graphe.add_node("hitl", nœud_hitl)
    graphe.add_node("creer", nœud_creer)
    graphe.add_node("lecture", nœud_lecture)
    graphe.add_edge(START, "equipement")
    graphe.add_edge("equipement", "historique")
    graphe.add_conditional_edges(
        "historique",
        aiguiller,
        {"brouillon": "brouillon", "lecture": "lecture"},
    )
    graphe.add_edge("brouillon", "hitl")
    graphe.add_edge("hitl", "creer")
    graphe.add_edge("creer", END)
    graphe.add_edge("lecture", END)
    return graphe.compile(checkpointer=SAUVEGARDE)


graphe = construire_graphe()
