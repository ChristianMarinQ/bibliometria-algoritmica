"""Acceso de solo lectura al corpus extraído (data/corpus.json)."""

import json
from functools import lru_cache

from app.config import RUTA_CORPUS


@lru_cache(maxsize=1)
def cargar_corpus():
    """Lee corpus.json una sola vez y lo mantiene en memoria.

    Cada artículo tiene la forma:
    {"id": int, "archivo": str, "titulo": str, "autores": [str], "anio": int|None,
     "revista": str, "abstract": str}
    """
    with open(RUTA_CORPUS, encoding="utf-8") as archivo:
        return json.load(archivo)


def obtener_articulo(id_articulo):
    """Busca un artículo por su id. Devuelve None si no existe."""
    for articulo in cargar_corpus():
        if articulo["id"] == id_articulo:
            return articulo
    return None


def obtener_articulos(ids):
    """Devuelve los artículos en el mismo orden de los ids recibidos."""
    resultado = []
    for id_articulo in ids:
        articulo = obtener_articulo(id_articulo)
        if articulo is None:
            raise KeyError(f"No existe el artículo con id {id_articulo}")
        resultado.append(articulo)
    return resultado
