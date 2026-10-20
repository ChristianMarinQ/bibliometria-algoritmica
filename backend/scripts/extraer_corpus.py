"""Script offline: recorre los PDFs de data/articulos y genera data/corpus.json.

Uso desde la carpeta backend:
    python -m scripts.extraer_corpus
    python scripts/extraer_corpus.py
"""

import json
import sys
from pathlib import Path

# Permite ejecutar el script directamente (sin -m) agregando backend al path.
RAIZ_BACKEND = Path(__file__).resolve().parent.parent
if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from app.config import CARPETA_ARTICULOS, RUTA_CORPUS  # noqa: E402
from app.corpus.extractor import extraer_articulo  # noqa: E402


def listar_pdfs(carpeta):
    """Devuelve [(id, ruta)] de los PDFs "N. Título.pdf" ordenados por id."""
    pdfs = []
    for ruta in carpeta.glob("*.pdf"):
        numero = ruta.name.split(".", 1)[0]
        if numero.isdigit():
            pdfs.append((int(numero), ruta))
    return sorted(pdfs)


def generar_corpus():
    """Extrae todos los artículos y escribe corpus.json. Devuelve la lista generada."""
    articulos = [extraer_articulo(ruta, id_articulo) for id_articulo, ruta in listar_pdfs(CARPETA_ARTICULOS)]
    with open(RUTA_CORPUS, "w", encoding="utf-8") as archivo:
        json.dump(articulos, archivo, indent=2, ensure_ascii=False)
    return articulos


def main():
    """Genera el corpus e imprime un resumen por artículo."""
    articulos = generar_corpus()
    for articulo in articulos:
        palabras = len(articulo["abstract"].split())
        print(f"{articulo['id']:>2} | {articulo['anio']} | {len(articulo['autores'])} autores | "
              f"{palabras} palabras | {articulo['titulo'][:60]}")
    print(f"Corpus escrito en {RUTA_CORPUS} ({len(articulos)} artículos)")


if __name__ == "__main__":
    main()
