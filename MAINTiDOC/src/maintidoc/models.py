"""Modèles de données de l'étape 1."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AccessLevel(str, Enum):
    """Niveau d'accès d'un document."""

    PUBLIC = "public"
    TECHNICIEN = "technicien"
    SUPERVISEUR = "superviseur"


class UserRole(str, Enum):
    """Rôle applicatif de l'utilisateur."""

    OPERATEUR = "operateur"
    TECHNICIEN = "technicien"
    SUPERVISEUR = "superviseur"


class DocumentRecord(BaseModel):
    """Entrée du catalogue documentaire."""

    document_id: str
    title: str
    version: str
    equipment_family: Literal["pompes", "variateurs"]
    access_level: AccessLevel
    filename: str


class Passage(BaseModel):
    """Passage indexable avec métadonnées exigées."""

    document_id: str
    title: str
    version: str
    page: int
    equipment_family: str
    access_level: AccessLevel
    content_hash: str
    text: str
    modality: Literal["text", "image"] = "text"
    image_path: str | None = None


class Citation(BaseModel):
    """Référence vérifiable renvoyée à l'utilisateur."""

    document_id: str
    title: str
    version: str
    page: int
    excerpt: str
    modality: Literal["text", "image"] = "text"
    image_path: str | None = None


class AskRequest(BaseModel):
    """Corps de POST /ask (texte et/ou photographie)."""

    question: str = Field(default="Que montre cette photographie d'équipement ?")
    user_id: str = Field(min_length=1)
    role: UserRole
    photo_b64: str | None = None


class AskResponse(BaseModel):
    """Réponse sourcée, avec incertitude (étape 2)."""

    answer: str
    citations: list[Citation]
    uncertainty: Literal["low", "medium", "high"] = "medium"
    clarification: str | None = None
    photo_description: str | None = None


class WorkflowRequest(BaseModel):
    """Démarre le graphe GMAO (étape 3)."""

    question: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    role: UserRole
    equipment_id: str = ""
    thread_id: str | None = None


class WorkflowResumeRequest(BaseModel):
    """Reprend après HITL."""

    thread_id: str = Field(min_length=1)
    approved: bool
    user_id: str = Field(min_length=1)
