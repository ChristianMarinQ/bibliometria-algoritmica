"""Utilidades para medir tiempos de ejecución de los algoritmos."""

import time


def medir(funcion, *args, repeticiones=1, **kwargs):
    """Ejecuta la función y devuelve (resultado, tiempo_promedio_ms).

    Se usa time.perf_counter por ser el reloj de mayor resolución disponible.
    """
    resultado = None
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        resultado = funcion(*args, **kwargs)
    fin = time.perf_counter()
    return resultado, (fin - inicio) * 1000 / repeticiones
