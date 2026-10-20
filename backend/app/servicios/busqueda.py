"""Servicio del Req. 3: búsqueda de patrones en los abstracts con KMP, Boyer-Moore y Rabin-Karp.

Mide por separado el tiempo de preprocesamiento y el de búsqueda, y arma
fragmentos con contexto alrededor de cada coincidencia.
"""

from app.algoritmos.busqueda import boyer_moore, kmp, rabin_karp
from app.nucleo.corpus import cargar_corpus, obtener_articulo, obtener_articulos
from app.nucleo.medicion import medir

# Orden fijo de los algoritmos en las respuestas
ALGORITMOS = {
    kmp.CLAVE: kmp,
    boyer_moore.CLAVE: boyer_moore,
    rabin_karp.CLAVE: rabin_karp,
}

LONGITUD_MAXIMA_PATRON = 100
CONTEXTO = 40
# Repeticiones para que los tiempos tan pequeños no salgan en 0
REPETICIONES_PREPROCESAMIENTO = 200
REPETICIONES_BUSQUEDA = 5


def a_minusculas(texto):
    """Convierte a minúsculas carácter a carácter conservando la longitud del texto.

    Si un carácter se expande al pasar a minúscula (p. ej. 'İ'), se deja igual
    para que las posiciones coincidan con el texto original.
    Complejidad: O(n)
    """
    caracteres = []
    for c in texto:
        minuscula = c.lower()
        caracteres.append(minuscula if len(minuscula) == 1 else c)
    return "".join(caracteres)


def _preparar(texto, distinguir_mayusculas):
    """Normaliza el texto según la opción de mayúsculas."""
    return texto if distinguir_mayusculas else a_minusculas(texto)


def _buscar_en_textos(modulo, textos, patron, preproceso):
    """Ejecuta la búsqueda de un algoritmo en todos los textos. Devuelve (lista de posiciones, comparaciones)."""
    todas = []
    comparaciones = 0
    for texto in textos:
        posiciones, comps = modulo.buscar_preprocesado(texto, patron, preproceso)
        todas.append(posiciones)
        comparaciones += comps
    return todas, comparaciones


def _fragmento(texto, posicion, m):
    """Arma el fragmento {posicion, antes, coincidencia, despues} con ~40 caracteres de contexto."""
    inicio = posicion - CONTEXTO if posicion - CONTEXTO > 0 else 0
    fin = posicion + m + CONTEXTO
    if fin > len(texto):
        fin = len(texto)
    antes = texto[inicio:posicion]
    despues = texto[posicion + m:fin]
    if inicio > 0:
        antes = "…" + antes
    if fin < len(texto):
        despues = despues + "…"
    return {
        "posicion": posicion,
        "antes": antes,
        "coincidencia": texto[posicion:posicion + m],
        "despues": despues,
    }


def buscar_patron(patron, ids=None, distinguir_mayusculas=False):
    """Busca el patrón con los tres algoritmos en los abstracts (todos o los ids dados).

    Devuelve el diccionario del contrato: patron, algoritmos (tiempos y comparaciones),
    coinciden y resultados por artículo. Lanza KeyError si un id no existe.
    """
    articulos = cargar_corpus() if ids is None else obtener_articulos(ids)
    patron_buscado = _preparar(patron, distinguir_mayusculas)
    textos = [_preparar(articulo["abstract"], distinguir_mayusculas) for articulo in articulos]
    m = len(patron_buscado)

    resumen = []
    posiciones_por_algoritmo = []
    for clave, modulo in ALGORITMOS.items():
        preproceso, tiempo_pre = medir(
            modulo.preprocesar, patron_buscado, repeticiones=REPETICIONES_PREPROCESAMIENTO
        )
        (posiciones, comparaciones), tiempo_busqueda = medir(
            _buscar_en_textos, modulo, textos, patron_buscado, preproceso,
            repeticiones=REPETICIONES_BUSQUEDA,
        )
        posiciones_por_algoritmo.append(posiciones)
        total = 0
        for lista in posiciones:
            total += len(lista)
        resumen.append({
            "clave": clave,
            "nombre": modulo.NOMBRE,
            "tiempo_preprocesamiento_ms": tiempo_pre,
            "tiempo_busqueda_ms": tiempo_busqueda,
            "comparaciones": comparaciones,
            "total_coincidencias": total,
        })

    # Los tres algoritmos deben encontrar exactamente las mismas posiciones
    coinciden = True
    for otras in posiciones_por_algoritmo[1:]:
        if otras != posiciones_por_algoritmo[0]:
            coinciden = False

    resultados = []
    referencia = posiciones_por_algoritmo[0]
    for indice, articulo in enumerate(articulos):
        posiciones = referencia[indice]
        if len(posiciones) == 0:
            continue
        resultados.append({
            "articulo_id": articulo["id"],
            "titulo": articulo["titulo"],
            "posiciones": posiciones,
            "fragmentos": [_fragmento(articulo["abstract"], p, m) for p in posiciones],
        })

    return {
        "patron": patron,
        "algoritmos": resumen,
        "coinciden": coinciden,
        "resultados": resultados,
    }


def _recortar_texto(texto, patron, max_caracteres):
    """Recorta el texto a max_caracteres procurando incluir la primera ocurrencia. Devuelve (recorte, inicio)."""
    n = len(texto)
    m = len(patron)
    if max_caracteres < m:
        max_caracteres = m
    if n <= max_caracteres:
        return texto, 0
    posiciones, _ = kmp.buscar(texto, patron)
    inicio = 0
    if len(posiciones) > 0 and posiciones[0] + m > max_caracteres:
        # Se centra la ventana en la primera ocurrencia
        inicio = posiciones[0] - (max_caracteres - m) // 2
        if inicio + max_caracteres > n:
            inicio = n - max_caracteres
        # Se retrocede hasta el inicio de una palabra (sin perder la ocurrencia)
        while inicio > 0 and texto[inicio - 1] != " " and posiciones[0] + m - (inicio - 1) <= max_caracteres:
            inicio -= 1
    return texto[inicio:inicio + max_caracteres], inicio


def traza_busqueda(patron, algoritmo, articulo_id, max_caracteres=300, distinguir_mayusculas=False):
    """Ejecuta la versión con traza de un algoritmo sobre un fragmento del abstract.

    Lanza KeyError si el artículo no existe y ValueError si el algoritmo no existe.
    """
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"Algoritmo desconocido: {algoritmo}")
    articulo = obtener_articulo(articulo_id)
    if articulo is None:
        raise KeyError(f"No existe el artículo con id {articulo_id}")
    patron_buscado = _preparar(patron, distinguir_mayusculas)
    texto = _preparar(articulo["abstract"], distinguir_mayusculas)
    recorte, inicio = _recortar_texto(texto, patron_buscado, max_caracteres)
    traza = ALGORITMOS[algoritmo].buscar_con_traza(recorte, patron_buscado)
    traza["articulo_id"] = articulo_id
    traza["inicio_texto"] = inicio
    return traza
