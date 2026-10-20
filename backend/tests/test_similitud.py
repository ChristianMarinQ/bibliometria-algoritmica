"""Pruebas del Req. 1: algoritmos de similitud, servicio y endpoints."""

import json
import math

import pytest
from fastapi.testclient import TestClient

from app.algoritmos.similitud import coseno_tfidf, embeddings, jaccard, levenshtein, needleman_wunsch
from app.config import RUTA_CORPUS, RUTA_EMBEDDINGS
from app.main import app
from app.nucleo import corpus as nucleo_corpus
from app.servicios import similitud as servicio

HAY_CORPUS = RUTA_CORPUS.exists()
HAY_EMBEDDINGS = RUTA_EMBEDDINGS.exists()

CORPUS_SINTETICO = [
    {"id": 1, "titulo": "Uno", "abstract": "Machine learning models improve education outcomes for students."},
    {"id": 2, "titulo": "Dos", "abstract": "Deep learning models improve student learning outcomes in education."},
    {"id": 3, "titulo": "Tres", "abstract": "Generative artificial intelligence changes creative writing practice."},
]


@pytest.fixture
def corpus_sintetico(monkeypatch, tmp_path):
    """Sustituye el corpus y los embeddings por datos pequeños conocidos."""
    monkeypatch.setattr(nucleo_corpus, "cargar_corpus", lambda: CORPUS_SINTETICO)
    monkeypatch.setattr(servicio, "cargar_corpus", lambda: CORPUS_SINTETICO)
    ruta = tmp_path / "embeddings.json"
    datos = {
        "word2vec": {"modelo": "prueba", "dimensiones": 3,
                     "vectores": {"1": [1.0, 0.0, 0.0], "2": [1.0, 1.0, 0.0], "3": [0.0, 0.0, 1.0]},
                     "cobertura": {"1": 1.0, "2": 0.8, "3": 0.5}},
        "sbert": {"modelo": "prueba", "dimensiones": 2,
                  "vectores": {"1": [1.0, 0.0], "2": [0.6, 0.8], "3": [-1.0, 0.0]}},
    }
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    monkeypatch.setattr(servicio, "RUTA_EMBEDDINGS", ruta)
    servicio._cache_idf.clear()
    yield ruta
    servicio._cache_idf.clear()


# ---------- Levenshtein ----------

def test_levenshtein_kitten_sitting_caracteres():
    assert levenshtein.distancia_levenshtein("kitten", "sitting") == 3
    assert levenshtein.matriz_levenshtein("kitten", "sitting")[6][7] == 3


def test_levenshtein_por_palabras():
    a = ["gato", "come", "pescado", "fresco"]
    b = ["perro", "come", "pescado"]
    assert levenshtein.distancia_levenshtein(a, b) == 2
    assert levenshtein.similitud_levenshtein(a, b) == pytest.approx(0.5)
    assert levenshtein.similitud_levenshtein([], []) == 1.0


def test_levenshtein_traza():
    similitud, pasos, detalle = levenshtein.levenshtein_con_traza("kitten", "sitting")
    assert detalle["distancia"] == 3
    assert similitud == pytest.approx(1 - 3 / 7)
    assert detalle["camino"][0] == [0, 0] and detalle["camino"][-1] == [6, 7]
    assert len(detalle["matriz"]) == 7 and len(detalle["matriz"][0]) == 8
    assert detalle["truncado"] is False
    assert pasos


def test_levenshtein_traza_truncada():
    a = [f"p{i}" for i in range(20)]
    b = [f"p{i}" for i in range(15)]
    _, _, detalle = levenshtein.levenshtein_con_traza(a, b)
    assert detalle["truncado"] is True
    assert len(detalle["matriz"]) == 13 and len(detalle["matriz"][0]) == 13
    assert detalle["distancia"] == 5


# ---------- Needleman-Wunsch ----------

def test_needleman_wunsch_ejemplo_libro():
    # Ejemplo clásico (Wikipedia): GCATGCG vs GATTACA con +1/-1/-1 da puntaje 0.
    assert needleman_wunsch.puntaje_needleman_wunsch("GCATGCG", "GATTACA") == 0
    matriz = needleman_wunsch.matriz_needleman_wunsch("GCATGCG", "GATTACA")
    assert matriz[7][7] == 0
    camino, al_a, al_b = needleman_wunsch.reconstruir_alineamiento(matriz, "GCATGCG", "GATTACA")
    assert len(al_a) == len(al_b)
    # El alineamiento reconstruido debe tener exactamente el puntaje óptimo.
    puntaje = 0
    for x, y in zip(al_a, al_b):
        puntaje += -1 if x == "-" or y == "-" else (1 if x == y else -1)
    assert puntaje == 0
    assert "".join(c for c in al_a if c != "-") == "GCATGCG"
    assert camino[0] == [0, 0] and camino[-1] == [7, 7]


