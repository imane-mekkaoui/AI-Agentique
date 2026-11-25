"""Fixtures pytest communes."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.make_fixtures import generate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    """Répertoire des PDF de test, générés à la volée."""
    target = ROOT / "tests" / "fixtures"
    generate(target)
    return target
