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
from app.nucleo.modelos_ia import (  # noqa: E402
    LIMITE_WORD2VEC, MODELO_SBERT, MODELO_WORD2VEC, cargar_sbert, cargar_word2vec, sbert_abstracts,
    word2vec_abstract,
)


def generar_word2vec(corpus, nombre, limite=None):
    """Vector promedio de las palabras preprocesadas de cada abstract."""
    print(f"Cargando Word2Vec '{nombre}' (límite de palabras: {limite or 'sin límite'})...")
    modelo = cargar_word2vec(nombre, limite)
    vectores = {}
    cobertura = {}
    for articulo in corpus:
        vector, fraccion = word2vec_abstract(articulo["abstract"], modelo)
        vectores[str(articulo["id"])] = vector
        cobertura[str(articulo["id"])] = fraccion
    return {"modelo": os.path.basename(nombre), "dimensiones": modelo.vector_size,
            "vectores": vectores, "cobertura": cobertura}


def generar_sbert(corpus, nombre):
    """Embedding de oración de cada abstract original con sentence-transformers."""
    print(f"Cargando Sentence-BERT '{nombre}'...")
    modelo = cargar_sbert(nombre)
    matriz = sbert_abstracts([articulo["abstract"] for articulo in corpus], modelo)
    vectores = {}
    for articulo, vector in zip(corpus, matriz):
        vectores[str(articulo["id"])] = vector
    return {"modelo": nombre, "dimensiones": int(len(matriz[0])), "vectores": vectores}


def main():
    """Lee el corpus, calcula ambos embeddings y escribe el archivo de salida."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--w2v", default=MODELO_WORD2VEC,
                        help="Nombre de modelo gensim-data o ruta a un archivo KeyedVectors/word2vec")
    parser.add_argument("--w2v-limite", type=int, default=LIMITE_WORD2VEC,
                        help="Cargar solo las N palabras más frecuentes del modelo (0 = todas)")
    parser.add_argument("--sbert", default=MODELO_SBERT, help="Modelo de sentence-transformers")
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
