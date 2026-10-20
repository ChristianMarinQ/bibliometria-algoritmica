"""Pruebas del Req. 3: KMP, Boyer-Moore, Rabin-Karp, servicio y endpoints de búsqueda."""

import random

import pytest

from app.algoritmos.busqueda import boyer_moore, kmp, rabin_karp
from app.config import RUTA_CORPUS

ALGORITMOS = [kmp, boyer_moore, rabin_karp]


def busqueda_ingenua(texto, patron):
    """Referencia O(n·m): compara el patrón en cada posición carácter a carácter."""
    posiciones = []
    for s in range(len(texto) - len(patron) + 1):
        j = 0
        while j < len(patron) and texto[s + j] == patron[j]:
            j += 1
        if j == len(patron):
            posiciones.append(s)
    return posiciones


@pytest.mark.parametrize("modulo", ALGORITMOS)
@pytest.mark.parametrize("texto, patron, esperado", [
    ("aaaaaa", "aaaa", [0, 1, 2]),
    ("learning analytics", "learning", [0]),
    ("deep learning", "learning", [5]),
    ("abcdef", "xyz", []),
    ("abc", "abcd", []),
    ("banana", "a", [1, 3, 5]),
    ("x", "x", [0]),
    ("abababab", "abab", [0, 2, 4]),
    ("", "a", []),
])
def test_casos_basicos(modulo, texto, patron, esperado):
    posiciones, comparaciones = modulo.buscar(texto, patron)
    assert posiciones == esperado
    assert comparaciones >= 0


def test_lps_ababaca():
    assert kmp.preprocesar("ababaca") == [0, 0, 1, 2, 3, 0, 1]
    lps, pasos = kmp.preprocesar_con_traza("ababaca")
    assert lps == [0, 0, 1, 2, 3, 0, 1]
    assert len(pasos) > 0


def test_caracter_malo_ultima_posicion():
    assert boyer_moore.tabla_caracter_malo("learning") == {
        "l": 0, "e": 1, "a": 2, "r": 3, "n": 6, "i": 5, "g": 7,
    }


def sufijo_bueno_por_definicion(patron):
    """Referencia: menor salto d que vuelve a alinear el sufijo bueno (regla fuerte)."""
    m = len(patron)
    tabla = [0] * (m + 1)
    for j in range(-1, m):
        d = 1
        while True:
            valido = True
            for k in range(j + 1, m):
                if k - d >= 0 and patron[k - d] != patron[k]:
                    valido = False
                    break
            if valido and j >= 0 and j - d >= 0 and patron[j - d] == patron[j]:
                valido = False
            if valido:
                break
            d += 1
        tabla[j + 1] = d
    return tabla


def test_sufijo_bueno_contra_definicion():
    generador = random.Random(7)
    patrones = ["abbabab", "ababaca", "learning", "aaaa", "abcab"]
    for _ in range(100):
        patrones.append("".join(generador.choice("ab") for _ in range(generador.randint(1, 8))))
    for patron in patrones:
        assert boyer_moore.tabla_sufijo_bueno(patron)[0] == sufijo_bueno_por_definicion(patron), patron


@pytest.mark.parametrize("modulo", ALGORITMOS)
def test_patron_vacio_lanza_error(modulo):
    with pytest.raises(ValueError):
        modulo.buscar("texto", "")


def test_aleatorio_contra_ingenua():
    generador = random.Random(2024)
    for _ in range(200):
        alfabeto = "ab" if generador.random() < 0.5 else "abcd "
        texto = "".join(generador.choice(alfabeto) for _ in range(generador.randint(0, 120)))
        patron = "".join(generador.choice(alfabeto) for _ in range(generador.randint(1, 6)))
        esperado = busqueda_ingenua(texto, patron)
        for modulo in ALGORITMOS:
            assert modulo.buscar(texto, patron)[0] == esperado, (modulo.NOMBRE, texto, patron)
        # La traza debe encontrar lo mismo y contar igual que la búsqueda normal
        assert kmp.buscar_con_traza(texto, patron)["posiciones"] == esperado
        assert boyer_moore.buscar_con_traza(texto, patron)["posiciones"] == esperado
        assert rabin_karp.buscar_con_traza(texto, patron)["posiciones"] == esperado
        assert kmp.buscar_con_traza(texto, patron)["total_comparaciones"] == kmp.buscar(texto, patron)[1]
        assert boyer_moore.buscar_con_traza(texto, patron)["total_comparaciones"] == boyer_moore.buscar(texto, patron)[1]


