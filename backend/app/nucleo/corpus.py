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


def estadisticas_corpus(articulos):
    """Resumen estadístico básico de una lista de artículos del corpus.

    Calcula sobre los abstracts de los artículos recibidos:
    - total              : número de artículos.
    - tokens_promedio    : promedio de tokens preprocesados por abstract.
    - tokens_min         : longitud mínima (en tokens preprocesados).
    - tokens_max         : longitud máxima (en tokens preprocesados).
    - vocabulario_total  : número de términos distintos en todo el corpus.

    Usa solo estructuras básicas (listas, diccionarios, bucles) conforme a las
    convenciones del proyecto. No hace llamadas de red ni accede a archivos.

    Complejidad: O(T), con T el total de tokens del corpus.

    Parámetros
    ----------
    articulos : list[dict]
        Lista de artículos tal como los devuelve `cargar_corpus()`.

    Devuelve
    --------
    dict con claves: total, tokens_promedio, tokens_min, tokens_max,
    vocabulario_total. Cuando la lista está vacía, todos los valores son 0.
    """
    # Importación local para evitar ciclos de importación; preprocesamiento
    # no depende de corpus, pero corpus sí puede necesitar preprocesar aquí.
    from app.nucleo.preprocesamiento import preprocesar

    total = len(articulos)
    if total == 0:
        return {
            "total": 0,
            "tokens_promedio": 0,
            "tokens_min": 0,
            "tokens_max": 0,
            "vocabulario_total": 0,
        }

    vocabulario = set()
    longitudes = []

    for articulo in articulos:
        tokens = preprocesar(articulo.get("abstract", ""))
        longitudes.append(len(tokens))
        for token in tokens:
            vocabulario.add(token)

    suma = 0
    minimo = longitudes[0]
    maximo = longitudes[0]
    for longitud in longitudes:
        suma += longitud
        if longitud < minimo:
            minimo = longitud
        if longitud > maximo:
            maximo = longitud

    return {
        "total": total,
        "tokens_promedio": round(suma / total, 2),
        "tokens_min": minimo,
        "tokens_max": maximo,
        "vocabulario_total": len(vocabulario),
    }
