"""Étape 2 : fusion, métriques, incertitude, sortie structurée."""

from __future__ import annotations

from maintidoc.models import AccessLevel, AskResponse, Passage, UserRole
from maintidoc.rag.chain import RagChain
from maintidoc.rag.prompts import UNKNOWN
from maintidoc.rag.rerank import fuse_passages, mrr_at_k, ndcg_at_k
from maintidoc.rag.retriever import _filtre_voyant
from maintidoc.rag.uncertainty import assess, is_unknown


def _p(doc: str, text: str, modality: str = "text") -> Passage:
    return Passage(
        document_id=doc,
        title=doc,
        version="1",
        page=1,
        equipment_family="pompes",
        access_level=AccessLevel.PUBLIC,
        content_hash=(doc + text)[:64].ljust(64, "0"),
        text=text,
        modality=modality,  # type: ignore[arg-type]
    )


def test_fuse_dedupe() -> None:
    a = _p("A", "alignement")
    merged = fuse_passages([a], [a], [_p("B", "pression")], limit=10)
    assert len(merged) == 2


def test_ndcg_mrr() -> None:
    assert ndcg_at_k([1, 0, 0], 5) == 1.0
    assert mrr_at_k([0, 1, 0], 10) == 0.5
    assert mrr_at_k([0, 0], 10) == 0.0


def test_incertitude_sans_contexte() -> None:
    level, clarify = assess("voyant ?", [], UNKNOWN)
    assert level == "high"
    assert clarify


def test_photo_ambiguite_medium() -> None:
    hits = [_p("A", "figure voyant", "image")]
    level, _ = assess("photo", hits, "Voir la figure.")
    assert level == "medium"


def test_ask_response_champs_etape2() -> None:
    payload = AskResponse(answer=UNKNOWN, citations=[], uncertainty="high")
    assert payload.clarification is None
    assert payload.photo_description is None


def test_je_ne_sais_pas_est_incertitude_haute() -> None:
    level, clarify = assess(
        "Voyant LED VLT FC 302 ?",
        [_p("D", "Split Shipment Electrical Connections")],
        "Je ne sais pas. Les extraits n'incluent aucun texte concernant les voyants.",
    )
    assert is_unknown(
        "Je ne sais pas. Les extraits n'incluent aucun texte concernant les voyants."
    )
    assert level == "high"
    assert clarify


def test_filtre_voyant_ecarte_cablage() -> None:
    keep = _p("D", "Le voyant LED orange indique un avertissement.")
    drop = _p("D", "Split Shipment Electrical Connections dU/dt Cabinet")
    out = _filtre_voyant("Voyant LED du VLT FC 302 ?", [keep, drop])
    assert out == [keep]


def test_chain_unknown_structure() -> None:
    class _Empty:
        def retrieve(self, question: str, role: UserRole) -> list[Passage]:
            return []

    class _Boom:
        def invoke(self, _messages: object) -> object:
            raise AssertionError("pas de LLM")

    result = RagChain(retriever=_Empty(), llm=_Boom()).invoke(  # type: ignore[arg-type]
        "photo", UserRole.TECHNICIEN
    )
    assert result.answer == UNKNOWN
    assert result.uncertainty == "high"
    assert result.clarification
