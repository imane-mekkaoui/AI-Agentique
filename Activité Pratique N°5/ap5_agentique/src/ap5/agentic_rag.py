from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ap5.llm import modele_ollama
from ap5.rag import rag_multimodal


@tool
def retriever_tool(question: str, image_ref: str = "") -> str:
    """Recherche dans les manuels (texte + figures)."""
    return rag_multimodal(question, image_ref=image_ref.strip() or None)


class EtatRAG(TypedDict, total=False):
    messages: list[Any]


def construire_graphe_rag():
    outils = [retriever_tool]
    llm = modele_ollama().bind_tools(outils)

    def agent(etat: EtatRAG) -> dict:
        messages = etat["messages"]
        systeme = SystemMessage(
            content=(
                "Tu es un chatbot RAG agentique. Appelle retriever_tool avant "
                "de répondre. Cite les sources. Réponds en français."
            )
        )
        sortie = llm.invoke([systeme, *messages])
        return {"messages": [sortie]}

    graphe = StateGraph(EtatRAG)
    graphe.add_node("agent", agent)
    graphe.add_node("tools", ToolNode(outils))
    graphe.add_edge(START, "agent")
    graphe.add_conditional_edges("agent", tools_condition)
    graphe.add_edge("tools", "agent")
    return graphe.compile()


graphe = construire_graphe_rag()
