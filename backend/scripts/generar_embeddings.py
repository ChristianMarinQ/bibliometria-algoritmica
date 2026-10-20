"""Genera data/embeddings.json con los vectores de Word2Vec y Sentence-BERT de cada abstract.

Uso (desde la carpeta backend):
    python scripts/generar_embeddings.py [--w2v word2vec-google-news-300] [--sbert all-MiniLM-L6-v2]
"""

import argparse
import json
import os
import sys

# Permite importar el paquete app al ejecutar el script directamente.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import RUTA_CORPUS, RUTA_EMBEDDINGS  # noqa: E402
from app.nucleo.preprocesamiento import preprocesar  # noqa: E402

DECIMALES = 6


def cargar_word2vec(nombre, limite=None):
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


def generar_word2vec(corpus, nombre, limite=None):
    """Vector promedio de las palabras preprocesadas de cada abstract."""
    print(f"Cargando Word2Vec '{nombre}' (límite de palabras: {limite or 'sin límite'})...")
    modelo = cargar_word2vec(nombre, limite)
    vectores = {}
    cobertura = {}
    for articulo in corpus:
        vector, fraccion = vector_promedio(preprocesar(articulo["abstract"]), modelo)
        vectores[str(articulo["id"])] = [round(v, DECIMALES) for v in vector]
        cobertura[str(articulo["id"])] = round(fraccion, 4)
    return {"modelo": os.path.basename(nombre), "dimensiones": modelo.vector_size,
            "vectores": vectores, "cobertura": cobertura}


def generar_sbert(corpus, nombre):
    """Embedding de oración de cada abstract original con sentence-transformers."""
    from sentence_transformers import SentenceTransformer

    print(f"Cargando Sentence-BERT '{nombre}'...")
    modelo = SentenceTransformer(nombre)
    textos = [articulo["abstract"] for articulo in corpus]
    matriz = modelo.encode(textos, show_progress_bar=False)
    vectores = {}
    for articulo, vector in zip(corpus, matriz):
        vectores[str(articulo["id"])] = [round(float(v), DECIMALES) for v in vector]
    return {"modelo": nombre, "dimensiones": int(len(matriz[0])), "vectores": vectores}


def main():
    """Lee el corpus, calcula ambos embeddings y escribe el archivo de salida."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--w2v", default="word2vec-google-news-300",
                        help="Nombre de modelo gensim-data o ruta a un archivo KeyedVectors/word2vec")
    parser.add_argument("--w2v-limite", type=int, default=500000,
                        help="Cargar solo las N palabras más frecuentes del modelo (0 = todas)")
    parser.add_argument("--sbert", default="all-MiniLM-L6-v2", help="Modelo de sentence-transformers")
    parser.add_argument("--salida", default=str(RUTA_EMBEDDINGS), help="Ruta del JSON de salida")
    argumentos = parser.parse_args()

    with open(RUTA_CORPUS, encoding="utf-8") as archivo:
        corpus = json.load(archivo)
    print(f"Corpus: {len(corpus)} artículos")

    resultado = {
        "word2vec": generar_word2vec(corpus, argumentos.w2v, argumentos.w2v_limite or None),
        "sbert": generar_sbert(corpus, argumentos.sbert),
    }
    with open(argumentos.salida, "w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo)
    coberturas = list(resultado["word2vec"]["cobertura"].values())
    promedio = sum(coberturas) / len(coberturas) if coberturas else 0.0
    print(f"Escrito {argumentos.salida} (cobertura media Word2Vec: {promedio:.1%})")


if __name__ == "__main__":
    main()
