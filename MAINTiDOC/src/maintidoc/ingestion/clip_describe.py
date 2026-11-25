"""Légendes d'images via CLIP (classement zero-shot)."""

from __future__ import annotations

import logging
from functools import lru_cache

from PIL import Image
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("maintidoc.ingestion")
CLIP_DIM = 512

CLIP_LABELS = [
    "centrifugal pump",
    "pump installation drawing",
    "electric motor",
    "wiring diagram",
    "exploded view of machine parts",
    "foundation and mounting drawing",
    "pipe flange connection",
    "control panel or keypad",
    "warning or safety symbol",
    "dimension table",
    "piping layout",
    "bearing assembly",
    "frequency converter or VFD",
    "nameplate label",
    "coupling and shaft",
    "feeler gauge on coupling",
    "straightedge alignment of pump and motor",
    "valve",
    "cooling fan",
    "terminal box",
    "hydraulic schematic",
    "product photo of industrial pump",
    "orange warning light on control panel",
    "blinking LED indicator",
    "keypad with status lights",
]


class ClipDescriber:
    """Attribue des libellés CLIP aux figures extraitees."""

    def __init__(self, model_name: str = "clip-ViT-B-32", device: str = "cpu") -> None:
        logger.info("chargement_clip name=%s", model_name)
        self._model = SentenceTransformer(model_name, device=device)
        self._label_vectors = self._model.encode(
            CLIP_LABELS, normalize_embeddings=True, show_progress_bar=False
        )

    def describe(self, image_path: str, top_k: int = 4) -> str:
        """Retourne les libellés CLIP les plus proches de l'image."""
        with Image.open(image_path) as image:
            rgb = image.convert("RGB")
            vector = self._model.encode(
                rgb, normalize_embeddings=True, show_progress_bar=False
            )
        scores = vector @ self._label_vectors.T
        ranked = sorted(zip(scores.tolist(), CLIP_LABELS, strict=True), reverse=True)
        picked = [label for score, label in ranked[:top_k] if score > 0.12]
        if not picked:
            picked = [ranked[0][1]]
        return ", ".join(picked)

    def describe_many(self, image_paths: list[str]) -> list[str]:
        return [self.describe(path) for path in image_paths]

    def encode_images(self, image_paths: list[str]) -> list[list[float]]:
        """Vecteurs CLIP des photographies / figures (recherche texte-image)."""
        vectors: list[list[float]] = []
        for path in image_paths:
            with Image.open(path) as image:
                rgb = image.convert("RGB")
                vec = self._model.encode(
                    rgb, normalize_embeddings=True, show_progress_bar=False
                )
            vectors.append(vec.tolist())
        return vectors

    def encode_texts(self, texts: list[str]) -> list[list[float]]:
        """Vecteurs CLIP texte, même espace que les images."""
        vecs = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [row.tolist() for row in vecs]


@lru_cache(maxsize=1)
def get_clip_describer(model_name: str, device: str) -> ClipDescriber:
    """Singleton CLIP pour l'ingestion."""
    return ClipDescriber(model_name, device)
