"""Servicio del Req. 1: matrices de similitud entre N artículos y trazas paso a paso.

Une el corpus, el preprocesamiento compartido, los algoritmos de similitud y la
medición de tiempos. Los embeddings de IA se leen de data/embeddings.json.
"""

import json
import os

from app.algoritmos.similitud import coseno_tfidf, embeddings, jaccard, levenshtein, needleman_wunsch
from app.config import RUTA_EMBEDDINGS
from app.nucleo.corpus import cargar_corpus, obtener_articulos
from app.nucleo.medicion import medir
from app.nucleo.preprocesamiento import preprocesar
from app.nucleo.vectorizacion import frecuencia_inversa

# Catálogo de algoritmos en el orden en que se reportan.
ALGORITMOS = {
    "levenshtein": {"nombre": "Levenshtein", "tipo": "clasico",
                    "formula": "sim = 1 - d / max(|A|, |B|)"},
    "needleman_wunsch": {"nombre": "Needleman-Wunsch", "tipo": "clasico",
                         "formula": "sim = (S - S_min) / (S_max - S_min), S_max = min(n,m) - |n-m|, S_min = -max(n,m)"},
    "coseno_tfidf": {"nombre": "Coseno TF-IDF", "tipo": "clasico",
                     "formula": "cos(θ) = (A · B) / (‖A‖ · ‖B‖), peso = TF · IDF"},
    "jaccard": {"nombre": "Jaccard", "tipo": "clasico",
                "formula": "J(A, B) = |A ∩ B| / |A ∪ B|"},
    "word2vec": {"nombre": "Word2Vec", "tipo": "ia",
                 "formula": "cos(θ) = (a · b) / (‖a‖ · ‖b‖), d = ‖a - b‖ (vector promedio de palabras)"},
    "sbert": {"nombre": "Sentence-BERT", "tipo": "ia",
              "formula": "cos(θ) = (a · b) / (‖a‖ · ‖b‖), d = ‖a - b‖ (embedding de oración)"},
}

MENSAJE_SIN_EMBEDDINGS = "Embeddings no generados; ejecute scripts/generar_embeddings.py"


class EmbeddingsNoDisponibles(Exception):
    """Se lanza cuando se pide un algoritmo de IA y no hay vectores precalculados."""


# Caché de embeddings: se invalida si el archivo cambia (fecha de modificación).
_cache_embeddings = {"mtime": None, "datos": None}
_cache_tokens = {}
_cache_idf = {}


def cargar_embeddings():
    """Lee data/embeddings.json (con caché por fecha de modificación). Devuelve None si no existe."""
    if not os.path.exists(RUTA_EMBEDDINGS):
        return None
    mtime = os.path.getmtime(RUTA_EMBEDDINGS)
    if _cache_embeddings["mtime"] != mtime:
        with open(RUTA_EMBEDDINGS, encoding="utf-8") as archivo:
            _cache_embeddings["datos"] = json.load(archivo)
        _cache_embeddings["mtime"] = mtime
    return _cache_embeddings["datos"]


def tokens_articulo(articulo):
    """Tokens preprocesados del abstract de un artículo (en caché por id)."""
    clave = (articulo["id"], articulo["abstract"])
    if clave not in _cache_tokens:
        _cache_tokens[clave] = preprocesar(articulo["abstract"])
    return _cache_tokens[clave]


def idf_corpus():
    """IDF calculado sobre todos los abstracts del corpus, para que los pesos sean estables."""
    corpus = cargar_corpus()
    clave = id(corpus)
    if clave not in _cache_idf:
        _cache_idf.clear()
        _cache_idf[clave] = frecuencia_inversa([tokens_articulo(a) for a in corpus])
    return _cache_idf[clave]


def modelo_embeddings(clave):
    """Devuelve la sección del modelo (word2vec o sbert) o lanza EmbeddingsNoDisponibles."""
    datos = cargar_embeddings()
    if datos is None or clave not in datos:
        raise EmbeddingsNoDisponibles(MENSAJE_SIN_EMBEDDINGS)
    return datos[clave]


def vector_articulo(modelo, id_articulo):
    """Vector precalculado de un artículo; si falta, los embeddings están desactualizados."""
    vector = modelo["vectores"].get(str(id_articulo))
    if vector is None:
        raise EmbeddingsNoDisponibles(
            f"El artículo {id_articulo} no tiene embedding; vuelva a ejecutar scripts/generar_embeddings.py"
        )
    return vector


def representaciones(clave, articulos):
    """Prepara la entrada de cada algoritmo (fuera de la medición de tiempo) y su función de similitud."""
    if clave in ("levenshtein", "needleman_wunsch", "jaccard"):
        funciones = {
            "levenshtein": levenshtein.similitud_levenshtein,
            "needleman_wunsch": needleman_wunsch.similitud_needleman_wunsch,
            "jaccard": jaccard.similitud_jaccard,
        }
        return [tokens_articulo(a) for a in articulos], funciones[clave]
    if clave == "coseno_tfidf":
        idf = idf_corpus()
        vectores = [coseno_tfidf.vector_tfidf(tokens_articulo(a), idf) for a in articulos]
        return vectores, coseno_tfidf.similitud_coseno
    modelo = modelo_embeddings(clave)
    vectores = [vector_articulo(modelo, a["id"]) for a in articulos]
    return vectores, embeddings.similitud_embeddings


