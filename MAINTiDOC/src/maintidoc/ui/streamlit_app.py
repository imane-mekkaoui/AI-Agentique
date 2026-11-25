"""Interface Streamlit V3 : documentation + tickets GMAO."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_URL = os.getenv("MAINTIDOC_API_URL", "http://127.0.0.1:8001")

st.set_page_config(page_title="MAINTiDOC", layout="centered")
st.title("MAINTiDOC — assistant documentaire V3")
st.caption(
    "Texte + photographie + tickets GMAO (MCP). "
    "Aucun diagnostic garanti. Aucun pilotage de machine. "
    f"API : {API_URL}"
)

role = st.selectbox(
    "Rôle utilisateur (droits)",
    options=["operateur", "technicien", "superviseur"],
    index=1,
)
user_id = st.text_input("Identifiant", value="tech-demo")
onglet_doc, onglet_gmao = st.tabs(["Documentation", "Ticket GMAO"])


def afficher_doc(data: dict) -> None:
    if data.get("photo_description"):
        st.subheader("Lecture de la photo")
        st.write(data["photo_description"])
    citations = data.get("citations") or []
    root = Path(__file__).resolve().parents[3]
    figures = [
        cite
        for cite in citations
        if cite.get("modality") == "image" and cite.get("image_path")
    ]
    if figures:
        st.subheader("Figure du manuel")
        for cite in figures:
            local = Path(cite["image_path"])
            if not local.is_absolute():
                local = root / cite["image_path"]
            if local.exists():
                st.image(
                    str(local),
                    caption=(
                        f"{cite['title']} — p.{cite['page']} "
                        f"({cite['document_id']})"
                    ),
                )
    st.subheader("Réponse")
    st.write(data.get("answer", ""))
    st.caption(f"Incertitude : {data.get('uncertainty', '?')}")
    if data.get("clarification"):
        st.warning(data["clarification"])
    st.subheader("Sources")
    if not citations:
        st.info("Aucune citation (contexte vide ou hors droits).")
    for cite in citations:
        kind = cite.get("modality") or "text"
        st.markdown(
            f"- **{cite['title']}** `{cite['document_id']}` "
            f"v{cite['version']} — page {cite['page']} ({kind})"
        )
        st.caption(cite.get("excerpt", ""))


with onglet_doc:
    question = st.text_area(
        "Question technique",
        height=100,
        placeholder="Voici une photo du panneau. Que signifie ce voyant orange ?",
        key="q_doc",
    )
    photo = st.file_uploader("Photographie (optionnel)", type=["png", "jpg", "jpeg", "webp"])
    if st.button("Demander") and (question.strip() or photo):
        payload = {
            "question": question.strip()
            or "Que montre cette photographie d'équipement ?",
            "user_id": user_id,
            "role": role,
        }
        if photo is not None:
            payload["photo_b64"] = base64.b64encode(photo.getvalue()).decode("ascii")
            st.image(photo, caption="Photo envoyée", width=280)
        with st.spinner("Analyse documentaire…"):
            try:
                response = httpx.post(f"{API_URL}/ask", json=payload, timeout=240.0)
                response.raise_for_status()
                afficher_doc(response.json())
            except httpx.HTTPError as exc:
                st.error(f"API indisponible : {exc}")

with onglet_gmao:
    st.write("Consulte l'historique puis prépare un ticket. La création exige **Approuver**.")
    q_gmao = st.text_area(
        "Demande",
        value="Voyant sur VLT FC 302, consulter l'historique et préparer un ticket.",
        key="q_gmao",
    )
    eq = st.text_input("Équipement (optionnel)", value="VLT-FC302-01")
    if st.button("Consulter GMAO"):
        try:
            response = httpx.post(
                f"{API_URL}/workflow",
                json={
                    "question": q_gmao,
                    "user_id": user_id,
                    "role": role,
                    "equipment_id": eq,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            st.session_state["gmao"] = response.json()
        except httpx.HTTPError as exc:
            st.error(f"API indisponible : {exc}")

    data = st.session_state.get("gmao")
    if data:
        st.caption(f"Fil {data.get('thread_id')} — {data.get('status')}")
        st.text(data.get("historique") or "")
        st.text(data.get("tickets_ouverts") or "")
        if data.get("draft_title"):
            st.subheader("Brouillon")
            st.write(data["draft_title"])
            st.text(data.get("draft_description") or "")
        if data.get("message"):
            st.info(data["message"])
        if data.get("ticket"):
            st.success(data["ticket"])
        if data.get("status") == "pending_approval":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Approuver le ticket"):
                    r = httpx.post(
                        f"{API_URL}/workflow/resume",
                        json={
                            "thread_id": data["thread_id"],
                            "approved": True,
                            "user_id": user_id,
                        },
                        timeout=30.0,
                    )
                    r.raise_for_status()
                    st.session_state["gmao"] = r.json()
                    st.rerun()
            with c2:
                if st.button("Refuser"):
                    r = httpx.post(
                        f"{API_URL}/workflow/resume",
                        json={
                            "thread_id": data["thread_id"],
                            "approved": False,
                            "user_id": user_id,
                        },
                        timeout=30.0,
                    )
                    r.raise_for_status()
                    st.session_state["gmao"] = r.json()
                    st.rerun()
