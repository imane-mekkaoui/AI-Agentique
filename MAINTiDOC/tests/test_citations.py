"""Les citations portent document, version et page exacts."""

from __future__ import annotations

from types import SimpleNamespace

from maintidoc.models import AccessLevel, Passage, UserRole
from maintidoc.rag.chain import RagChain, passages_to_citations


def test_citations_include_document_and_page() -> None:
    passage = Passage(
        document_id="FIX-SEC-001",
        title="Procédure SD-100",
        version="1.0",
        page=2,
        equipment_family="pompes",
        access_level=AccessLevel.PUBLIC,
        content_hash="b" * 64,
        text="Couper l'alimentation électrique avant d'ouvrir le capot.",
    )
    cites = passages_to_citations([passage, passage])
    assert len(cites) == 1
    assert cites[0].document_id == "FIX-SEC-001"
    assert cites[0].page == 2
    assert cites[0].version == "1.0"
    assert "alimentation" in cites[0].excerpt


class _Ret:
    def retrieve(self, question: str, role: UserRole) -> list[Passage]:
        return [
            Passage(
                document_id="FIX-SEC-001",
                title="Procédure SD-100",
                version="1.0",
                page=1,
                equipment_family="pompes",
                access_level=AccessLevel.PUBLIC,
                content_hash="c" * 64,
                text="Pression maximale 8 bar.",
            )
        ]


class _Llm:
    def invoke(self, _messages: object) -> object:
        return SimpleNamespace(content="La pression maximale est de 8 bar.")


def test_chain_returns_citations_when_context_present() -> None:
    chain = RagChain(retriever=_Ret(), llm=_Llm())  # type: ignore[arg-type]
    result = chain.invoke("Quelle pression max ?", UserRole.TECHNICIEN)
    assert result.citations
    assert result.citations[0].page == 1
    assert result.citations[0].document_id == "FIX-SEC-001"
    assert "8 bar" in result.answer
