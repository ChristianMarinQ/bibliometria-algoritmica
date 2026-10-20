"""Pruebas de la subida de artículos (corpus dinámico) y de GET /api/sistema.

Usan una carpeta de subidos temporal (conftest.py) y modelos de IA falsos para no
cargar Word2Vec ni SBERT reales.
"""

import hashlib
import json
import math

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.nucleo import almacen_subidos
from app.servicios import embeddings_servidor

cliente = TestClient(app)

PDF_ART_5 = next(config.CARPETA_ARTICULOS.glob("5. *.pdf"), None)
requiere_datos = pytest.mark.skipif(
    PDF_ART_5 is None or not config.RUTA_CORPUS.exists() or not config.RUTA_EMBEDDINGS.exists(),
    reason="Faltan los PDFs, data/corpus.json o data/embeddings.json",
)


class Word2VecFalso:
    """Imita gensim KeyedVectors: cada palabra tiene un vector determinista de 300 dimensiones."""
    vector_size = 300

    class _Indice:
        def __contains__(self, token):
            return True

    key_to_index = _Indice()

    def __getitem__(self, token):
        semilla = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        return [math.sin(semilla % 1000 + k) for k in range(self.vector_size)]


class SbertFalso:
    """Imita SentenceTransformer.encode con vectores de 384 dimensiones."""

    def encode(self, textos, show_progress_bar=False):
        return [[math.cos(len(texto) + k) for k in range(384)] for texto in textos]


@pytest.fixture
def subida_activa(monkeypatch):
    """Subida habilitada, sin clave, IA activa con modelos falsos."""
    monkeypatch.setattr(config, "SUBIDA_HABILITADA", True)
    monkeypatch.setattr(config, "CLAVE_SUBIDA", None)
    monkeypatch.setattr(config, "IA_EN_SERVIDOR", True)
    falsos = {"word2vec": Word2VecFalso(), "sbert": SbertFalso()}
    monkeypatch.setattr(embeddings_servidor, "modelo", lambda clave: falsos[clave])
    yield


def subir_pdf(cabeceras=None, nombre="copia-articulo-5.pdf", contenido=None):
    """Envía el PDF del art. 5 (o el contenido dado) a /articulos/extraer."""
    if contenido is None:
        contenido = PDF_ART_5.read_bytes()
    return cliente.post("/api/articulos/extraer", files={"archivo": (nombre, contenido, "application/pdf")},
                        headers=cabeceras or {})


def guardar(extraido, cabeceras=None, **cambios):
    """Confirma lo extraído en POST /articulos con los cambios indicados."""
    datos = {clave: extraido[clave] for clave in ("titulo", "autores", "anio", "revista", "abstract", "archivo")}
    datos.update(cambios)
    return cliente.post("/api/articulos", json=datos, headers=cabeceras or {})


def test_sistema(subida_activa):
    datos = cliente.get("/api/sistema").json()
    assert datos["subida_habilitada"] is True
    assert datos["requiere_clave"] is False
    assert datos["ia_en_servidor"] is True
    assert datos["tamano_maximo_mb"] == 15
    if config.RUTA_CORPUS.exists():
        assert datos["total_articulos"] == datos["articulos_base"] == 20


@requiere_datos
def test_flujo_completo(subida_activa, carpeta_subidos_temporal):
    """Extraer → guardar → aparece en todas las vistas → borrar → desaparece."""
    respuesta = subir_pdf()
    assert respuesta.status_code == 200, respuesta.text
    extraido = respuesta.json()
    assert extraido["archivo"] == "copia-articulo-5.pdf"
    assert extraido["titulo"] and extraido["autores"] and extraido["anio"]
    assert extraido["palabras_abstract"] > 100
    assert isinstance(extraido["advertencias"], list)
    # La extracción no guarda nada todavía.
    assert len(cliente.get("/api/articulos").json()) == 20

    respuesta = guardar(extraido, titulo="Copia de prueba: " + extraido["titulo"])
    assert respuesta.status_code == 201, respuesta.text
    nuevo = respuesta.json()
    assert nuevo["id"] == 21 and nuevo["origen"] == "subido"
    assert nuevo["embeddings"] == {"word2vec": True, "sbert": True}
    assert (carpeta_subidos_temporal / "pdfs" / "21.pdf").exists()
    assert json.loads((carpeta_subidos_temporal / "articulos.json").read_text(encoding="utf-8"))[0]["id"] == 21

    # Corpus
    lista = cliente.get("/api/articulos").json()
    assert len(lista) == 21 and lista[-1]["origen"] == "subido"
    assert cliente.get("/api/articulos/21").json()["abstract"] == extraido["abstract"]
    assert cliente.get("/api/sistema").json()["total_articulos"] == 21

    # Búsqueda: el abstract copiado aparece junto al del art. 5.
    patron = " ".join(extraido["abstract"].split()[3:6])
    ids = [r["articulo_id"] for r in cliente.post("/api/busqueda", json={"patron": patron}).json()["resultados"]]
    assert 5 in ids and 21 in ids

    # Ranking: hay más tokens que con el corpus base.
    total = cliente.get("/api/ranking").json()["total_tokens"]

    # Clustering con TF-IDF y SBERT: 21 hojas.
    for representacion in ("tfidf", "sbert"):
        datos = cliente.get(f"/api/clustering?representacion={representacion}").json()
        assert len(datos["articulos"]) == 21
        assert len(datos["metodos"][0]["fusiones"]) == 20

    # Similitud: todos los algoritmos (incluida IA) con el id 21.
    datos = cliente.post("/api/similitud", json={"ids": [5, 21]}).json()
    claves = [r["clave"] for r in datos["resultados"]]
    assert "word2vec" in claves and "sbert" in claves and "avisos" not in datos
    jaccard = next(r for r in datos["resultados"] if r["clave"] == "jaccard")
    assert jaccard["matriz"][0][1] == pytest.approx(1.0)
    assert cliente.post("/api/similitud/traza",
                        json={"id_a": 1, "id_b": 21, "algoritmo": "sbert"}).status_code == 200

    # Borrar
    assert cliente.delete("/api/articulos/21").status_code == 204
    assert len(cliente.get("/api/articulos").json()) == 20
    assert cliente.get("/api/articulos/21").status_code == 404
    assert not (carpeta_subidos_temporal / "pdfs" / "21.pdf").exists()
    assert cliente.get("/api/ranking").json()["total_tokens"] < total
    assert len(cliente.get("/api/clustering").json()["articulos"]) == 20
    assert cliente.post("/api/similitud", json={"ids": [5, 21]}).status_code == 404
    assert almacen_subidos.leer_embeddings()["sbert"]["vectores"] == {}


