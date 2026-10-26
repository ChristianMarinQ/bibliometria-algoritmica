"""Pruebas del seguimiento: Counting, Radix y Bucket Sort y endpoints de ranking."""

import random

import pytest

from app.algoritmos.ordenamiento.bucket_sort import bucket_sort
from app.algoritmos.ordenamiento.counting_sort import counting_sort
from app.algoritmos.ordenamiento.radix_sort import radix_sort
from app.config import RUTA_CORPUS
from app.servicios.ranking import benchmark_desde_pares, construir_pares, ranking_desde_pares

ALGORITMOS = [counting_sort, radix_sort, bucket_sort]


def esperado(pares):
    """Orden de referencia: frecuencia descendente, empates alfabéticos (en tests sí se usa sorted)."""
    return sorted(pares, key=lambda par: (-par[1], par[0]))


def lista_aleatoria(generador):
    """Genera pares únicos por término, ya ordenados alfabéticamente como en el servicio."""
    n = generador.randint(0, 300)
    maximo = generador.choice([1, 5, 9, 10, 99, 100, 1000, 12345])
    conteo = {}
    for i in range(n):
        conteo[f"t{generador.randint(0, 10 * n + 10):05d}_{i}"] = generador.randint(1, maximo)
    return construir_pares(conteo)


@pytest.mark.parametrize("algoritmo", ALGORITMOS)
def test_listas_aleatorias(algoritmo):
    generador = random.Random(2024)
    for _ in range(200):
        pares = lista_aleatoria(generador)
        assert algoritmo(pares) == esperado(pares)


@pytest.mark.parametrize("algoritmo", ALGORITMOS)
def test_casos_borde(algoritmo):
    assert algoritmo([]) == []
    assert algoritmo([("unico", 7)]) == [("unico", 7)]
    iguales = [("a", 3), ("b", 3), ("c", 3), ("d", 3)]
    assert algoritmo(iguales) == iguales
    assert algoritmo([("x", 0), ("y", 1)]) == [("y", 1), ("x", 0)]


@pytest.mark.parametrize("algoritmo", ALGORITMOS)
def test_estabilidad(algoritmo):
    # Términos en orden NO alfabético: un algoritmo estable debe respetar el orden de entrada.
    pares = [("zeta", 2), ("alfa", 5), ("mu", 2), ("beta", 5), ("eta", 12), ("gamma", 2), ("pi", 12)]
    assert algoritmo(pares) == [("eta", 12), ("pi", 12), ("alfa", 5), ("beta", 5),
                                ("zeta", 2), ("mu", 2), ("gamma", 2)]


@pytest.mark.parametrize("algoritmo", ALGORITMOS)
def test_no_modifica_entrada(algoritmo):
    pares = [("b", 1), ("a", 3), ("c", 2)]
    copia = list(pares)
    algoritmo(pares)
    assert pares == copia


def test_servicio_sin_corpus():
    pares = construir_pares({"learning": 9, "data": 9, "model": 4, "ai": 1})
    datos = ranking_desde_pares(pares, 23, top=3, repeticiones=1)
    assert datos["coinciden"] is True
    assert datos["frecuencia_maxima"] == 9
    assert [a["clave"] for a in datos["algoritmos"]] == ["counting_sort", "radix_sort", "bucket_sort"]
    assert datos["algoritmos"][0]["top"] == [
        {"termino": "data", "frecuencia": 9},
        {"termino": "learning", "frecuencia": 9},
        {"termino": "model", "frecuencia": 4},
    ]
    banco = benchmark_desde_pares(pares, repeticiones=2)
    assert [fila["n"] for fila in banco["escalamiento"]] == [4, 8, 16, 32]


requiere_corpus = pytest.mark.skipif(not RUTA_CORPUS.exists(), reason="data/corpus.json no existe todavía")


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app)


@requiere_corpus
def test_endpoint_ranking(cliente):
    respuesta = cliente.get("/api/ranking", params={"top": 15})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["coinciden"] is True
    assert len(datos["algoritmos"]) == 3
    for algoritmo in datos["algoritmos"]:
        assert set(algoritmo) == {"clave", "nombre", "tiempo_ms", "complejidad", "top"}
        assert len(algoritmo["top"]) == min(15, datos["terminos_distintos"])
    top = datos["algoritmos"][0]["top"]
    assert top[0]["frecuencia"] == datos["frecuencia_maxima"]
    assert top == sorted(top, key=lambda t: (-t["frecuencia"], t["termino"]))


@requiere_corpus
def test_endpoint_benchmark(cliente):
    respuesta = cliente.get("/api/ranking/benchmark", params={"repeticiones": 2})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["repeticiones"] == 2
    assert [fila["n"] for fila in datos["escalamiento"]] == [datos["n"] * f for f in (1, 2, 4, 8)]
    for algoritmo in datos["algoritmos"]:
        assert algoritmo["minimo_ms"] <= algoritmo["promedio_ms"] <= algoritmo["maximo_ms"]


def test_validacion_parametros(cliente):
    assert cliente.get("/api/ranking", params={"top": 0}).status_code == 422
    assert cliente.get("/api/ranking", params={"top": 101}).status_code == 422
    assert cliente.get("/api/ranking/benchmark", params={"repeticiones": 501}).status_code == 422


def test_escalamiento_limita_repeticiones(monkeypatch):
    """El escalamiento usa como máximo MAXIMO_REPETICIONES_ESCALAMIENTO ejecuciones por medición."""
    from app.servicios import ranking

    llamadas = []
    original = ranking.medir

    def medir_espia(funcion, *args, repeticiones=1, **kwargs):
        llamadas.append(repeticiones)
        return original(funcion, *args, repeticiones=repeticiones, **kwargs)

    monkeypatch.setattr(ranking, "medir", medir_espia)
    pares = construir_pares({"learning": 9, "data": 9, "model": 4})
    ranking.benchmark_desde_pares(pares, repeticiones=200)
    # 200 mediciones individuales por algoritmo + 4 factores × 3 algoritmos con tope
    assert llamadas.count(ranking.MAXIMO_REPETICIONES_ESCALAMIENTO) == 12
    assert max(llamadas) == ranking.MAXIMO_REPETICIONES_ESCALAMIENTO


def test_preprocesamiento_conserva_la_sigla_ai():
    """La sigla "AI" se conserva aunque tenga menos de tres letras; las palabras cortas comunes no."""
    from app.nucleo.preprocesamiento import preprocesar
    assert preprocesar("AI in education is a key topic of AI research") == [
        "ai", "education", "key", "topic", "ai", "research"]
