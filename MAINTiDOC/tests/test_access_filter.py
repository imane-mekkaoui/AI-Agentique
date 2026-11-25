"""Un rôle sans droit ne voit pas les documents restreints."""

from __future__ import annotations

from maintidoc.access import allowed_levels, is_allowed
from maintidoc.models import AccessLevel, Passage, UserRole
from maintidoc.rag.chain import RagChain
from maintidoc.rag.prompts import UNKNOWN


class _FilteredRetriever:
    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages

    def retrieve(self, question: str, role: UserRole) -> list[Passage]:
        return [p for p in self.passages if is_allowed(role, p.access_level)]


class _FailLLM:
    def invoke(self, _messages: object) -> object:
        raise AssertionError("le LLM ne doit pas voir un document interdit")


def _passage(doc: str, level: AccessLevel, secret: str) -> Passage:
    return Passage(
        document_id=doc,
        title=doc,
        version="3.0",
        page=4,
        equipment_family="variateurs",
        access_level=level,
        content_hash="a" * 64,
        text=secret,
    )


def test_operateur_ne_voit_que_public() -> None:
    assert allowed_levels(UserRole.OPERATEUR) == frozenset({AccessLevel.PUBLIC})
    assert not is_allowed(UserRole.OPERATEUR, AccessLevel.SUPERVISEUR)


def test_operateur_zero_hit_sur_document_superviseur() -> None:
    secret = "Le code de déverrouillage est SUPER-LOCK-40"
    retriever = _FilteredRetriever(
        [_passage("FIX-CMP-002", AccessLevel.SUPERVISEUR, secret)]
    )
    chain = RagChain(retriever=retriever, llm=_FailLLM())  # type: ignore[arg-type]
    result = chain.invoke("Quel est le code de la vanne ?", UserRole.OPERATEUR)
    assert result.answer == UNKNOWN
    assert result.citations == []
    assert secret not in result.answer