def test_rabin_karp_colision_sin_falsos_positivos():
    # Con módulo 3 casi todas las ventanas colisionan con el hash del patrón
    texto = "the quick brown fox jumps over the lazy dog " * 3
    patron = "fox"
    posiciones, _ = rabin_karp.buscar(texto, patron, modulo=3)
    assert posiciones == busqueda_ingenua(texto, patron)
    traza = rabin_karp.buscar_con_traza(texto, patron, modulo=3)
    assert traza["posiciones"] == busqueda_ingenua(texto, patron)
    colisiones = [paso for paso in traza["pasos"] if paso["colision"]]
    assert len(colisiones) > 0
    for paso in colisiones:
        assert paso["coincidencia"] is False
        assert paso["hash_ventana"] == traza["preprocesamiento"]["hash_patron"]


def test_rabin_karp_traza_modulo_101():
    texto = "learning analytics and machine learning in higher education learning"
    traza = rabin_karp.buscar_con_traza(texto, "learning")
    pre = traza["preprocesamiento"]
    assert pre["base"] == 256 and pre["modulo"] == 101
    assert pre["h"] == pow(256, 7, 101)
    assert traza["posiciones"] == busqueda_ingenua(texto, "learning")
    for paso in traza["pasos"]:
        assert 0 <= paso["hash_ventana"] < 101


def test_estructura_traza():
    for modulo in ALGORITMOS:
        traza = modulo.buscar_con_traza("abracadabra", "abra")
        assert traza["clave"] == modulo.CLAVE
        assert traza["posiciones"] == [0, 7]
        for paso in traza["pasos"]:
            assert set(["alineacion", "comparaciones", "coincidencia", "desplazamiento", "motivo", "hash_ventana"]) <= set(paso)
            for comp in paso["comparaciones"]:
                assert set(comp) == {"i", "j", "igual"}
    pre_bm = boyer_moore.buscar_con_traza("abracadabra", "abra")["preprocesamiento"]
    assert pre_bm["caracter_malo"] == {"a": 3, "b": 1, "r": 2}
    assert len(pre_bm["sufijo_bueno"]) == 5


def test_minusculas_conserva_longitud():
    from app.servicios.busqueda import a_minusculas
    assert a_minusculas("Learning ANALYTICS") == "learning analytics"
    assert len(a_minusculas("İstanbul")) == len("İstanbul")


# --- Endpoints (requieren data/corpus.json) ---

requiere_corpus = pytest.mark.skipif(not RUTA_CORPUS.exists(), reason="Falta data/corpus.json")


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@requiere_corpus
def test_endpoint_busqueda(cliente):
    respuesta = cliente.post("/api/busqueda", json={"patron": "learning", "ids": None, "distinguir_mayusculas": False})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["patron"] == "learning"
    assert [a["clave"] for a in datos["algoritmos"]] == ["kmp", "boyer_moore", "rabin_karp"]
    assert datos["coinciden"] is True
    for algoritmo in datos["algoritmos"]:
        assert algoritmo["tiempo_preprocesamiento_ms"] > 0
        assert algoritmo["tiempo_busqueda_ms"] > 0
    totales = {a["total_coincidencias"] for a in datos["algoritmos"]}
    assert len(totales) == 1
    for resultado in datos["resultados"]:
        assert len(resultado["posiciones"]) > 0
        for fragmento in resultado["fragmentos"]:
            assert fragmento["coincidencia"].lower() == "learning"


@requiere_corpus
def test_endpoint_busqueda_errores(cliente):
    assert cliente.post("/api/busqueda", json={"patron": ""}).status_code == 400
    assert cliente.post("/api/busqueda", json={"patron": "a" * 101}).status_code == 400
    assert cliente.post("/api/busqueda", json={"patron": "ai", "ids": [9999]}).status_code == 404


@requiere_corpus
def test_endpoint_traza(cliente):
    for clave in ["kmp", "boyer_moore", "rabin_karp"]:
        respuesta = cliente.post("/api/busqueda/traza", json={
            "patron": "learning", "algoritmo": clave, "articulo_id": 1, "max_caracteres": 300,
        })
        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert datos["clave"] == clave
        assert len(datos["texto"]) <= 300
        assert datos["posiciones"] == busqueda_ingenua(datos["texto"], "learning")
    assert cliente.post("/api/busqueda/traza", json={
        "patron": "learning", "algoritmo": "kmp", "articulo_id": 9999}).status_code == 404
    assert cliente.post("/api/busqueda/traza", json={
        "patron": "", "algoritmo": "kmp", "articulo_id": 1}).status_code == 400
