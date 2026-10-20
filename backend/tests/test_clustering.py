"""Pruebas del Req. 2: clustering jerárquico, métricas internas y endpoint."""

import json

import pytest
from fastapi.testclient import TestClient

from app import config
from app.algoritmos.clustering.jerarquico import METODOS, agrupar, construir_arbol
from app.algoritmos.clustering.metricas import (
    correlacion_cofenetica, correlacion_pearson, cortar_arbol, matriz_cofenetica, silhouette)
from app.main import app
from app.servicios import clustering as servicio

# Cinco puntos sobre una recta: posiciones 0, 2, 4.4, 7 y 7.5; d(i, j) = |xi − xj|.
# Fusiones esperadas (a mano):
#   paso 1: (3, 4) a 0.5 -> nodo 5      paso 2: (0, 1) a 2 -> nodo 6
#   single:   d(6,2)=min(4.4,2.4)=2.4 < d(5,2)=min(2.6,3.1)=2.6 -> (2, 6) a 2.4; raíz a 2.6
#   complete: d(6,2)=max(4.4,2.4)=4.4 > d(5,2)=max(2.6,3.1)=3.1 -> (2, 5) a 3.1; raíz a 7.5
#   average:  d(6,2)=(4.4+2.4)/2=3.4 > d(5,2)=(2.6+3.1)/2=2.85 -> (2, 5) a 2.85;
#             raíz = (4.4+7+7.5+2.4+5+5.5)/6 = 5.3
POSICIONES = [0.0, 2.0, 4.4, 7.0, 7.5]
DISTANCIAS = [[abs(x - y) for y in POSICIONES] for x in POSICIONES]

ESPERADO = {
    "single": [(3, 4, 0.5), (0, 1, 2.0), (2, 6, 2.4), (5, 7, 2.6)],
    "complete": [(3, 4, 0.5), (0, 1, 2.0), (2, 5, 3.1), (6, 7, 7.5)],
    "average": [(3, 4, 0.5), (0, 1, 2.0), (2, 5, 2.85), (6, 7, 5.3)],
}


def contar_nodos(nodo, hojas, internos):
    """Recorre el árbol y acumula hojas y nodos internos."""
    if "hijos" in nodo:
        internos.append(nodo)
        assert len(nodo["hijos"]) == 2
        for hijo in nodo["hijos"]:
            contar_nodos(hijo, hojas, internos)
    else:
        hojas.append(nodo)


@pytest.mark.parametrize("metodo", list(METODOS))
def test_orden_de_fusiones_conocido(metodo):
    fusiones = agrupar(DISTANCIAS, metodo)
    obtenido = [(f["a"], f["b"], f["distancia"]) for f in fusiones]
    assert len(obtenido) == len(ESPERADO[metodo])
    for (a, b, d), (ea, eb, ed) in zip(obtenido, ESPERADO[metodo]):
        assert (a, b) == (ea, eb)
        assert d == pytest.approx(ed)
    assert [f["nuevo"] for f in fusiones] == [5, 6, 7, 8]
    assert [f["tamano"] for f in fusiones][-1] == 5


@pytest.mark.parametrize("metodo", list(METODOS))
def test_arbol_tiene_n_hojas_y_n_menos_1_internos(metodo):
    fusiones = agrupar(DISTANCIAS, metodo)
    hojas = [{"articulo_id": i + 1, "titulo": f"T{i}"} for i in range(5)]
    raiz = construir_arbol(fusiones, hojas)
    lista_hojas, internos = [], []
    contar_nodos(raiz, lista_hojas, internos)
    assert len(lista_hojas) == 5 and len(internos) == 4
    assert sorted(h["articulo_id"] for h in lista_hojas) == [1, 2, 3, 4, 5]
    assert raiz["tamano"] == 5 and raiz["id"] == 8


