"""Configuración común de pytest: aísla la carpeta de artículos subidos."""

import pytest

from app import config


@pytest.fixture(autouse=True)
def carpeta_subidos_temporal(monkeypatch, tmp_path):
    """Cada prueba usa una carpeta de subidos vacía y temporal (nunca data/subidos real)."""
    monkeypatch.setattr(config, "CARPETA_SUBIDOS", tmp_path / "subidos")
    return tmp_path / "subidos"
