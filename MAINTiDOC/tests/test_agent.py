"""L'agent utilise le tool RAG ; sans hit il ne hallucine pas."""

from __future__ import annotations

from maintidoc.models import AccessLevel, Passage, UserRole
from maintidoc.rag.agent import AgentMemory, build_search_tool
from maintidoc.rag.chain import RagChain
from maintidoc.rag.prompts import UNKNOWN


class _EmptyRetriever:
    def retrieve(self, question: str, role: UserRole) -> list[Passage]:
        return []


def test_search_manuals_tool_respects_empty_index() -> None:
    memory = AgentMemory(role=UserRole.TECHNICIEN)
    tool = build_search_tool(_EmptyRetriever(), memory)  # type: ignore[arg-type]
    text = tool.invoke({"query": "How do I install a Grundfos NK pump?"})
    assert "Aucun passage" in text
    assert memory.passages == []


def test_fallback_chain_unknown_when_no_hits() -> None:
    class _Boom:
        def invoke(self, _messages: object) -> object:
            raise AssertionError("pas de LLM sans contexte")

    chain = RagChain(retriever=_EmptyRetriever(), llm=_Boom())  # type: ignore[arg-type]
    result = chain.invoke("photo du voyant", UserRole.OPERATEUR)
    assert result.answer == UNKNOWN


def test_search_manuals_tool_returns_figure_metadata() -> None:
    class _ImgRet:
        def retrieve(self, question: str, role: UserRole) -> list[Passage]:
            return [
                Passage(
                    document_id="GF-NK-IEC-001",
                    title="NK",
                    version="1",
                    page=8,
                    equipment_family="pompes",
                    access_level=AccessLevel.PUBLIC,
                    content_hash="d" * 64,
                    text="Figure : pump installation drawing",
                    modality="image",
                    image_path="data/extracted_images/GF-NK-IEC-001/p8_0.png",
                )
            ]

    memory = AgentMemory(role=UserRole.TECHNICIEN)
    tool = build_search_tool(_ImgRet(), memory)  # type: ignore[arg-type]
    text = tool.invoke({"query": "pump figure"})
    assert "p8_0.png" in text
    assert memory.passages[0].modality == "image"
