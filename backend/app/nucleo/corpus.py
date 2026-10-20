"""Acceso al corpus combinado: 20 artículos base (data/corpus.json) + artículos subidos."""

import json
from functools import lru_cache

from app.config import RUTA_CORPUS
from app.nucleo import almacen_subidos


def clave_corpus():
    """Clave que cambia cuando cambia el corpus (rutas, fechas de modificación y versión).

    Los servicios la usan en sus cachés. Lanza FileNotFoundError si falta corpus.json.
    """
    marca_base = almacen_subidos.marca_archivo(RUTA_CORPUS)
    if marca_base is None:
        raise FileNotFoundError(str(RUTA_CORPUS))
    ruta_subidos = almacen_subidos.ruta_articulos()
    return (str(RUTA_CORPUS), marca_base, str(ruta_subidos),
            almacen_subidos.marca_archivo(ruta_subidos), almacen_subidos.version())


@lru_cache(maxsize=1)
def _leer_corpus(clave):
    """Lee el corpus base y los subidos para una clave dada (en caché)."""
    with open(clave[0], encoding="utf-8") as archivo:
        base = json.load(archivo)
    articulos = [dict(articulo, origen="base") for articulo in base]
    for articulo in almacen_subidos.leer_articulos():
        articulos.append(dict(articulo, origen="subido"))
    return articulos


def cargar_corpus():
    """Devuelve el corpus combinado (base + subidos), en caché hasta que cambie.

    Cada artículo tiene la forma:
    {"id": int, "archivo": str, "titulo": str, "autores": [str], "anio": int|None,
     "revista": str, "abstract": str, "origen": "base"|"subido"}
    """
    return _leer_corpus(clave_corpus())


def invalidar_corpus():
    """Olvida el corpus en caché (se vuelve a leer en la siguiente llamada)."""
    _leer_corpus.cache_clear()
    almacen_subidos.incrementar_version()


# Compatibilidad con el uso anterior de lru_cache (cargar_corpus.cache_clear()).
cargar_corpus.cache_clear = invalidar_corpus


def cantidad_base():
    """Cantidad de artículos base del corpus."""
    return sum(1 for articulo in cargar_corpus() if articulo["origen"] == "base")


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
