"""Analyse d'une photographie : VLM Ollama, repli CLIP."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx

from maintidoc.config import Settings
from maintidoc.ingestion.clip_describe import ClipDescriber

logger = logging.getLogger("maintidoc.rag")

VLM_PROMPT = (
    "Tu es un assistant documentaire de maintenance. "
    "Décris uniquement ce qui est visible : type d'équipement, voyants, "
    "pictogrammes, texte sur le panneau. Pas de diagnostic, pas d'action. "
    "Réponds en français, 4 phrases maximum."
)


def describe_photo(
    image_path: Path,
    settings: Settings,
    clip: ClipDescriber | None = None,
) -> str:
    """Légende VLM si le modèle est disponible, sinon tags CLIP."""
    raw = image_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    url = settings.ollama_url.rstrip("/") + "/api/chat"
    try:
        response = httpx.post(
            url,
            json={
                "model": settings.vlm_model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": VLM_PROMPT,
                        "images": [b64],
                    }
                ],
            },
            timeout=180.0,
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        if isinstance(content, str) and content.strip():
            logger.info("vlm_ok model=%s", settings.vlm_model)
            return content.strip()
    except httpx.HTTPError as exc:
        logger.warning("vlm_indisponible err=%s", exc)
    if clip is not None:
        return "Description CLIP : " + clip.describe(str(image_path))
    return "Photographie d'équipement (légende VLM indisponible)."
