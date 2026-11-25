"""Sans contexte, la chaîne répond Je ne sais pas."""

from __future__ import annotations

from maintidoc.models import Passage, UserRole
from maintidoc.rag.chain import RagChain
from maintidoc.rag.prompts import UNKNOWN, format_context, user_prompt


class _EmptyRetriever:
    def retrieve(self, question: str, role: UserRole) -> list[Passage]:
        return []


class _MustNotRun:
    def invoke(self, _messages: object) -> object:
        raise AssertionError("LLM inutile si le contexte est vide")


def test_empty_context_returns_je_ne_sais_pas() -> None:
    chain = RagChain(retriever=_EmptyRetriever(), llm=_MustNotRun())  # type: ignore[arg-type]
    result = chain.invoke("Quelle est la recette secrète du moteur ?", UserRole.TECHNICIEN)
    assert result.answer == UNKNOWN
    assert result.citations == []


def test_user_prompt_forces_unknown_without_context() -> None:
    prompt = user_prompt("test", format_context([]))
    assert "Je ne sais pas" in prompt
