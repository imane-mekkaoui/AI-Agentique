from __future__ import annotations

from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from ap5.garantie import consulter_garantie, extraire_numero_serie
from ap5.llm import modele_ollama
from ap5.rag import rag_multimodal
from ap5.routage import classer_demande

Categorie = Literal["documentation", "garantie"]


class EtatSAV(TypedDict, total=False):
    question: str
    photo: str
    categorie: Categorie
    agent: str
    observation: str
    reponse: str


@tool
def consulter_garantie_tool(numero_serie: str) -> str:
    """Registre SAV local, lecture seule."""
    return consulter_garantie(numero_serie)


def node_orchestrateur(etat: EtatSAV) -> dict[str, Any]:
    if etat.get("reponse"):
        return {}
    categorie = classer_demande(etat.get("question", ""), etat.get("photo") or None)
    agent = "agent_documentaire" if categorie == "documentation" else "agent_garantie"
    return {"categorie": categorie, "agent": agent}


def node_documentaire(etat: EtatSAV) -> dict[str, Any]:
    photo = (etat.get("photo") or "").strip() or None
    observation = rag_multimodal(etat["question"], image_ref=photo)
    llm = modele_ollama()
    resultat = llm.invoke(
        [
            SystemMessage(
                content=(
                    "Tu es l'agent documentaire SAV. Réponds en français "
                    "uniquement à partir de l'observation RAG. Cite les ids "
                    "de sources ([1], img_px200_01, …)."
                )
            ),
            HumanMessage(content=observation),
        ]
    )
    return {
        "observation": observation,
        "reponse": resultat.content.strip(),
        "agent": "agent_documentaire",
    }


def node_garantie(etat: EtatSAV) -> dict[str, Any]:
    numero = extraire_numero_serie(etat["question"])
    if not numero:
        observation = "Aucun numéro de série au format PX000-0000 dans la demande."
    else:
        observation = consulter_garantie_tool.invoke({"numero_serie": numero})
    llm = modele_ollama()
    resultat = llm.invoke(
        [
            SystemMessage(
                content=(
                    "Tu es l'agent garantie. Réponds clairement à partir de "
                    "l'observation du registre. N'invente pas de numéro."
                )
            ),
            HumanMessage(
                content=f"Question : {etat['question']}\nObservation : {observation}"
            ),
        ]
    )
    return {
        "observation": observation,
        "reponse": resultat.content.strip(),
        "agent": "agent_garantie",
    }


def aiguillage(etat: EtatSAV) -> str:
    if etat.get("reponse"):
        return "fin"
    if etat.get("categorie") == "garantie":
        return "garantie"
    return "documentation"


def construire_graphe_sav():
    graphe = StateGraph(EtatSAV)
    graphe.add_node("orchestrateur", node_orchestrateur)
    graphe.add_node("depanneur", node_documentaire)
    graphe.add_node("verificateur", node_garantie)
    graphe.add_edge(START, "orchestrateur")
    graphe.add_conditional_edges(
        "orchestrateur",
        aiguillage,
        {
            "documentation": "depanneur",
            "garantie": "verificateur",
            "fin": END,
        },
    )
    graphe.add_edge("depanneur", "orchestrateur")
    graphe.add_edge("verificateur", "orchestrateur")
    return graphe.compile()


graphe = construire_graphe_sav()
