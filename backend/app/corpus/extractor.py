"""Extracción de título, autores, año, revista y abstract desde los PDFs del corpus.

Usa PyMuPDF: el texto plano para el abstract y las líneas con tamaño de fuente
para el título y los autores (que suelen ser el texto más grande de la página 1).
"""

import re
import unicodedata

import pymupdf

from app.corpus.marcadores import CORRECCIONES, MARCADORES_ARTICULO, REVISTAS

# Ligaduras y caracteres especiales frecuentes en los PDFs de las editoriales.
REEMPLAZOS = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    "​": "",
    "﻿": "",
    "‑": "-",
    "‐": "-",
}

# Caracteres que algunos PDFs usan como guion de corte de línea (guion suave).
GUIONES_SUAVES = "­�"

# Marcadores generales de inicio y fin del abstract.
PATRON_INICIO = re.compile(r"A B S T R A C T|\bAbstract\b:?")
PATRON_FIN = re.compile(r"Keywords|K E Y W O R D S|\n\s*1\.\s*Introduction|\n\s*Introduction\s*\n")


def normalizar_caracteres(texto):
    """Reemplaza ligaduras, espacios especiales y guiones raros. Devuelve el texto."""
    for original, nuevo in REEMPLAZOS.items():
        texto = texto.replace(original, nuevo)
    return texto


def reparar_diacriticos(texto):
    """Une acentos sueltos con su letra ("Gaševi´c" -> "Gašević")."""
    combinantes = {"´": "́", "ˇ": "̌", "¨": "̈", "`": "̀"}
    for suelto, combinante in combinantes.items():
        texto = re.sub(re.escape(suelto) + r"([A-Za-z])", lambda m: m.group(1) + combinante, texto)
    return unicodedata.normalize("NFC", texto)


def reparar_guiones(texto, texto_documento):
    """Une palabras cortadas al final de línea. Devuelve el texto reparado.

    Un guion suave siempre se elimina. Un guion normal se conserva si la palabra
    con guion aparece en otra parte del documento (p. ej. "self-regulated"), si
    lo precede una mayúscula (siglas como "AI-driven") o si sigue una mayúscula.
    """
    def unir(coincidencia):
        izquierda, guion, derecha = coincidencia.group(1), coincidencia.group(2), coincidencia.group(3)
        if guion in GUIONES_SUAVES:
            return izquierda + derecha
        compuesta = izquierda + "-" + derecha
        if (izquierda[-1].isupper() or not derecha[0].islower()
                or compuesta.lower() in texto_documento.lower()):
            return compuesta
        return izquierda + derecha

    patron = re.compile(r"(\w+)([-" + GUIONES_SUAVES + r"])[ \t]*\n\s*(\w+)")
    texto = patron.sub(unir, texto)
    # Guiones suaves que quedaron dentro de una línea ("well-­defined").
    for guion in GUIONES_SUAVES:
        texto = texto.replace(guion, "")
    return texto


