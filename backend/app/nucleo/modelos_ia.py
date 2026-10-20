"""Funciones compartidas para calcular embeddings (script offline y servidor).

gensim y sentence_transformers solo se importan dentro de las funciones de carga,
así importar este módulo no exige tener instaladas las librerías de IA.
"""

import os

from app.nucleo.preprocesamiento import preprocesar

MODELO_WORD2VEC = "word2vec-google-news-300"
LIMITE_WORD2VEC = 500000
MODELO_SBERT = "all-MiniLM-L6-v2"
DECIMALES = 6


def cargar_word2vec(nombre=MODELO_WORD2VEC, limite=LIMITE_WORD2VEC):
    """Carga un modelo gensim KeyedVectors desde una ruta local o por nombre de gensim-data.

    `limite` carga solo las primeras N palabras (los modelos word2vec vienen
    ordenados por frecuencia), lo que reduce mucho la memoria necesaria.
    """
    from gensim.models import KeyedVectors

    if not os.path.exists(nombre):
        import gensim.downloader
        ruta = gensim.downloader.load(nombre, return_path=True)
        # Los modelos word2vec de gensim-data se distribuyen en formato binario .gz
        if ruta.endswith(".gz") and "word2vec" in nombre:
            return KeyedVectors.load_word2vec_format(ruta, binary=True, limit=limite)
        return gensim.downloader.load(nombre)
    if nombre.endswith(".bin") or nombre.endswith(".bin.gz"):
        return KeyedVectors.load_word2vec_format(nombre, binary=True, limit=limite)
    if nombre.endswith(".txt") or nombre.endswith(".vec") or nombre.endswith(".gz"):
        return KeyedVectors.load_word2vec_format(nombre, binary=False, limit=limite)
    return KeyedVectors.load(nombre)


def cargar_sbert(nombre=MODELO_SBERT):
    """Carga un modelo de sentence-transformers por nombre."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(nombre)


def vector_promedio(tokens, modelo):
    """Promedio de los vectores de los tokens presentes en el modelo. Devuelve (vector, cobertura)."""
    dimensiones = modelo.vector_size
    suma = [0.0] * dimensiones
    encontrados = 0
    for token in tokens:
        if token in modelo.key_to_index:
            vector = modelo[token]
            for k in range(dimensiones):
                suma[k] += float(vector[k])
            encontrados += 1
    if encontrados > 0:
        suma = [valor / encontrados for valor in suma]
    cobertura = encontrados / len(tokens) if tokens else 0.0
    return suma, cobertura


def word2vec_abstract(abstract, modelo):
    """Vector Word2Vec redondeado de un abstract preprocesado. Devuelve (vector, cobertura)."""
    vector, cobertura = vector_promedio(preprocesar(abstract), modelo)
    return [round(v, DECIMALES) for v in vector], round(cobertura, 4)


def sbert_abstracts(abstracts, modelo):
    """Embeddings SBERT redondeados de una lista de abstracts (texto original)."""
    matriz = modelo.encode(abstracts, show_progress_bar=False)
    return [[round(float(v), DECIMALES) for v in vector] for vector in matriz]
