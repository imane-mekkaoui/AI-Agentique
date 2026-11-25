"""Étape 3 : jeton, droits, idempotence, graphe HITL."""

from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.types import Command

from maintidoc import mcp_service as gmao
from maintidoc.mcp_service import (
    create_ticket,
    get_equipment_history,
    jeton_approbation,
    verifier_jeton,
)
from maintidoc.workflow import construire_graphe


@pytest.fixture()
def tickets_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cible = tmp_path / "tickets.json"
    monkeypatch.setattr(gmao, "TICKETS", cible)
    return cible


def test_historique_connu() -> None:
    texte = get_equipment_history("VLT-FC302-01")
    assert "FC 302" in texte
    assert "2026-11-02" in texte


def test_operateur_jeton_refuse(tickets_tmp: Path) -> None:
    token = jeton_approbation("op1", "operateur", "SD-100", "t", "d")
    with pytest.raises(PermissionError, match="opérateur"):
        verifier_jeton(token, "SD-100", "t", "d")


def test_jeton_contenu_modifie(tickets_tmp: Path) -> None:
    token = jeton_approbation("tech-demo", "technicien", "SD-100", "titre", "desc")
    with pytest.raises(PermissionError, match="invalide"):
        verifier_jeton(token, "SD-100", "titre", "DESC CHANGÉ")


def test_create_et_idempotence(tickets_tmp: Path) -> None:
    token = jeton_approbation("tech-demo", "technicien", "SD-100", "Fuite", "Joint")
    a = create_ticket("SD-100", "Fuite", "Joint", token)
    b = create_ticket("SD-100", "Fuite", "Joint", token)
    assert "TCK-" in a
    assert "Idempotence" in b


def test_graphe_hitl_puis_approbation(tickets_tmp: Path) -> None:
    graphe = construire_graphe()
    cfg = {"configurable": {"thread_id": "demo-hitl"}}
    graphe.invoke(
        {
            "question": "Historique VLT FC 302 et ticket",
            "user_id": "tech-demo",
            "role": "technicien",
            "equipment_id": "VLT-FC302-01",
        },
        cfg,
    )
    snap = graphe.get_state(cfg)
    assert snap.next
    assert snap.values.get("draft_title")
    graphe.invoke(Command(resume={"approved": True}), cfg)
    snap2 = graphe.get_state(cfg)
    assert not snap2.next
    assert "TCK-" in (snap2.values.get("ticket") or "")


def test_operateur_pas_de_ticket() -> None:
    graphe = construire_graphe()
    cfg = {"configurable": {"thread_id": "op-1"}}
    out = graphe.invoke(
        {
            "question": "Historique NK",
            "user_id": "op1",
            "role": "operateur",
            "equipment_id": "GF-NK-01",
        },
        cfg,
    )
    assert "opérateur" in out.get("message", "").casefold()
    assert not out.get("ticket")
