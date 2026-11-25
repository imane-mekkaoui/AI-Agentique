"""Graphe pédagogique : nœuds, arêtes, aiguillage."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class Etat(TypedDict):
    texte: str
    etape: str
    resultat: str


def nœud_accueil(etat: Etat) -> dict:
    return {"etape": "accueil", "resultat": f"Reçu : {etat['texte']}"}


def nœud_majuscules(etat: Etat) -> dict:
    return {"etape": "majuscules", "resultat": etat["texte"].upper()}


def nœud_compter(etat: Etat) -> dict:
    n = len(etat["texte"].split())
    return {"etape": "compter", "resultat": f"{n} mot(s)"}


def aiguiller(etat: Etat) -> Literal["majuscules", "compter"]:
    if etat["texte"].isupper() or "compte" in etat["texte"].casefold():
        return "compter"
    return "majuscules"


def construire_graphe_bases():
    graphe = StateGraph(Etat)
    graphe.add_node("accueil", nœud_accueil)
    graphe.add_node("majuscules", nœud_majuscules)
    graphe.add_node("compter", nœud_compter)
    graphe.add_edge(START, "accueil")
    graphe.add_conditional_edges(
        "accueil",
        aiguiller,
        {"majuscules": "majuscules", "compter": "compter"},
    )
    graphe.add_edge("majuscules", END)
    graphe.add_edge("compter", END)
    return graphe.compile()


graphe = construire_graphe_bases()