@requiere_datos
def test_duplicado_409(subida_activa):
    extraido = subir_pdf().json()
    # Mismo título que el art. 5 base, con otras mayúsculas y espacios.
    titulo = "  " + extraido["titulo"].upper().replace(" ", "   ") + " "
    assert guardar(extraido, titulo=titulo).status_code == 409


@requiere_datos
def test_borrar_base_403_e_inexistente_404(subida_activa):
    assert cliente.delete("/api/articulos/3").status_code == 403
    assert cliente.delete("/api/articulos/999").status_code == 404


@requiere_datos
def test_validaciones_422(subida_activa):
    extraido = subir_pdf().json()
    assert guardar(extraido, titulo="   ").status_code == 422
    assert guardar(extraido, titulo="Otro título", abstract="muy corto").status_code == 422
    assert guardar(extraido, titulo="Otro título", abstract="palabra " * 1001).status_code == 422


def test_archivo_no_pdf_y_tamano(subida_activa, monkeypatch):
    assert subir_pdf(nombre="notas.txt", contenido=b"%PDF-1.4 hola").status_code == 400
    assert subir_pdf(nombre="falso.pdf", contenido=b"esto no es un pdf").status_code == 400
    assert subir_pdf(nombre="roto.pdf", contenido=b"%PDF-1.4 basura sin estructura").status_code == 400
    monkeypatch.setattr(config, "TAMANO_MAXIMO_MB", 0)
    assert subir_pdf(nombre="grande.pdf", contenido=b"%PDF-1.4 " + b"x" * 10).status_code == 413


@requiere_datos
def test_clave_requerida(subida_activa, monkeypatch):
    monkeypatch.setattr(config, "CLAVE_SUBIDA", "secreta")
    assert cliente.get("/api/sistema").json()["requiere_clave"] is True
    assert subir_pdf().status_code == 403
    assert subir_pdf({"X-Clave-Subida": "otra"}).status_code == 403
    extraido = subir_pdf({"X-Clave-Subida": "secreta"}).json()
    assert guardar(extraido, titulo="Con clave").status_code == 403
    respuesta = guardar(extraido, {"X-Clave-Subida": "secreta"}, titulo="Con clave")
    assert respuesta.status_code == 201
    id_nuevo = respuesta.json()["id"]
    assert cliente.delete(f"/api/articulos/{id_nuevo}").status_code == 403
    assert cliente.delete(f"/api/articulos/{id_nuevo}", headers={"X-Clave-Subida": "secreta"}).status_code == 204


def test_subida_deshabilitada(subida_activa, monkeypatch):
    monkeypatch.setattr(config, "SUBIDA_HABILITADA", False)
    assert cliente.get("/api/sistema").json()["subida_habilitada"] is False
    assert subir_pdf(nombre="a.pdf", contenido=b"%PDF-1.4").status_code == 403
    assert cliente.post("/api/articulos", json={"titulo": "x"}).status_code == 403
    assert cliente.delete("/api/articulos/21").status_code == 403


@requiere_datos
def test_ia_desactivada_avisos(subida_activa, monkeypatch):
    """Sin IA en el servidor el artículo se guarda sin vectores y las vistas avisan."""
    monkeypatch.setattr(config, "IA_EN_SERVIDOR", False)
    extraido = subir_pdf().json()
    respuesta = guardar(extraido, titulo="Sin IA")
    assert respuesta.status_code == 201
    nuevo = respuesta.json()
    assert nuevo["embeddings"] == {"word2vec": False, "sbert": False}
    assert nuevo["avisos"]

    datos = cliente.post("/api/similitud", json={"ids": [1, nuevo["id"]]}).json()
    claves = [r["clave"] for r in datos["resultados"]]
    assert "sbert" not in claves and "word2vec" not in claves and "jaccard" in claves
    assert len(datos["avisos"]) == 2
    explicito = cliente.post("/api/similitud", json={"ids": [1, nuevo["id"]], "algoritmos": ["sbert"]})
    assert explicito.status_code == 503

    sbert = cliente.get("/api/clustering?representacion=sbert")
    assert sbert.status_code == 503 and "subido" in sbert.json()["detail"]
    assert len(cliente.get("/api/clustering").json()["articulos"]) == 21


@pytest.mark.lento
@pytest.mark.skipif(not config.IA_EN_SERVIDOR, reason="gensim/sentence-transformers no instalados")
def test_modelos_reales_opcional(monkeypatch):
    """Opcional (pytest -m lento): calcula embeddings reales de un texto corto."""
    monkeypatch.setattr(config, "IA_EN_SERVIDOR", True)
    resultado = embeddings_servidor.calcular_embeddings("Artificial intelligence in higher education " * 5)
    assert len(resultado["word2vec"]["vector"]) == 300
    assert len(resultado["sbert"]["vector"]) == 384