@pytest.mark.parametrize("metodo", list(METODOS))
def test_distancias_de_fusion_monotonas(metodo):
    # Matriz pseudoaleatoria determinista (puntos en el plano) más grande.
    puntos = [((i * 37) % 23 / 7.0, (i * 53) % 29 / 5.0) for i in range(15)]
    distancias = [[((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 for q in puntos] for p in puntos]
    fusiones = agrupar(distancias, metodo)
    alturas = [f["distancia"] for f in fusiones]
    for anterior, siguiente in zip(alturas, alturas[1:]):
        assert siguiente >= anterior - 1e-12


def test_corte_del_arbol():
    fusiones = agrupar(DISTANCIAS, "complete")
    assert cortar_arbol(fusiones, 5, 2) == [0, 0, 1, 1, 1]
    assert cortar_arbol(fusiones, 5, 3) == [0, 0, 1, 2, 2]
    assert cortar_arbol(fusiones, 5, 5) == [0, 1, 2, 3, 4]
    single = agrupar(DISTANCIAS, "single")
    assert cortar_arbol(single, 5, 2) == [0, 0, 0, 1, 1]


@pytest.mark.parametrize("metodo", list(METODOS))
def test_silhouette_en_rango(metodo):
    fusiones = agrupar(DISTANCIAS, metodo)
    for k in range(2, 5):
        valor = silhouette(DISTANCIAS, cortar_arbol(fusiones, 5, k))
        assert -1.0 <= valor <= 1.0


def test_silhouette_valor_a_mano():
    # Grupos {0,1} y {2,3,4}; s(0) = (b−a)/max con a=2, b=(4.4+7+7.5)/3=6.3.
    etiquetas = [0, 0, 1, 1, 1]
    s0 = (6.3 - 2.0) / 6.3
    s1 = ((2.4 + 5 + 5.5) / 3 - 2.0) / ((2.4 + 5 + 5.5) / 3)
    s2 = (3.4 - 2.85) / 3.4
    s3 = (6.0 - 1.55) / 6.0
    s4 = (6.5 - 1.8) / 6.5
    esperado = (s0 + s1 + s2 + s3 + s4) / 5
    assert silhouette(DISTANCIAS, etiquetas) == pytest.approx(esperado)


@pytest.mark.parametrize("metodo", list(METODOS))
def test_correlacion_cofenetica_en_rango(metodo):
    fusiones = agrupar(DISTANCIAS, metodo)
    valor = correlacion_cofenetica(DISTANCIAS, fusiones)
    assert -1.0 <= valor <= 1.0
    cofenetica = matriz_cofenetica(fusiones, 5)
    assert cofenetica[3][4] == pytest.approx(0.5)
    assert cofenetica[0][4] == pytest.approx(fusiones[-1]["distancia"])


def test_pearson_casos_basicos():
    assert correlacion_pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert correlacion_pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert correlacion_pearson([1, 1, 1], [1, 2, 3]) == 0.0


# ---------------------------------------------------------------- endpoint

cliente = TestClient(app)

ARTICULOS_FALSOS = [
    {"id": 1, "titulo": "A", "abstract": "machine learning models predict student performance"},
    {"id": 2, "titulo": "B", "abstract": "deep learning models predict student dropout"},
    {"id": 3, "titulo": "C", "abstract": "blockchain ledger security cryptography protocols"},
    {"id": 4, "titulo": "D", "abstract": "cryptography protocols secure blockchain networks"},
    {"id": 5, "titulo": "E", "abstract": "generative artificial intelligence chatbots education"},
    {"id": 6, "titulo": "F", "abstract": "chatbots artificial intelligence higher education"},
]


@pytest.fixture
def corpus_falso(monkeypatch, tmp_path):
    """Sustituye el corpus por seis artículos pequeños para probar la ruta."""
    ruta = tmp_path / "corpus.json"
    ruta.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(config, "RUTA_CORPUS", ruta)
    monkeypatch.setattr(servicio, "cargar_corpus", lambda: ARTICULOS_FALSOS)
    return ARTICULOS_FALSOS


def validar_respuesta(datos, n, representacion):
    """Comprueba la forma de la respuesta según el contrato."""
    assert datos["representacion"] == representacion
    assert len(datos["articulos"]) == n
    assert [m["clave"] for m in datos["metodos"]] == ["single", "complete", "average"]
    assert datos["mejor_metodo"] in ("single", "complete", "average")
    assert "cofenética" in datos["criterio"]
    for metodo in datos["metodos"]:
        assert len(metodo["fusiones"]) == n - 1
        assert metodo["fusiones"][0]["nuevo"] == n
        assert metodo["arbol"]["id"] == 2 * n - 2 and metodo["arbol"]["tamano"] == n
        assert -1 <= metodo["silhouette"] <= 1
        assert -1 <= metodo["correlacion_cofenetica"] <= 1
        assert metodo["tiempo_ms"] >= 0
        hojas, internos = [], []
        contar_nodos(metodo["arbol"], hojas, internos)
        assert len(hojas) == n and len(internos) == n - 1
        assert all("articulo_id" in h and "titulo" in h for h in hojas)


def test_endpoint_con_corpus_falso(corpus_falso):
    respuesta = cliente.get("/api/clustering", params={"k": 3})
    assert respuesta.status_code == 200
    validar_respuesta(respuesta.json(), 6, "tfidf")


def test_endpoint_sbert_con_embeddings_falsos(corpus_falso, monkeypatch, tmp_path):
    ruta = tmp_path / "embeddings.json"
    vectores = {str(a["id"]): [float(a["id"] % 3), 1.0, float(a["id"])] for a in corpus_falso}
    ruta.write_text(json.dumps({"sbert": {"vectores": vectores}}), encoding="utf-8")
    monkeypatch.setattr(config, "RUTA_EMBEDDINGS", ruta)
    respuesta = cliente.get("/api/clustering", params={"representacion": "sbert"})
    assert respuesta.status_code == 200
    validar_respuesta(respuesta.json(), 6, "sbert")


def test_endpoint_sbert_sin_embeddings_503(corpus_falso, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "RUTA_EMBEDDINGS", tmp_path / "no_existe.json")
    respuesta = cliente.get("/api/clustering", params={"representacion": "sbert"})
    assert respuesta.status_code == 503
    assert "embeddings" in respuesta.json()["detail"]


def test_endpoint_sin_corpus_503(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "RUTA_CORPUS", tmp_path / "no_existe.json")
    respuesta = cliente.get("/api/clustering")
    assert respuesta.status_code == 503


def test_endpoint_parametros_invalidos_422():
    assert cliente.get("/api/clustering", params={"k": 1}).status_code == 422
    assert cliente.get("/api/clustering", params={"k": 11}).status_code == 422
    assert cliente.get("/api/clustering", params={"representacion": "bow"}).status_code == 422


@pytest.mark.skipif(not config.RUTA_CORPUS.exists(), reason="data/corpus.json aún no existe")
def test_endpoint_corpus_real():
    respuesta = cliente.get("/api/clustering")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    validar_respuesta(datos, len(datos["articulos"]), "tfidf")