def limpiar_abstract(crudo, texto_documento):
    """Une líneas, repara cortes y normaliza espacios. Devuelve el abstract limpio."""
    texto = reparar_guiones(normalizar_caracteres(crudo), texto_documento)
    # Tras "/" o una raya al final de línea no va espacio ("countries/regions").
    texto = re.sub(r"([/\u2014])[ \t]*\n\s*", r"\1", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    # Quita restos de rótulo o puntuación inicial (":" de "Abstract:").
    return texto.lstrip(":").strip()


def leer_lineas(pagina):
    """Devuelve las líneas de una página con texto, tamaño de fuente, caja y spans."""
    lineas = []
    for bloque in pagina.get_text("dict")["blocks"]:
        for linea in bloque.get("lines", []):
            spans = [s for s in linea["spans"] if s["text"].strip()]
            if not spans:
                continue
            texto = normalizar_caracteres("".join(s["text"] for s in linea["spans"])).strip()
            lineas.append({
                "texto": texto,
                "tam": round(max(s["size"] for s in spans), 1),
                "x0": linea["bbox"][0], "y0": linea["bbox"][1],
                "x1": linea["bbox"][2], "y1": linea["bbox"][3],
                "spans": linea["spans"],
            })
    # Orden de lectura aproximado: de arriba hacia abajo y de izquierda a derecha.
    lineas.sort(key=lambda l: (round(l["y0"]), l["x0"]))
    return lineas


def es_cabecera_revista(texto):
    """Indica si un texto corresponde al nombre de una revista conocida."""
    for revista in REVISTAS:
        if re.search(revista["patron"], texto):
            return True
    return False


def extraer_titulo(lineas):
    """Busca el título como el grupo de líneas contiguas de mayor fuente.

    Descarta grupos cortos (logos, "1 3") o que son el nombre de la revista.
    Devuelve (titulo, lineas_del_titulo) o ("", []) si no lo encuentra.
    """
    tamanos = sorted({l["tam"] for l in lineas}, reverse=True)
    for tam in tamanos:
        grupo = [l for l in lineas if abs(l["tam"] - tam) < 0.2]
        # Solo el primer bloque contiguo de ese tamaño.
        contiguas = [grupo[0]]
        for linea in grupo[1:]:
            if linea["y0"] - contiguas[-1]["y1"] > tam * 1.5:
                break
            contiguas.append(linea)
        texto = " ".join(l["texto"] for l in contiguas)
        texto = re.sub(r"\s+", " ", texto).strip()
        if len(texto.split()) < 4 or es_cabecera_revista(texto):
            continue
        return texto, contiguas
    return "", []


def extraer_autores(lineas, lineas_titulo):
    """Toma las líneas que siguen al título con la fuente de los autores.

    Ignora los superíndices (spans de fuente menor) y separa por comas, "and",
    "|" y "·". Devuelve la lista de nombres.
    """
    ultima = lineas_titulo[-1]
    # Solo líneas bajo el título y dentro de su franja horizontal (evita cabeceras laterales).
    x_minimo = min(l["x0"] for l in lineas_titulo) - 10
    x_maximo = max(l["x1"] for l in lineas_titulo)
    siguientes = [l for l in lineas
                  if l["y0"] > ultima["y1"] - 1 and x_minimo <= l["x0"] < x_maximo
                  and l not in lineas_titulo]
    if not siguientes:
        return []
    tam = siguientes[0]["tam"]
    seleccion = [siguientes[0]]
    for linea in siguientes[1:]:
        if abs(linea["tam"] - tam) > 0.3 or linea["y0"] - seleccion[-1]["y1"] > tam * 1.2:
            break
        seleccion.append(linea)

    # Se descartan los spans pequeños: afiliaciones (a, b, 1,2) y marcas "*".
    texto = ""
    for linea in seleccion:
        for span in linea["spans"]:
            if span["size"] >= tam * 0.85:
                texto += span["text"]
        texto += " "
    texto = reparar_diacriticos(normalizar_caracteres(texto))
    texto = re.sub(r"\band\b", ",", texto)

    autores = []
    for parte in re.split(r"[,|·&]", texto):
        nombre = re.sub(r"[*∗†‡\d]", "", parte)
        nombre = re.sub(r"\s+", " ", nombre).strip()
        # Fragmentos de una sola letra son superíndices que se colaron.
        if len(nombre) > 1:
            autores.append(nombre)
    return autores


def detectar_revista(texto, metadatos):
    """Identifica la revista y el año a partir del texto de la página 1.

    Devuelve (revista, anio). Si no hay año en el texto, usa la fecha de creación.
    """
    plano = re.sub(r"\s+", " ", normalizar_caracteres(texto))
    for revista in REVISTAS:
        if re.search(revista["patron"], plano):
            anio = re.search(revista["patron_anio"], plano)
            if anio:
                return revista["nombre"], int(anio.group(1))
            return revista["nombre"], anio_de_metadatos(metadatos)
    return "", anio_de_metadatos(metadatos)


def anio_de_metadatos(metadatos):
    """Extrae el año de la fecha de creación del PDF ("D:2022...") o None."""
    fecha = (metadatos or {}).get("creationDate") or ""
    coincidencia = re.search(r"(\d{4})", fecha)
    return int(coincidencia.group(1)) if coincidencia else None


def extraer_abstract(texto, id_articulo, usar_marcadores=True):
    """Recorta el abstract entre los marcadores generales o los del artículo.

    Devuelve el texto crudo (sin limpiar) o "" si no encuentra el inicio.
    """
    marcadores = MARCADORES_ARTICULO.get(id_articulo, {}) if usar_marcadores else {}
    inicio = PATRON_INICIO.search(texto)
    if not inicio:
        return ""
    posicion = inicio.end()
    if "inicio" in marcadores:
        posicion = texto.index(marcadores["inicio"], posicion) + len(marcadores["inicio"])
    if "fin" in marcadores:
        fin = texto.index(marcadores["fin"], posicion)
    else:
        coincidencia = PATRON_FIN.search(texto, posicion)
        fin = coincidencia.start() if coincidencia else len(texto)
    return texto[posicion:fin]


def extraer_articulo(ruta_pdf, id_articulo, usar_marcadores=True):
    """Procesa un PDF y devuelve el diccionario del artículo según el esquema del corpus.

    `usar_marcadores=False` ignora los ajustes por id de marcadores.py (PDFs subidos).
    """
    documento = pymupdf.open(ruta_pdf)
    try:
        pagina = documento[0]
        texto_pag1 = pagina.get_text()
        # Las dos primeras páginas bastan para el abstract y para validar guiones.
        texto = texto_pag1 + "\n" + (documento[1].get_text() if len(documento) > 1 else "")
        texto_documento = normalizar_caracteres("".join(p.get_text() for p in documento))

        lineas = leer_lineas(pagina)
        titulo, lineas_titulo = extraer_titulo(lineas)
        autores = extraer_autores(lineas, lineas_titulo) if lineas_titulo else []
        revista, anio = detectar_revista(texto_pag1, documento.metadata)
        crudo = extraer_abstract(texto, id_articulo, usar_marcadores)
    finally:
        documento.close()

    articulo = {
        "id": id_articulo,
        "archivo": ruta_pdf.name,
        "titulo": titulo,
        "autores": autores,
        "anio": anio,
        "revista": revista,
        "abstract": limpiar_abstract(crudo, texto_documento),
    }
    # Correcciones manuales documentadas en marcadores.py (si las hubiera).
    if usar_marcadores:
        articulo.update(CORRECCIONES.get(id_articulo, {}))
    return articulo


# ---------- Heurísticas genéricas para PDFs de revistas desconocidas ----------

PATRON_ANIO = re.compile(r"(19[5-9]\d|20\d\d)")
MINIMO_PALABRAS_BLOQUE = 60


def abstract_por_bloques(ruta_pdf):
    """Primer bloque de texto largo de las dos primeras páginas (sin rótulo "Abstract").

    Devuelve el texto crudo o "" si ningún bloque tiene suficientes palabras.
    """
    documento = pymupdf.open(ruta_pdf)
    try:
        for numero in range(min(2, len(documento))):
            for bloque in documento[numero].get_text("blocks"):
                texto = bloque[4]
                if len(texto.split()) >= MINIMO_PALABRAS_BLOQUE:
                    return texto
    finally:
        documento.close()
    return ""


def metadatos_pdf(ruta_pdf):
    """Metadatos del PDF (title, author, creationDate...) como diccionario."""
    documento = pymupdf.open(ruta_pdf)
    try:
        return dict(documento.metadata or {})
    finally:
        documento.close()


def texto_primera_pagina(ruta_pdf):
    """Texto plano normalizado de la primera página."""
    documento = pymupdf.open(ruta_pdf)
    try:
        return normalizar_caracteres(documento[0].get_text()) if len(documento) else ""
    finally:
        documento.close()


def extraer_articulo_generico(ruta_pdf):
    """Extrae un PDF cualquiera (sin marcadores por id) completando lo que falte con heurísticas.

    Si no hay rótulo "Abstract" usa el primer bloque largo; si falta el título o los
    autores usa los metadatos del PDF; si falta el año busca uno en la página 1.
    Devuelve el diccionario del artículo (sin id).
    """
    articulo = extraer_articulo(ruta_pdf, 0, usar_marcadores=False)
    articulo.pop("id")
    metadatos = metadatos_pdf(ruta_pdf)
    if not articulo["abstract"]:
        crudo = abstract_por_bloques(ruta_pdf)
        if crudo:
            articulo["abstract"] = limpiar_abstract(crudo, crudo)
    if not articulo["titulo"] and (metadatos.get("title") or "").strip():
        articulo["titulo"] = re.sub(r"\s+", " ", metadatos["title"]).strip()
    if not articulo["autores"] and (metadatos.get("author") or "").strip():
        partes = re.split(r"[,;]| and ", metadatos["author"])
        articulo["autores"] = [p.strip() for p in partes if len(p.strip()) > 1]
    if articulo["anio"] is None:
        coincidencia = PATRON_ANIO.search(texto_primera_pagina(ruta_pdf))
        if coincidencia:
            articulo["anio"] = int(coincidencia.group(1))
    return articulo
