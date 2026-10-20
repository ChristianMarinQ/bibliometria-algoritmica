"""Pruebas del corpus extraído (data/corpus.json) y de las rutas /api/articulos."""

from fastapi.testclient import TestClient

from app.corpus.extractor import limpiar_abstract, reparar_guiones
from app.main import app
from app.nucleo.corpus import cargar_corpus

cliente = TestClient(app)


def test_corpus_tiene_20_articulos_ordenados():
    """El corpus tiene los ids 1..20 en orden."""
    ids = [articulo["id"] for articulo in cargar_corpus()]
    assert ids == list(range(1, 21))


def test_campos_completos():
    """Cada artículo tiene título, al menos un autor, año y revista."""
    for articulo in cargar_corpus():
        assert articulo["titulo"], articulo["id"]
        assert articulo["autores"], articulo["id"]
        assert isinstance(articulo["anio"], int), articulo["id"]
        assert articulo["revista"], articulo["id"]
        assert articulo["archivo"].startswith(f"{articulo['id']}. ")


def test_abstracts_limpios_y_de_longitud_razonable():
    """Ningún abstract está vacío, trae keywords o introducción, ni rótulo inicial."""
    for articulo in cargar_corpus():
        abstract = articulo["abstract"]
        palabras = len(abstract.split())
        assert 80 <= palabras <= 450, (articulo["id"], palabras)
        for prohibido in ("Keywords", "K E Y W O R D S", "Introduction", "A B S T R A C T", "ﬁ", "­"):
            assert prohibido not in abstract, (articulo["id"], prohibido)
        assert not abstract.startswith("Abstract"), articulo["id"]
        assert "\n" not in abstract and "  " not in abstract, articulo["id"]


def test_reparar_guiones():
    """Une cortes de línea y conserva los compuestos que existen en el documento."""
    documento = "texto con self-regulated learning"
    assert reparar_guiones("practi-\ntioners", documento) == "practitioners"
    assert reparar_guiones("practi­\ntioners", documento) == "practitioners"
    assert reparar_guiones("self-\nregulated", documento) == "self-regulated"
    assert reparar_guiones("AI-\ndriven", documento) == "AI-driven"


def test_limpiar_abstract_normaliza():
    """Normaliza ligaduras, saltos de línea y espacios múltiples."""
    assert limpiar_abstract("  ﬁnal   ﬂow\nend  ", "") == "final flow end"


def test_endpoint_lista_articulos():
    """GET /api/articulos responde con los 20 artículos y el conteo de palabras."""
    respuesta = cliente.get("/api/articulos")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos) == 20
    assert set(datos[0]) == {"id", "titulo", "autores", "anio", "revista", "archivo", "palabras_abstract", "origen"}
    assert all(articulo["origen"] == "base" for articulo in datos)
    assert all(articulo["palabras_abstract"] > 0 for articulo in datos)


def test_endpoint_detalle_y_404():
    """GET /api/articulos/{id} incluye el abstract y devuelve 404 si no existe."""
    respuesta = cliente.get("/api/articulos/1")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["id"] == 1
    assert datos["palabras_abstract"] == len(datos["abstract"].split())
    assert cliente.get("/api/articulos/999").status_code == 404


def test_endpoints_sin_corpus_503(monkeypatch, tmp_path):
    """Sin data/corpus.json las rutas de corpus responden 503 en vez de 500."""
    from app.nucleo import corpus as nucleo_corpus

    monkeypatch.setattr(nucleo_corpus, "RUTA_CORPUS", tmp_path / "no_existe.json")
    nucleo_corpus.cargar_corpus.cache_clear()
    try:
        cliente = TestClient(app)
        assert cliente.get("/api/articulos").status_code == 503
        assert cliente.get("/api/articulos/1").status_code == 503
        assert cliente.get("/api/ranking").status_code == 503
    finally:
        nucleo_corpus.cargar_corpus.cache_clear()
