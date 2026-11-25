"""Journalisation minimale : pas de question, réponse ni extrait documentaire."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure un logger applicatif sans données sensibles."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("maintidoc").debug("journalisation initialisée")
