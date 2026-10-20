"""Imprime el top 15 de términos con cada algoritmo y sus tiempos, y guarda los JSON.

Ejecutar desde la carpeta backend:
    python scripts/benchmark_ranking.py
"""

import json
import sys
from pathlib import Path

# Permite importar el paquete app al ejecutar el script directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import RAIZ_PROYECTO  # noqa: E402
from app.servicios.ranking import generar_benchmark, generar_ranking  # noqa: E402

CARPETA_RESULTADOS = RAIZ_PROYECTO / "docs" / "resultados"
TOP = 15
REPETICIONES = 50


def imprimir_ranking(datos):
    """Imprime una tabla con el top de cada algoritmo lado a lado."""
    print(f"Tokens totales: {datos['total_tokens']}  |  Términos distintos: "
          f"{datos['terminos_distintos']}  |  Frecuencia máxima: {datos['frecuencia_maxima']}")
    encabezado = f"{'#':>3}"
    for algoritmo in datos["algoritmos"]:
        encabezado += f"  {algoritmo['nombre']:<24}"
    print(encabezado)
    for posicion in range(len(datos["algoritmos"][0]["top"])):
        fila = f"{posicion + 1:>3}"
        for algoritmo in datos["algoritmos"]:
            item = algoritmo["top"][posicion]
            fila += f"  {item['termino']:<18}{item['frecuencia']:>6}"
        print(fila)
    print(f"Coinciden los tres algoritmos: {datos['coinciden']}")


def imprimir_benchmark(datos):
    """Imprime los tiempos por algoritmo y la tabla de escalamiento."""
    print(f"\nBenchmark: n = {datos['n']}, repeticiones = {datos['repeticiones']}")
    print(f"{'Algoritmo':<16}{'promedio_ms':>14}{'minimo_ms':>14}{'maximo_ms':>14}")
    for algoritmo in datos["algoritmos"]:
        print(f"{algoritmo['clave']:<16}{algoritmo['promedio_ms']:>14.4f}"
              f"{algoritmo['minimo_ms']:>14.4f}{algoritmo['maximo_ms']:>14.4f}")
    print(f"\n{'n':>8}{'counting_sort':>16}{'radix_sort':>14}{'bucket_sort':>14}")
    for fila in datos["escalamiento"]:
        print(f"{fila['n']:>8}{fila['counting_sort']:>16.4f}"
              f"{fila['radix_sort']:>14.4f}{fila['bucket_sort']:>14.4f}")


def guardar(nombre, datos):
    """Guarda los datos como JSON en docs/resultados."""
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_RESULTADOS / nombre
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print(f"Guardado: {ruta}")


def main():
    """Ejecuta ranking y benchmark sobre el corpus completo."""
    datos_ranking = generar_ranking(TOP)
    imprimir_ranking(datos_ranking)
    datos_benchmark = generar_benchmark(REPETICIONES)
    imprimir_benchmark(datos_benchmark)
    guardar("ranking.json", datos_ranking)
    guardar("benchmark_ranking.json", datos_benchmark)


if __name__ == "__main__":
    main()