def matriz_similitud(entradas, funcion):
    """Matriz N×N simétrica con diagonal 1; solo se calcula el triángulo superior.

    Complejidad: O(N² · C), con C el costo de una comparación.
    """
    n = len(entradas)
    matriz = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            valor = funcion(entradas[i], entradas[j])
            matriz[i][j] = valor
            matriz[j][i] = valor
    return matriz


def validar_algoritmos(algoritmos):
    """Lanza ValueError si alguna clave no pertenece al catálogo."""
    for clave in algoritmos:
        if clave not in ALGORITMOS:
            raise ValueError(f"Algoritmo desconocido: '{clave}'. Opciones: {', '.join(ALGORITMOS)}")


def calcular_similitudes(ids, algoritmos=None):
    """Calcula la matriz de similitud de los artículos para cada algoritmo, con su tiempo en ms.

    Si no se indican algoritmos se usan todos; en ese caso, si faltan los
    embeddings, se omiten los de IA y se agrega un aviso en vez de fallar.
    Lanza ValueError (entrada inválida), KeyError (id inexistente) o EmbeddingsNoDisponibles.
    """
    if ids is None or len(ids) < 2:
        raise ValueError("Se requieren al menos 2 ids de artículos")
    explicitos = algoritmos is not None and len(algoritmos) > 0
    claves = list(algoritmos) if explicitos else list(ALGORITMOS)
    validar_algoritmos(claves)
    articulos = obtener_articulos(ids)

    resultados = []
    avisos = []
    for clave in claves:
        info = ALGORITMOS[clave]
        try:
            entradas, funcion = representaciones(clave, articulos)
        except EmbeddingsNoDisponibles as error:
            if explicitos:
                raise
            avisos.append(f"{info['nombre']}: {error}")
            continue
        matriz, tiempo_ms = medir(matriz_similitud, entradas, funcion)
        resultados.append({
            "clave": clave,
            "nombre": info["nombre"],
            "tipo": info["tipo"],
            "matriz": [[round(valor, 6) for valor in fila] for fila in matriz],
            "tiempo_ms": tiempo_ms,
        })

    respuesta = {
        "articulos": [{"id": a["id"], "titulo": a["titulo"]} for a in articulos],
        "resultados": resultados,
    }
    if avisos:
        respuesta["avisos"] = avisos
    return respuesta


def calcular_traza(id_a, id_b, algoritmo):
    """Demostración paso a paso de un algoritmo entre dos artículos (formato del contrato).

    Lanza ValueError, KeyError o EmbeddingsNoDisponibles igual que calcular_similitudes.
    """
    validar_algoritmos([algoritmo])
    articulo_a, articulo_b = obtener_articulos([id_a, id_b])
    tokens_a = tokens_articulo(articulo_a)
    tokens_b = tokens_articulo(articulo_b)

    if algoritmo == "levenshtein":
        similitud, pasos, detalle = levenshtein.levenshtein_con_traza(tokens_a, tokens_b)
    elif algoritmo == "needleman_wunsch":
        similitud, pasos, detalle = needleman_wunsch.needleman_wunsch_con_traza(tokens_a, tokens_b)
    elif algoritmo == "coseno_tfidf":
        similitud, pasos, detalle = coseno_tfidf.coseno_tfidf_con_traza(tokens_a, tokens_b, idf_corpus())
    elif algoritmo == "jaccard":
        similitud, pasos, detalle = jaccard.jaccard_con_traza(tokens_a, tokens_b)
    else:
        modelo = modelo_embeddings(algoritmo)
        vector_a = vector_articulo(modelo, id_a)
        vector_b = vector_articulo(modelo, id_b)
        cobertura_a = cobertura_b = None
        if algoritmo == "word2vec":
            cobertura = modelo.get("cobertura", {})
            cobertura_a = cobertura.get(str(id_a), 0.0)
            cobertura_b = cobertura.get(str(id_b), 0.0)
        similitud, pasos, detalle = embeddings.embeddings_con_traza(
            vector_a, vector_b, modelo.get("modelo", algoritmo), cobertura_a, cobertura_b
        )

    if algoritmo in ("levenshtein", "needleman_wunsch", "coseno_tfidf", "jaccard"):
        pasos.insert(0, "Texto: se trabaja sobre el abstract preprocesado (minúsculas, sin signos, "
                        "sin palabras vacías ni palabras de menos de 3 letras).")

    info = ALGORITMOS[algoritmo]
    return {
        "clave": algoritmo,
        "nombre": info["nombre"],
        "tipo": info["tipo"],
        "similitud": round(similitud, 6),
        "formula": info["formula"],
        "pasos": pasos,
        "detalle": detalle,
    }
