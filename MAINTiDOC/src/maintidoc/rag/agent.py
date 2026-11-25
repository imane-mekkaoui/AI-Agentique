"""Agent LangChain : le RAG est un tool, pas un retrieve+generate caché."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from maintidoc.models import AskResponse, Passage, UserRole
from maintidoc.rag.chain import passages_to_citations
from maintidoc.rag.prompts import UNKNOWN, format_passages, user_prompt
from maintidoc.rag.retriever import PassageRetriever
from maintidoc.rag.uncertainty import assess, is_unknown

logger = logging.getLogger("maintidoc.rag")

AGENT_PROMPT = """Tu es MAINTiDOC, assistant documentaire pour techniciens de maintenance.
Tu ne pilotes aucune machine et tu ne donnes aucun diagnostic garanti.

Le tool search_manuals a déjà été exécuté. Utilise le TEXTE des extraits pour la procédure.
Les libellés « Description CLIP » sont des tags, pas une description fidèle de la photo :
ne les recopie pas comme s'ils étaient visibles (pas de « pompe centrifuge » inventée).
Si Modalite: image est présent, dis simplement que la figure d'alignement d'accouplement
est affichée sous les sources, puis résume les étapes du texte (règle, couple, marque).
Ne réponds « Je ne sais pas » que si aucun extrait n'a de rapport.
Réponds dans la langue de la question, en 6 phrases maximum.
"""


@dataclass
class AgentMemory:
    """État par requête : rôle et derniers passages du tool RAG."""

    role: UserRole = UserRole.TECHNICIEN
    passages: list[Passage] = field(default_factory=list)


def build_search_tool(retriever: PassageRetriever, memory: AgentMemory) -> StructuredTool:
    """Tool RAG : recherche filtrée par droits, texte + images."""

    def search_manuals(query: str) -> str:
        """Cherche dans les manuels (texte et figures CLIP). À appeler avant de répondre."""
        hits = retriever.retrieve(query, memory.role)
        memory.passages = hits
        logger.info("tool_search_manuals hits=%s", len(hits))
        if not hits:
            return "Aucun passage autorisé pour ce rôle."
        return format_passages(hits)

    return StructuredTool.from_function(
        func=search_manuals,
        name="search_manuals",
        description=(
            "Recherche sémantique dans les manuels de maintenance "
            "(passages texte et figures décrites par CLIP). "
            "Argument : query, la question technique."
        ),
    )


class MaintenanceAgent:
    """Agent : tool RAG puis une seule génération (évite le timeout Ollama)."""

    def __init__(self, retriever: PassageRetriever, llm: ChatOpenAI) -> None:
        self.retriever = retriever
        self.llm = llm
        self.memory = AgentMemory()
        self.search_manuals = build_search_tool(retriever, self.memory)

    def invoke(
        self,
        question: str,
        role: UserRole,
        *,
        photo_caption: str | None = None,
        photo_vector: list[float] | None = None,
    ) -> AskResponse:
        """Tool RAG (texte + photo CLIP), puis une génération."""
        self.memory.role = role
        self.memory.passages = []
        query = question if not photo_caption else f"{question}\n{photo_caption}"
        hits = self.retriever.retrieve(
            query,
            role,
            photo_vector=photo_vector,
            photo_caption=photo_caption,
        )
        self.memory.passages = hits
        if not hits:
            level, clarify = assess(question, [], UNKNOWN)
            return AskResponse(
                answer=UNKNOWN,
                citations=[],
                uncertainty=level,  # type: ignore[arg-type]
                clarification=clarify,
                photo_description=photo_caption,
            )
        context = format_passages(hits)
        messages = [
            SystemMessage(content=AGENT_PROMPT),
            HumanMessage(content=user_prompt(query, context)),
        ]
        logger.info("llm_debut")
        raw = self.llm.invoke(messages)
        answer = str(raw.content).strip() or UNKNOWN
        logger.info("llm_ok")
        level, clarify = assess(question, hits, answer)
        return AskResponse(
            answer=answer,
            citations=[] if is_unknown(answer) else passages_to_citations(hits),
            uncertainty=level,  # type: ignore[arg-type]
            clarification=clarify,
            photo_description=photo_caption,
        )
