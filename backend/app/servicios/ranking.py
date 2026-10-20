"""Servicio del seguimiento: ranking de términos más frecuentes del corpus.

Calcula las frecuencias de los abstracts del corpus, las ordena con Counting, Radix y
Bucket Sort, mide tiempos y arma el benchmark de escalamiento.
"""

from app.algoritmos.ordenamiento.bucket_sort import bucket_sort
from app.algoritmos.ordenamiento.counting_sort import counting_sort
from app.algoritmos.ordenamiento.radix_sort import radix_sort
from app.nucleo.corpus import cargar_corpus
from app.nucleo.medicion import medir
from app.nucleo.preprocesamiento import frecuencias, preprocesar

# Catálogo de algoritmos: (clave, nombre, complejidad, función).
ALGORITMOS = [
    ("counting_sort", "Counting Sort", "O(n + k)", counting_sort),
    ("radix_sort", "Radix Sort", "O(d·(n + b))", radix_sort),
    ("bucket_sort", "Bucket Sort", "O(n) promedio", bucket_sort),
]

REPETICIONES_RANKING = 20
FACTORES_ESCALAMIENTO = [1, 2, 4, 8]
# Tope de repeticiones del escalamiento: la lista ×8 es 8 veces más costosa y
# sin tope la petición superaría varios segundos con repeticiones=50.
MAXIMO_REPETICIONES_ESCALAMIENTO = 10


def calcular_tokens(corpus):
    """Preprocesa todos los abstracts y devuelve la lista total de tokens."""
    tokens = []
    for articulo in corpus:
        tokens.extend(preprocesar(articulo.get("abstract", "")))
    return tokens


def construir_pares(conteo):
    """Convierte el diccionario de frecuencias en pares (termino, frecuencia).

    Preparación de datos, no es el algoritmo evaluado: se ordena una sola vez
    alfabéticamente con sorted() para que, al ser estables los tres algoritmos,
    los empates de frecuencia queden en orden alfabético y todos den el mismo top.
    """
    return sorted(conteo.items(), key=lambda par: par[0])


def datos_corpus():
    """Devuelve (tokens, pares) del corpus completo."""
    tokens = calcular_tokens(cargar_corpus())
    return tokens, construir_pares(frecuencias(tokens))


def a_top(ordenados, top):
    """Toma los primeros `top` pares y los convierte al formato del contrato."""
    resultado = []
    for termino, frecuencia in ordenados[:top]:
        resultado.append({"termino": termino, "frecuencia": frecuencia})
    return resultado


def ranking_desde_pares(pares, total_tokens, top=15, repeticiones=REPETICIONES_RANKING):
    """Ejecuta los tres algoritmos sobre los pares y arma la respuesta de /ranking."""
    frecuencia_maxima = 0
    for _, frecuencia in pares:
        if frecuencia > frecuencia_maxima:
            frecuencia_maxima = frecuencia

    algoritmos = []
    for clave, nombre, complejidad, funcion in ALGORITMOS:
        ordenados, tiempo_ms = medir(funcion, pares, repeticiones=repeticiones)
        algoritmos.append({
            "clave": clave,
            "nombre": nombre,
            "tiempo_ms": tiempo_ms,
            "complejidad": complejidad,
            "top": a_top(ordenados, top),
        })

    # Los tres deben coincidir término a término en el top solicitado.
    coinciden = True
    for algoritmo in algoritmos[1:]:
        if algoritmo["top"] != algoritmos[0]["top"]:
            coinciden = False

    return {
        "total_tokens": total_tokens,
        "terminos_distintos": len(pares),
        "frecuencia_maxima": frecuencia_maxima,
        "algoritmos": algoritmos,
        "coinciden": coinciden,
    }


def generar_ranking(top=15):
    """Ranking de los `top` términos más frecuentes del corpus completo."""
    tokens, pares = datos_corpus()
    return ranking_desde_pares(pares, len(tokens), top)


def benchmark_desde_pares(pares, repeticiones=50):
    """Mide promedio, mínimo y máximo de cada algoritmo y el escalamiento ×1, ×2, ×4, ×8.

    El escalamiento promedia min(repeticiones, MAXIMO_REPETICIONES_ESCALAMIENTO) ejecuciones.
    """
    algoritmos = []
    for clave, _, _, funcion in ALGORITMOS:
        tiempos = []
        for _ in range(repeticiones):
            _, tiempo_ms = medir(funcion, pares)
            tiempos.append(tiempo_ms)
        algoritmos.append({
            "clave": clave,
            "promedio_ms": sum(tiempos) / len(tiempos),
            "minimo_ms": min(tiempos),
            "maximo_ms": max(tiempos),
        })

    # Escalamiento: se duplica la lista de pares; el rango de frecuencias no cambia,
    # así que un crecimiento lineal del tiempo evidencia el término O(n).
    repeticiones_escalamiento = min(repeticiones, MAXIMO_REPETICIONES_ESCALAMIENTO)
    escalamiento = []
    for factor in FACTORES_ESCALAMIENTO:
        lista = pares * factor
        fila = {"n": len(lista)}
        for clave, _, _, funcion in ALGORITMOS:
            _, tiempo_ms = medir(funcion, lista, repeticiones=repeticiones_escalamiento)
            fila[clave] = tiempo_ms
        escalamiento.append(fila)

    return {
        "n": len(pares),
        "repeticiones": repeticiones,
        "algoritmos": algoritmos,
        "escalamiento": escalamiento,
    }


def generar_benchmark(repeticiones=50):
    """Benchmark de los tres algoritmos sobre la lista de frecuencias del corpus."""
    _, pares = datos_corpus()
    return benchmark_desde_pares(pares, repeticiones)
