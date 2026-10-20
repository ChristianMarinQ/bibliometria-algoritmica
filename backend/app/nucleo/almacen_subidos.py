"""Almacenamiento en disco de los artículos subidos por el usuario.

Guarda en config.CARPETA_SUBIDOS: articulos.json, embeddings.json y pdfs/<id>.pdf,
con escrituras atómicas, un lock para concurrencia y un contador de versión.
"""

import json
import os
import tempfile
import threading

from app import config

# Un solo lock para todas las escrituras de la carpeta de subidos.
LOCK = threading.Lock()

# Se incrementa en cada escritura; los cachés derivados del corpus lo usan en su clave.
_estado = {"version": 0}


def version():
    """Número de versión de los datos subidos (cambia en cada escritura)."""
    return _estado["version"]


def incrementar_version():
    """Marca que los datos subidos cambiaron para invalidar los cachés."""
    _estado["version"] += 1


def ruta_articulos():
    """Ruta de articulos.json dentro de la carpeta de subidos."""
    return config.CARPETA_SUBIDOS / "articulos.json"


def ruta_embeddings():
    """Ruta de embeddings.json dentro de la carpeta de subidos."""
    return config.CARPETA_SUBIDOS / "embeddings.json"


def ruta_pdf(id_articulo):
    """Ruta del PDF guardado de un artículo subido."""
    return config.CARPETA_SUBIDOS / "pdfs" / f"{id_articulo}.pdf"


def marca_archivo(ruta):
    """Fecha de modificación de un archivo o None si no existe (para claves de caché)."""
    try:
        return os.path.getmtime(ruta)
    except OSError:
        return None


def leer_json(ruta, por_defecto):
    """Lee un JSON; si el archivo no existe devuelve el valor por defecto."""
    try:
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return por_defecto


def escribir_atomico(ruta, contenido):
    """Escribe bytes en un archivo temporal de la misma carpeta y lo reemplaza con os.replace."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(dir=ruta.parent, prefix=".tmp_", suffix=ruta.suffix)
    try:
        with os.fdopen(descriptor, "wb") as archivo:
            archivo.write(contenido)
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise


def escribir_json(ruta, datos):
    """Serializa los datos a JSON (UTF-8) y los escribe de forma atómica."""
    escribir_atomico(ruta, json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8"))


def leer_articulos():
    """Lista de artículos subidos (vacía si aún no hay ninguno)."""
    return leer_json(ruta_articulos(), [])


def leer_embeddings():
    """Embeddings de los artículos subidos con el formato de data/embeddings.json ({} si no hay)."""
    return leer_json(ruta_embeddings(), {})


def combinar_embeddings(base, subidos):
    """Une los embeddings base con los subidos sin modificar los originales.

    Devuelve un diccionario con el mismo formato de data/embeddings.json.
    """
    resultado = {}
    for clave, modelo in base.items():
        copia = dict(modelo)
        copia["vectores"] = dict(modelo.get("vectores", {}))
        if "cobertura" in modelo:
            copia["cobertura"] = dict(modelo["cobertura"])
        extra = subidos.get(clave, {})
        copia["vectores"].update(extra.get("vectores", {}))
        if "cobertura" in extra:
            copia.setdefault("cobertura", {}).update(extra["cobertura"])
        resultado[clave] = copia
    return resultado


def guardar(articulos, embeddings):
    """Escribe articulos.json y embeddings.json de subidos e invalida los cachés.

    Debe llamarse con LOCK tomado.
    """
    escribir_json(ruta_embeddings(), embeddings)
    escribir_json(ruta_articulos(), articulos)
    incrementar_version()
