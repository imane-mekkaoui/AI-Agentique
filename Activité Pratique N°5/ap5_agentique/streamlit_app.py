from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
from langchain_core.messages import HumanMessage

from ap5.agentic_rag import construire_graphe_rag
from ap5.orchestrateur import construire_graphe_sav

st.set_page_config(page_title="AP5 — Agents SAV", layout="wide")
st.title("Activité pratique N°5")
onglet_rag, onglet_sav = st.tabs(["Chatbot RAG agentique", "SAV distributeur"])


@st.cache_resource
def graphe_rag():
    return construire_graphe_rag()


@st.cache_resource
def graphe_sav():
    return construire_graphe_sav()


with onglet_rag:
    st.caption("LangGraph + retriever_tool (manuel PX-200).")
    if "hist_rag" not in st.session_state:
        st.session_state.hist_rag = []
    for role, texte in st.session_state.hist_rag:
        st.chat_message(role).write(texte)
    msg = st.chat_input("Question sur le manuel…", key="rag_in")
    if msg:
        st.session_state.hist_rag.append(("user", msg))
        with st.spinner("Agent RAG…"):
            out = graphe_rag().invoke({"messages": [HumanMessage(content=msg)]})
        reponse = out["messages"][-1].content
        st.session_state.hist_rag.append(("assistant", reponse))
        st.rerun()

with onglet_sav:
    st.caption("Orchestrateur → dépanneur (MCP RAG local) ou vérificateur garantie.")
    question = st.text_area(
        "Demande",
        "Mon imprimante PX-200 affiche un voyant clignotant. "
        "Que signifie le pictogramme sur la photo jointe ?",
    )
    photo = st.text_input("Référence photo (optionnel)", "img_px200_01")
    if st.button("Traiter la demande"):
        with st.spinner("Orchestrateur…"):
            etat = graphe_sav().invoke(
                {"question": question, "photo": photo.strip()}
            )
        st.write(f"**Catégorie :** {etat.get('categorie')} · **Agent :** {etat.get('agent')}")
        st.markdown(etat.get("reponse", ""))
        with st.expander("Observation brute"):
            st.text(etat.get("observation", ""))
