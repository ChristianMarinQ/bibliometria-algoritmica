"""Servicio de subida de artículos: extraer un PDF, guardarlo en el corpus y borrarlo.

Reutiliza el extractor del corpus con heurísticas genéricas, calcula los embeddings
en el servidor (si está activo) y escribe en la carpeta de subidos.
"""

import hmac
import os
import tempfile
import threading
import time
from pathlib import Path

import pymupdf

from app import config
from app.corpus.extractor import extraer_articulo_generico
from app.nucleo import almacen_subidos
from app.nucleo.corpus import cargar_corpus, invalidar_corpus
from app.servicios import embeddings_servidor

MINIMO_PALABRAS = 30
MAXIMO_PALABRAS = 1000
PRIMER_ID_SUBIDO = 21
# PDFs extraídos que esperan confirmación (POST /articulos), por nombre de archivo.
MAXIMO_PENDIENTES = 20
VIGENCIA_PENDIENTE_S = 3600
_pendientes = {}
_lock_pendientes = threading.Lock()


class ErrorSubida(Exception):
    """Error de la subida con su código HTTP (400, 403, 404, 409, 413, 422)."""

    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo


def estado_sistema():
    """Capacidades del servidor para el frontend (GET /sistema)."""
    try:
        corpus = cargar_corpus()
    except FileNotFoundError:
        corpus = []
    return {
        "subida_habilitada": bool(config.SUBIDA_HABILITADA),
        "requiere_clave": bool(config.CLAVE_SUBIDA),
        "ia_en_servidor": bool(config.IA_EN_SERVIDOR),
        "total_articulos": len(corpus),
        "articulos_base": sum(1 for a in corpus if a["origen"] == "base"),
        "tamano_maximo_mb": config.TAMANO_MAXIMO_MB,
    }


def verificar_permiso(clave_recibida):
    """Lanza ErrorSubida 403 si la subida está deshabilitada o la clave no coincide."""
    if not config.SUBIDA_HABILITADA:
        raise ErrorSubida(403, "La subida de artículos está deshabilitada en este servidor.")
    if config.CLAVE_SUBIDA:
        # Comparación en tiempo constante para no filtrar la clave por tiempos.
        if not clave_recibida or not hmac.compare_digest(str(clave_recibida), config.CLAVE_SUBIDA):
            raise ErrorSubida(403, "Clave de subida inválida o ausente (cabecera X-Clave-Subida).")


def nombre_seguro(nombre):
    """Deja solo el nombre del archivo (sin carpetas) y limita su longitud."""
    nombre = Path((nombre or "").replace("\\", "/")).name.strip() or "articulo.pdf"
    return nombre[-150:]


def validar_pdf(nombre, contenido):
    """Valida extensión, tamaño y firma %PDF. Lanza ErrorSubida (400 o 413)."""
    if not nombre.lower().endswith(".pdf"):
        raise ErrorSubida(400, "El archivo debe tener extensión .pdf.")
    if len(contenido) > config.TAMANO_MAXIMO_MB * 1024 * 1024:
        raise ErrorSubida(413, f"El PDF supera el tamaño máximo de {config.TAMANO_MAXIMO_MB} MB.")
    if not contenido.startswith(b"%PDF"):
        raise ErrorSubida(400, "El archivo no es un PDF válido (falta la firma %PDF).")


def advertencias_de(articulo):
    """Lista en español de los campos que no se encontraron o parecen dudosos."""
    advertencias = []
    if not articulo["titulo"]:
        advertencias.append("No se encontró el título")
    if not articulo["autores"]:
        advertencias.append("No se encontraron los autores")
    if articulo["anio"] is None:
        advertencias.append("No se encontró el año")
    if not articulo["revista"]:
        advertencias.append("No se reconoció la revista")
    palabras = len(articulo["abstract"].split())
    if palabras == 0:
        advertencias.append("No se encontró el abstract")
    elif palabras < MINIMO_PALABRAS:
        advertencias.append(f"El abstract parece incompleto ({palabras} palabras)")
    elif palabras > MAXIMO_PALABRAS:
        advertencias.append(f"El abstract parece incluir texto de más ({palabras} palabras); revíselo")
    return advertencias


