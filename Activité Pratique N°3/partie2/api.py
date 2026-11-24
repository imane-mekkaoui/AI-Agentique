from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from partie2.rag_runtime import creer_agent_rag_reel

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOSSIER_IMAGES = PROJECT_ROOT / "data" / "images_extraites"
EXTENSIONS_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def nettoyer_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("La question ne peut pas être vide.")
        return question


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    numero: int
    document: str
    page: str | int
    type: str
    contenu: str
    distance: float
    image_path: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


class HealthResponse(BaseModel):
    status: str
    ready: bool


def formater_sources_api(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations = []
    for numero, source in enumerate(sources, start=1):
        metadata = source["metadata"]
        citations.append(
            {
                "numero": numero,
                "document": metadata.get("source", "Document inconnu"),
                "page": metadata.get("page_number", "inconnue"),
                "type": metadata.get("content_type", "inconnu"),
                "image_path": metadata.get("image_path"),
                "contenu": source["contenu"],
                "distance": source["distance"],
            }
        )
    return citations


def create_app(
    agent_factory: Callable[[], Any] = creer_agent_rag_reel,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            app.state.agent = agent_factory()
        except Exception:
            logger.exception("Impossible d'initialiser le service RAG.")
            raise
        yield

    app = FastAPI(
        title="API RAG multimodale",
        version="1.0.0",
        lifespan=lifespan,
    )
    origins = cors_origins
    if origins is None:
        origins = [
            origin.strip()
            for origin in os.getenv(
                "RAG_CORS_ORIGINS", "http://localhost:5173"
            ).split(",")
            if origin.strip()
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        ready = getattr(request.app.state, "agent", None) is not None
        return HealthResponse(status="ok" if ready else "starting", ready=ready)

    @app.get("/api/images/{filename}", response_class=FileResponse)
    def image_extraite(filename: str) -> FileResponse:
        if (
            Path(filename).name != filename
            or Path(filename).suffix.lower() not in EXTENSIONS_IMAGE
        ):
            raise HTTPException(status_code=404, detail="Image introuvable.")

        dossier_images = DOSSIER_IMAGES.resolve()
        chemin_image = (dossier_images / filename).resolve()
        if chemin_image.parent != dossier_images or not chemin_image.is_file():
            raise HTTPException(status_code=404, detail="Image introuvable.")
        return FileResponse(chemin_image)

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(payload: QuestionRequest, request: Request) -> ChatResponse:
        agent = getattr(request.app.state, "agent", None)
        if agent is None:
            raise HTTPException(
                status_code=503, detail="Le service RAG n'est pas prêt."
            )
        try:
            resultat = agent.invoke({"question": payload.question})
            reponse = resultat.get("reponse")
            if not isinstance(reponse, str) or not reponse.strip():
                raise ValueError("L'agent RAG a renvoyé une réponse vide.")
            sources = resultat.get("sources", [])
            citations = formater_sources_api(sources)
            return ChatResponse(answer=reponse.strip(), sources=citations)
        except HTTPException:
            raise
        except Exception as error:
            logger.exception("Échec du traitement de la question par le RAG.")
            raise HTTPException(
                status_code=502,
                detail=(
                    "Échec de la recherche ou de la génération. "
                    "Vérifiez l'index Chroma et la disponibilité d'Ollama."
                ),
            ) from error

    return app


app = create_app()