def test_needleman_wunsch_normalizacion():
    assert needleman_wunsch.similitud_needleman_wunsch(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    assert needleman_wunsch.similitud_needleman_wunsch(["a", "b"], ["x", "y"]) == 0.0
    assert needleman_wunsch.similitud_needleman_wunsch([], ["x"]) == 0.0
    # GCATGCG/GATTACA: (0 - (-7)) / (7 - (-7)) = 0.5
    assert needleman_wunsch.similitud_needleman_wunsch("GCATGCG", "GATTACA") == pytest.approx(0.5)


def test_needleman_wunsch_traza():
    similitud, pasos, detalle = needleman_wunsch.needleman_wunsch_con_traza("GCATGCG", "GATTACA")
    assert detalle["puntaje"] == 0
    assert detalle["parametros"] == {"match": 1, "mismatch": -1, "gap": -1}
    assert similitud == pytest.approx(0.5)
    assert len(detalle["alineamiento"]["a"]) == len(detalle["alineamiento"]["b"])


# ---------- Jaccard ----------

def test_jaccard_conjuntos_simples():
    assert jaccard.similitud_jaccard(["a", "b", "c"], ["b", "c", "d"]) == pytest.approx(2 / 4)
    assert jaccard.similitud_jaccard(["a", "a", "b"], ["a", "b"]) == 1.0
    assert jaccard.similitud_jaccard(["a"], ["b"]) == 0.0
    _, _, detalle = jaccard.jaccard_con_traza(["a", "b", "c"], ["b", "c", "d"])
    assert detalle["interseccion"] == ["b", "c"]
    assert detalle["solo_a"] == ["a"] and detalle["solo_b"] == ["d"]
    assert detalle["tam_union"] == 4


# ---------- Coseno ----------

def test_coseno_ortogonales_e_iguales():
    assert embeddings.coseno([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert embeddings.coseno([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)
    assert embeddings.coseno([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    assert embeddings.similitud_embeddings([1.0, 0.0], [-1.0, 0.0]) == 0.0
    assert embeddings.distancia_euclidiana([0.0, 0.0], [3.0, 4.0]) == pytest.approx(5.0)
    assert coseno_tfidf.similitud_coseno({"x": 1.0}, {"y": 2.0}) == 0.0
    assert coseno_tfidf.similitud_coseno({"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 4.0}) == pytest.approx(1.0)


def test_coseno_tfidf_traza():
    idf = {"gato": 1.5, "perro": 2.0, "come": 1.0}
    similitud, _, detalle = coseno_tfidf.coseno_tfidf_con_traza(["gato", "come"], ["perro", "come"], idf)
    # A = (0.75, 0, 0.5), B = (0, 1.0, 0.5): coseno = 0.25 / (0.9014 · 1.1180)
    esperado = 0.25 / (math.sqrt(0.75 ** 2 + 0.25) * math.sqrt(1.25))
    assert similitud == pytest.approx(esperado)
    assert detalle["terminos"][0]["termino"] == "come"
    assert detalle["angulo_grados"] == pytest.approx(math.degrees(math.acos(esperado)))


def test_embeddings_traza():
    similitud, _, detalle = embeddings.embeddings_con_traza([1.0, 0.0], [0.6, 0.8], "prueba", 0.9, 0.8)
    assert similitud == pytest.approx(0.6)
    assert detalle["distancia_euclidiana"] == pytest.approx(math.sqrt(0.16 + 0.64))
    assert detalle["cobertura_a"] == 0.9


# ---------- Servicio (datos sintéticos) ----------

def test_matriz_simetrica_diagonal_uno(corpus_sintetico):
    respuesta = servicio.calcular_similitudes([1, 2, 3])
    assert [r["clave"] for r in respuesta["resultados"]] == list(servicio.ALGORITMOS)
    for resultado in respuesta["resultados"]:
        matriz = resultado["matriz"]
        assert resultado["tiempo_ms"] >= 0
        for i in range(3):
            assert matriz[i][i] == 1.0
            for j in range(3):
                assert matriz[i][j] == matriz[j][i]
                assert 0.0 <= matriz[i][j] <= 1.0
    # Los abstracts 1 y 2 se parecen más entre sí que con el 3.
    tfidf = next(r for r in respuesta["resultados"] if r["clave"] == "coseno_tfidf")["matriz"]
    assert tfidf[0][1] > tfidf[0][2]


def test_servicio_sin_embeddings(corpus_sintetico, monkeypatch, tmp_path):
    monkeypatch.setattr(servicio, "RUTA_EMBEDDINGS", tmp_path / "no_existe.json")
    respuesta = servicio.calcular_similitudes([1, 2])
    assert [r["tipo"] for r in respuesta["resultados"]] == ["clasico"] * 4
    assert respuesta["avisos"]
    with pytest.raises(servicio.EmbeddingsNoDisponibles):
        servicio.calcular_similitudes([1, 2], ["sbert"])


def test_endpoints_sinteticos(corpus_sintetico, monkeypatch, tmp_path):
    cliente = TestClient(app)
    r = cliente.post("/api/similitud", json={"ids": [1, 2, 3], "algoritmos": ["jaccard", "sbert"]})
    assert r.status_code == 200
    assert len(r.json()["resultados"]) == 2
    assert cliente.post("/api/similitud", json={"ids": [1]}).status_code == 400
    assert cliente.post("/api/similitud", json={"ids": [1, 2], "algoritmos": ["xyz"]}).status_code == 400
    assert cliente.post("/api/similitud", json={"ids": [1, 99]}).status_code == 404
    for clave in servicio.ALGORITMOS:
        r = cliente.post("/api/similitud/traza", json={"id_a": 1, "id_b": 2, "algoritmo": clave})
        assert r.status_code == 200, clave
        cuerpo = r.json()
        assert set(cuerpo) == {"clave", "nombre", "tipo", "similitud", "formula", "pasos", "detalle"}
    monkeypatch.setattr(servicio, "RUTA_EMBEDDINGS", tmp_path / "no_existe.json")
    r = cliente.post("/api/similitud/traza", json={"id_a": 1, "id_b": 2, "algoritmo": "word2vec"})
    assert r.status_code == 503
    assert "generar_embeddings" in r.json()["detail"]


# ---------- Endpoints con el corpus real ----------

@pytest.mark.skipif(not HAY_CORPUS, reason="Falta data/corpus.json")
def test_endpoint_similitud_corpus_real():
    cliente = TestClient(app)
    ids = [a["id"] for a in nucleo_corpus.cargar_corpus()[:3]]
    algoritmos = ["levenshtein", "needleman_wunsch", "coseno_tfidf", "jaccard"]
    if HAY_EMBEDDINGS:
        algoritmos += ["word2vec", "sbert"]
    r = cliente.post("/api/similitud", json={"ids": ids, "algoritmos": algoritmos})
    assert r.status_code == 200
    cuerpo = r.json()
    assert [a["id"] for a in cuerpo["articulos"]] == ids
    for resultado in cuerpo["resultados"]:
        for i in range(3):
            assert resultado["matriz"][i][i] == 1.0
            for j in range(3):
                assert resultado["matriz"][i][j] == resultado["matriz"][j][i]


@pytest.mark.skipif(not HAY_CORPUS, reason="Falta data/corpus.json")
def test_endpoint_traza_corpus_real():
    cliente = TestClient(app)
    ids = [a["id"] for a in nucleo_corpus.cargar_corpus()[:2]]
    r = cliente.post("/api/similitud/traza", json={"id_a": ids[0], "id_b": ids[1], "algoritmo": "levenshtein"})
    assert r.status_code == 200
    detalle = r.json()["detalle"]
    assert len(detalle["matriz"]) <= 13
    assert detalle["distancia"] >= 0


# ---------- Regresiones de la auditoría ----------

def test_versiones_rapidas_coinciden_con_la_matriz():
    """La versión de dos filas (usada en /similitud) da lo mismo que la matriz completa de la traza."""
    import random

    generador = random.Random(7)
    for _ in range(300):
        a = [generador.choice("abc") for _ in range(generador.randint(0, 9))]
        b = [generador.choice("abc") for _ in range(generador.randint(0, 9))]
        assert levenshtein.distancia_levenshtein(a, b) == levenshtein.matriz_levenshtein(a, b)[-1][-1]
        assert (needleman_wunsch.puntaje_needleman_wunsch(a, b)
                == needleman_wunsch.matriz_needleman_wunsch(a, b)[-1][-1])
        assert (needleman_wunsch.puntaje_needleman_wunsch(a, b, 2, -3, -2)
                == needleman_wunsch.matriz_needleman_wunsch(a, b, 2, -3, -2)[-1][-1])


def test_servidor_no_depende_de_librerias_de_ia():
    """Ningún módulo de app/ importa gensim, sentence_transformers, torch ni numpy al cargarse.

    Única excepción: app/nucleo/modelos_ia.py puede importarlas dentro de funciones
    (carga perezosa de los modelos para los artículos subidos).
    """
    import ast
    from pathlib import Path

    prohibidos = {"gensim", "sentence_transformers", "torch", "numpy", "scipy", "sklearn"}
    carpeta_app = Path(__file__).resolve().parent.parent / "app"
    for ruta in carpeta_app.rglob("*.py"):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        if ruta.name == "modelos_ia.py":
            # Solo se revisan las sentencias del nivel del módulo.
            nodos = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        else:
            nodos = list(ast.walk(arbol))
        for nodo in nodos:
            if isinstance(nodo, ast.Import):
                modulos = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                modulos = [nodo.module or ""]
            else:
                continue
            for modulo in modulos:
                assert modulo.split(".")[0] not in prohibidos, f"{ruta.name} importa {modulo}"


def test_arranque_no_importa_librerias_de_ia():
    """Importar app.main en un proceso nuevo no carga gensim ni sentence_transformers."""
    import subprocess
    import sys
    from pathlib import Path

    codigo = ("import sys, app.main; "
              "print(any(m.split('.')[0] in ('gensim', 'sentence_transformers', 'torch') for m in sys.modules))")
    salida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                            cwd=Path(__file__).resolve().parent.parent, check=True)
    assert salida.stdout.strip() == "False"
