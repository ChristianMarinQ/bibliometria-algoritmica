"""Servicio del Req. 2: arma la matriz de distancias del corpus y ejecuta
los tres métodos de clustering jerárquico con sus tiempos y métricas.
"""

import json

from app import config
from app.algoritmos.clustering.jerarquico import METODOS, agrupar, construir_arbol
from app.algoritmos.clustering.metricas import correlacion_cofenetica, cortar_arbol, silhouette
from app.algoritmos.similitud.embeddings import coseno
from app.nucleo.corpus import cargar_corpus
from app.nucleo.medicion import medir
from app.nucleo.preprocesamiento import preprocesar
from app.nucleo.vectorizacion import coseno_dispersos, tfidf

REPRESENTACIONES = ("tfidf", "sbert")
CRITERIO = "Mayor coeficiente de correlación cofenética; Silhouette como desempate"
TOLERANCIA_EMPATE = 1e-9


class DatosNoDisponibles(Exception):
    """Falta un archivo de datos generado (corpus o embeddings)."""


def matriz_desde_similitud(n, similitud):
    """Construye la matriz de distancias d = 1 − sim (simétrica, diagonal 0).

    `similitud(i, j)` devuelve la similitud del coseno entre los elementos i y j.
    Complejidad: O(n²) llamadas a `similitud`.
    """
    distancias = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            # Se recorta a 0 por errores de redondeo cuando sim ≈ 1.
            valor = max(0.0, 1.0 - similitud(i, j))
            distancias[i][j] = valor
            distancias[j][i] = valor
    return distancias


def distancias_tfidf(articulos):
    """Preprocesa los abstracts, vectoriza con TF-IDF y devuelve 1 − coseno."""
    documentos = [preprocesar(articulo["abstract"]) for articulo in articulos]
    vectores, _ = tfidf(documentos)
    return matriz_desde_similitud(len(vectores),
                                  lambda i, j: coseno_dispersos(vectores[i], vectores[j]))


def distancias_sbert(articulos):
    """Lee los embeddings SBERT precalculados y devuelve 1 − coseno."""
    if not config.RUTA_EMBEDDINGS.exists():
        raise DatosNoDisponibles(
            "No existe data/embeddings.json; ejecute el script de generación de embeddings.")
    with open(config.RUTA_EMBEDDINGS, encoding="utf-8") as archivo:
        datos = json.load(archivo)
    vectores_por_id = datos.get("sbert", {}).get("vectores", {})
    vectores = []
    for articulo in articulos:
        vector = vectores_por_id.get(str(articulo["id"]))
        if vector is None:
            raise DatosNoDisponibles(
                f"embeddings.json no tiene vector SBERT para el artículo {articulo['id']}.")
        vectores.append(vector)
    return matriz_desde_similitud(len(vectores),
                                  lambda i, j: coseno(vectores[i], vectores[j]))


def cargar_articulos():
    """Devuelve el corpus o lanza DatosNoDisponibles si aún no se ha generado."""
    if not config.RUTA_CORPUS.exists():
        raise DatosNoDisponibles(
            "No existe data/corpus.json; ejecute primero la extracción del corpus.")
    return cargar_corpus()


def elegir_mejor(metodos):
    """Elige la clave del mejor método: mayor cofenética y, si empatan, mayor Silhouette."""
    mejor = None
    for metodo in metodos:
        if mejor is None:
            mejor = metodo
            continue
        diferencia = metodo["correlacion_cofenetica"] - mejor["correlacion_cofenetica"]
        if diferencia > TOLERANCIA_EMPATE:
            mejor = metodo
        elif abs(diferencia) <= TOLERANCIA_EMPATE and metodo["silhouette"] > mejor["silhouette"]:
            mejor = metodo
    return mejor["clave"] if mejor else None


def ejecutar_metodos(distancias, hojas, k):
    """Ejecuta single, complete y average sobre la matriz y calcula sus métricas.

    Devuelve la lista de resultados con la forma de `metodos` del contrato.
    """
    n = len(distancias)
    resultados = []
    for clave in METODOS:
        fusiones, tiempo = medir(agrupar, distancias, clave)
        etiquetas = cortar_arbol(fusiones, n, k)
        fusiones_redondeadas = []
        for fusion in fusiones:
            copia = dict(fusion)
            copia["distancia"] = round(fusion["distancia"], 6)
            fusiones_redondeadas.append(copia)
        resultados.append({
            "clave": clave,
            "nombre": METODOS[clave],
            "arbol": construir_arbol(fusiones_redondeadas, hojas),
            "fusiones": fusiones_redondeadas,
            "silhouette": round(silhouette(distancias, etiquetas), 4),
            "correlacion_cofenetica": round(correlacion_cofenetica(distancias, fusiones), 4),
            "tiempo_ms": round(tiempo, 4),
        })
    return resultados


def ejecutar_clustering(representacion="tfidf", k=4):
    """Pipeline completo del Req. 2 sobre el corpus: distancias -> clustering -> métricas.

    Devuelve el diccionario de respuesta de GET /clustering.
    """
    if representacion not in REPRESENTACIONES:
        raise ValueError(f"Representación no soportada: {representacion}")
    articulos = cargar_articulos()
    n = len(articulos)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 artículos para agrupar.")
    if k < 2 or k > n:
        raise ValueError(f"k debe estar entre 2 y {n}.")

    if representacion == "tfidf":
        distancias = distancias_tfidf(articulos)
    else:
        distancias = distancias_sbert(articulos)

    hojas = [{"articulo_id": a["id"], "titulo": a["titulo"]} for a in articulos]
    metodos = ejecutar_metodos(distancias, hojas, k)
    return {
        "representacion": representacion,
        "articulos": [{"id": a["id"], "titulo": a["titulo"]} for a in articulos],
        "metodos": metodos,
        "mejor_metodo": elegir_mejor(metodos),
        "criterio": CRITERIO,
    }