def guardar_pendiente(nombre, contenido):
    """Recuerda el PDF extraído para guardarlo si el usuario lo confirma."""
    with _lock_pendientes:
        ahora = time.time()
        for clave in [c for c, (_, t) in _pendientes.items() if ahora - t > VIGENCIA_PENDIENTE_S]:
            del _pendientes[clave]
        while len(_pendientes) >= MAXIMO_PENDIENTES:
            del _pendientes[next(iter(_pendientes))]
        _pendientes[nombre] = (contenido, ahora)


def tomar_pendiente(nombre):
    """Devuelve (y olvida) el PDF pendiente con ese nombre, o None."""
    with _lock_pendientes:
        dato = _pendientes.pop(nombre, None)
    return dato[0] if dato else None


def extraer_pdf(nombre, contenido):
    """Extrae los metadatos y el abstract de un PDF sin guardarlo.

    Devuelve el diccionario de POST /articulos/extraer con `advertencias`.
    Lanza ErrorSubida 400 (no es PDF, ilegible o sin texto) o 413 (muy grande).
    """
    nombre = nombre_seguro(nombre)
    validar_pdf(nombre, contenido)
    # Primero se abre desde memoria para validar que sea legible y tenga texto.
    try:
        with pymupdf.open(stream=contenido, filetype="pdf") as documento:
            con_texto = sum(1 for pagina in documento if pagina.get_text().strip())
    except Exception as error:  # noqa: BLE001 - PyMuPDF lanza varios tipos según el daño
        raise ErrorSubida(400, f"No se pudo leer el PDF: {error}")
    if con_texto == 0:
        raise ErrorSubida(400, "El PDF no tiene texto extraíble (¿es un escaneo?).")

    # El extractor trabaja con rutas: se usa un archivo temporal que se borra al terminar.
    descriptor, temporal = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(descriptor, "wb") as archivo:
            archivo.write(contenido)
        try:
            articulo = extraer_articulo_generico(Path(temporal))
        except Exception as error:  # noqa: BLE001
            raise ErrorSubida(400, f"No se pudo leer el PDF: {error}")
    finally:
        try:
            os.remove(temporal)
        except OSError:
            pass

    guardar_pendiente(nombre, contenido)
    return {
        "archivo": nombre,
        "titulo": articulo["titulo"],
        "autores": articulo["autores"],
        "anio": articulo["anio"],
        "revista": articulo["revista"],
        "abstract": articulo["abstract"],
        "palabras_abstract": len(articulo["abstract"].split()),
        "advertencias": advertencias_de(articulo),
    }


def normalizar_titulo(titulo):
    """Título en minúsculas y con espacios simples, para detectar duplicados."""
    return " ".join((titulo or "").lower().split())


def validar_datos(datos):
    """Limpia y valida lo enviado por el usuario. Lanza ErrorSubida 422. Devuelve el artículo sin id."""
    titulo = " ".join((datos.get("titulo") or "").split())
    abstract = " ".join((datos.get("abstract") or "").split())
    if not titulo:
        raise ErrorSubida(422, "El título no puede estar vacío.")
    palabras = len(abstract.split())
    if palabras < MINIMO_PALABRAS or palabras > MAXIMO_PALABRAS:
        raise ErrorSubida(422, f"El abstract debe tener entre {MINIMO_PALABRAS} y {MAXIMO_PALABRAS} "
                               f"palabras (tiene {palabras}).")
    autores = [" ".join(str(a).split()) for a in (datos.get("autores") or []) if str(a).strip()]
    return {
        "archivo": nombre_seguro(datos.get("archivo")),
        "titulo": titulo,
        "autores": autores,
        "anio": datos.get("anio"),
        "revista": " ".join((datos.get("revista") or "").split()),
        "abstract": abstract,
    }


