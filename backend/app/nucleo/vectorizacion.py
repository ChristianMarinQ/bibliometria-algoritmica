"""Vectorización TF-IDF implementada desde cero.

Se usa en la similitud del coseno (Req. 1) y en el clustering (Req. 2).
Los vectores se representan como diccionarios dispersos {termino: peso}.
"""

import math


def frecuencia_termino(tokens):
    """TF normalizado: apariciones del término / total de términos del documento."""
    conteo = {}
    for token in tokens:
        conteo[token] = conteo.get(token, 0) + 1
    total = len(tokens)
    tf = {}
    for termino in conteo:
        tf[termino] = conteo[termino] / total if total else 0.0
    return tf


def frecuencia_inversa(documentos_tokens):
    """IDF suavizado: ln((1 + N) / (1 + df)) + 1, igual que en la literatura clásica.

    El suavizado evita divisiones por cero y que un término presente en
    todos los documentos tenga peso exactamente cero.
    """
    n = len(documentos_tokens)
    df = {}
    for tokens in documentos_tokens:
        for termino in set(tokens):
            df[termino] = df.get(termino, 0) + 1
    idf = {}
    for termino in df:
        idf[termino] = math.log((1 + n) / (1 + df[termino])) + 1
    return idf


def tfidf(documentos_tokens):
    """Calcula los vectores TF-IDF dispersos de cada documento.

    Devuelve (vectores, idf) donde vectores es una lista de diccionarios.
    """
    idf = frecuencia_inversa(documentos_tokens)
    vectores = []
    for tokens in documentos_tokens:
        tf = frecuencia_termino(tokens)
        vector = {}
        for termino in tf:
            vector[termino] = tf[termino] * idf[termino]
        vectores.append(vector)
    return vectores, idf


def producto_punto(a, b):
    """Producto punto entre dos vectores dispersos (diccionarios)."""
    if len(a) > len(b):
        a, b = b, a
    total = 0.0
    for termino in a:
        if termino in b:
            total += a[termino] * b[termino]
    return total


def norma(vector):
    """Norma euclidiana de un vector disperso."""
    total = 0.0
    for termino in vector:
        total += vector[termino] * vector[termino]
    return math.sqrt(total)


def coseno_dispersos(a, b):
    """Similitud del coseno entre dos vectores dispersos."""
    na = norma(a)
    nb = norma(b)
    if na == 0 or nb == 0:
        return 0.0
    return producto_punto(a, b) / (na * nb)
