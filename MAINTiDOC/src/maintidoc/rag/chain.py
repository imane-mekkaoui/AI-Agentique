"""Chaîne RAG : retrieve (droits) puis génération contrainte."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from maintidoc.config import Settings
from maintidoc.models import AskResponse, Citation, Passage, UserRole
from maintidoc.rag.prompts import UNKNOWN, SYSTEM_PROMPT, format_passages, user_prompt
from maintidoc.rag.uncertainty import assess, is_unknown
from maintidoc.rag.retriever import PassageRetriever

logger = logging.getLogger("maintidoc.rag")

EXCERPT_MAX = 280


def passages_to_citations(passages: list[Passage]) -> list[Citation]:
    """Construit des citations vérifiables à partir des passages filtrés."""
    citations: list[Citation] = []
    seen: set[tuple[str, int, str]] = set()
    seen_figure: set[tuple[int, str]] = set()
    for passage in passages:
        key = (passage.document_id, passage.page, passage.content_hash)
        if key in seen:
            continue
        if passage.modality == "image":
            fig_key = (passage.page, passage.text.strip()[:120])
            if fig_key in seen_figure:
                continue
            seen_figure.add(fig_key)
        seen.add(key)
        excerpt = passage.text[:EXCERPT_MAX]
        citations.append(
            Citation(
                document_id=passage.document_id,
                title=passage.title,
                version=passage.version,
                page=passage.page,
                excerpt=excerpt,
                modality=passage.modality,
                image_path=passage.image_path,
            )
        )
    return citations


class RagChain:
    """Orchestration LangChain minimale autour du retriever et du LLM."""

    def __init__(self, retriever: PassageRetriever, llm: ChatOpenAI) -> None:
        self.retriever = retriever
        self.llm = llm

    def invoke(self, question: str, role: UserRole) -> AskResponse:
        """Répond à une question en n'utilisant que des passages autorisés."""
        passages = self.retriever.retrieve(question, role)
        logger.info("retrieve_ok role=%s hits=%s", role.value, len(passages))
        if not passages:
            level, clarify = assess(question, [], UNKNOWN)
            return AskResponse(
                answer=UNKNOWN,
                citations=[],
                uncertainty=level,  # type: ignore[arg-type]
                clarification=clarify,
            )

        context = format_passages(passages)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt(question, context)),
        ]
        logger.info("llm_debut")
        raw = self.llm.invoke(messages)
        answer = str(raw.content).strip() or UNKNOWN
        logger.info("llm_ok")
        level, clarify = assess(question, passages, answer)
        return AskResponse(
            answer=answer,
            citations=[] if is_unknown(answer) else passages_to_citations(passages),
            uncertainty=level,  # type: ignore[arg-type]
            clarification=clarify,
        )


def build_llm(settings: Settings) -> ChatOpenAI:
    """LLM OpenAI-compatible (Ollama ou API)."""
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0,
        max_tokens=220,
        timeout=90,
    )