def guardar_articulo(datos):
    """Agrega un artículo al corpus de subidos con sus embeddings (si la IA está activa).

    Devuelve el artículo completo con id, origen y `embeddings` {"word2vec": bool, "sbert": bool}.
    Lanza ErrorSubida 422 (datos inválidos) o 409 (título duplicado).
    """
    articulo = validar_datos(datos)
    clave_titulo = normalizar_titulo(articulo["titulo"])
    if any(normalizar_titulo(a["titulo"]) == clave_titulo for a in cargar_corpus()):
        raise ErrorSubida(409, "Ya existe un artículo con ese título.")

    # Los modelos pueden tardar: se calculan fuera del lock (no dependen del id).
    calculados = embeddings_servidor.calcular_embeddings(articulo["abstract"])
    pdf = tomar_pendiente(articulo["archivo"])

    with almacen_subidos.LOCK:
        corpus = cargar_corpus()
        if any(normalizar_titulo(a["titulo"]) == clave_titulo for a in corpus):
            raise ErrorSubida(409, "Ya existe un artículo con ese título.")
        id_nuevo = max([PRIMER_ID_SUBIDO - 1] + [a["id"] for a in corpus]) + 1
        articulo = dict({"id": id_nuevo}, **articulo)

        subidos = almacen_subidos.leer_articulos()
        subidos.append(articulo)
        embeddings = almacen_subidos.leer_embeddings()
        clave_id = str(id_nuevo)
        if calculados["word2vec"]:
            w2v = calculados["word2vec"]
            seccion = embeddings.setdefault("word2vec", {"modelo": w2v["modelo"], "dimensiones": w2v["dimensiones"],
                                                         "vectores": {}, "cobertura": {}})
            seccion["vectores"][clave_id] = w2v["vector"]
            seccion.setdefault("cobertura", {})[clave_id] = w2v["cobertura"]
        if calculados["sbert"]:
            sbert = calculados["sbert"]
            seccion = embeddings.setdefault("sbert", {"modelo": sbert["modelo"], "dimensiones": sbert["dimensiones"],
                                                      "vectores": {}})
            seccion["vectores"][clave_id] = sbert["vector"]
        if pdf is not None:
            almacen_subidos.escribir_atomico(almacen_subidos.ruta_pdf(id_nuevo), pdf)
        almacen_subidos.guardar(subidos, embeddings)
        invalidar_corpus()

    respuesta = dict(articulo, origen="subido", palabras_abstract=len(articulo["abstract"].split()))
    respuesta["embeddings"] = {"word2vec": calculados["word2vec"] is not None,
                               "sbert": calculados["sbert"] is not None}
    if calculados["avisos"]:
        respuesta["avisos"] = calculados["avisos"]
    return respuesta


def borrar_articulo(id_articulo):
    """Elimina un artículo subido, sus vectores y su PDF. Lanza ErrorSubida 404 o 403 (artículo base)."""
    with almacen_subidos.LOCK:
        articulo = next((a for a in cargar_corpus() if a["id"] == id_articulo), None)
        if articulo is None:
            raise ErrorSubida(404, f"No existe el artículo con id {id_articulo}")
        if articulo["origen"] != "subido":
            raise ErrorSubida(403, "Los artículos base del corpus no se pueden borrar.")
        subidos = [a for a in almacen_subidos.leer_articulos() if a["id"] != id_articulo]
        embeddings = almacen_subidos.leer_embeddings()
        for seccion in embeddings.values():
            seccion.get("vectores", {}).pop(str(id_articulo), None)
            seccion.get("cobertura", {}).pop(str(id_articulo), None)
        almacen_subidos.guardar(subidos, embeddings)
        ruta = almacen_subidos.ruta_pdf(id_articulo)
        if ruta.exists():
            ruta.unlink()
        invalidar_corpus()
