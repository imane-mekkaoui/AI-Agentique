"""API FastAPI — santé et questions-réponses."""

from __future__ import annotations

import base64
import logging
import tempfile
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from langgraph.types import Command

from maintidoc.config import Settings, get_settings
from maintidoc.embeddings import get_embedding_client
from maintidoc.ingestion.clip_describe import get_clip_describer
from maintidoc.logging_setup import configure_logging

from maintidoc.models import (
    AskRequest,
    AskResponse,
    WorkflowRequest,
    WorkflowResumeRequest,
)
from maintidoc.workflow import graphe
from maintidoc.rag.agent import MaintenanceAgent
from maintidoc.rag.chain import build_llm
from maintidoc.rag.retriever import PassageRetriever
from maintidoc.rag.vlm import describe_photo
from maintidoc.vectorstore import connect, ensure_collection

logger = logging.getLogger("maintidoc.api")


@lru_cache(maxsize=1)
def get_chain() -> MaintenanceAgent:
    """Construit l'agent RAG une seule fois."""
    settings = get_settings()
    configure_logging(settings.log_level)
    client = connect(settings.qdrant_url)
    embeddings = get_embedding_client(settings.embedding_model, settings.embedding_device)
    clip = get_clip_describer(settings.clip_model, settings.embedding_device)
    ensure_collection(client, settings.qdrant_clip_collection, 512)
    retriever = PassageRetriever(
        client=client,
        collection=settings.qdrant_collection,
        embeddings=embeddings,
        k=settings.retrieval_k,
        clip_collection=settings.qdrant_clip_collection,
        clip=clip,
        settings=settings,
    )
    return MaintenanceAgent(retriever=retriever, llm=build_llm(settings))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Précharge embeddings + LLM client pour éviter un timeout au 1er /ask."""
    get_chain()
    yield


app = FastAPI(title="MAINTiDOC", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, str]:
    """Point d'entrée : l'API n'a pas d'interface HTML ici."""
    return {
        "service": "MAINTiDOC",
        "health": "/health",
        "ask": "POST /ask (question + photo_b64 optionnel)",
        "workflow": "POST /workflow puis POST /workflow/resume",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Vérification liveness."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    """Question et/ou photographie, filtrées selon le rôle."""
    logger.info(
        "ask role=%s user_id=%s photo=%s",
        payload.role.value,
        payload.user_id,
        bool(payload.photo_b64),
    )
    agent = get_chain()
    settings = get_settings()
    caption = None
    photo_vector = None
    if payload.photo_b64:
        raw = base64.b64decode(payload.photo_b64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            photo_path = Path(tmp.name)
        clip = get_clip_describer(settings.clip_model, settings.embedding_device)
        caption = describe_photo(photo_path, settings, clip)
        photo_vector = clip.encode_images([str(photo_path)])[0]
        photo_path.unlink(missing_ok=True)
    return agent.invoke(
        payload.question,
        payload.role,
        photo_caption=caption,
        photo_vector=photo_vector,
    )


def _etat_public(thread_id: str) -> dict:
    snap = graphe.get_state({"configurable": {"thread_id": thread_id}})
    values = dict(snap.values or {})
    pending = bool(snap.next)
    return {
        "thread_id": thread_id,
        "status": "pending_approval" if pending else "done",
        "equipment_id": values.get("equipment_id"),
        "historique": values.get("historique"),
        "tickets_ouverts": values.get("tickets_ouverts"),
        "draft_title": values.get("draft_title"),
        "draft_description": values.get("draft_description"),
        "message": values.get("message"),
        "ticket": values.get("ticket"),
        "decision": values.get("decision"),
    }


@app.post("/workflow")
def workflow_start(payload: WorkflowRequest) -> dict:
    """Lance historique + brouillon ; s'arrête pour approbation si technicien."""
    thread_id = payload.thread_id or str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    graphe.invoke(
        {
            "question": payload.question,
            "user_id": payload.user_id,
            "role": payload.role.value,
            "equipment_id": payload.equipment_id,
        },
        config,
    )
    return _etat_public(thread_id)


@app.post("/workflow/resume")
def workflow_resume(payload: WorkflowResumeRequest) -> dict:
    """Approuve ou refuse le brouillon (contenu figé dans le jeton)."""
    config = {"configurable": {"thread_id": payload.thread_id}}
    snap = graphe.get_state(config)
    values = snap.values or {}
    if values.get("user_id") != payload.user_id:
        return {"status": "error", "message": "L'approbation doit venir du même utilisateur."}
    graphe.invoke(Command(resume={"approved": payload.approved}), config)
    return _etat_public(payload.thread_id)


def create_app(_settings: Settings | None = None) -> FastAPI:
    """Factory pour les tests."""
    return app
