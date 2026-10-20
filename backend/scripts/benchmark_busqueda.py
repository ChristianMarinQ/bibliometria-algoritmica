"""Benchmark del Req. 3: KMP, Boyer-Moore y Rabin-Karp sobre el corpus y sobre un texto grande.

Mide por separado preprocesamiento y búsqueda, imprime una tabla y guarda
docs/resultados/benchmark_busqueda.json. Ejecutar desde backend:
    python scripts/benchmark_busqueda.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import RAIZ_PROYECTO  # noqa: E402
from app.nucleo.corpus import cargar_corpus  # noqa: E402
from app.nucleo.medicion import medir  # noqa: E402
from app.servicios.busqueda import ALGORITMOS, a_minusculas  # noqa: E402

PATRONES = [
    ("corto", "ai"),
    ("medio", "learning"),
    ("largo", "artificial intelligence in education"),
    ("inexistente", "quantum blockchain"),
]
FACTOR_TEXTO_GRANDE = 50
REPETICIONES_PREPROCESAMIENTO = 2000
COMPLEJIDAD = {
    "kmp": {"preprocesamiento": "O(m)", "busqueda": "O(n)", "peor_caso": "O(n + m)"},
    "boyer_moore": {"preprocesamiento": "O(m + σ)", "busqueda": "O(n/m) mejor, O(n·m) peor",
                    "peor_caso": "O(n·m)"},
    "rabin_karp": {"preprocesamiento": "O(m)", "busqueda": "O(n + m) promedio, O(n·m) peor",
                   "peor_caso": "O(n·m)"},
}
RUTA_SALIDA = RAIZ_PROYECTO / "docs" / "resultados" / "benchmark_busqueda.json"


def buscar_en_textos(modulo, textos, patron, preproceso):
    """Busca en todos los textos con un preprocesamiento ya calculado. Devuelve (coincidencias, comparaciones)."""
    coincidencias = 0
    comparaciones = 0
    for texto in textos:
        posiciones, comps = modulo.buscar_preprocesado(texto, patron, preproceso)
        coincidencias += len(posiciones)
        comparaciones += comps
    return coincidencias, comparaciones


def medir_escenario(nombre, textos, repeticiones_busqueda):
    """Mide los tres algoritmos con todos los patrones sobre una lista de textos."""
    n = 0
    for texto in textos:
        n += len(texto)
    filas = []
    for tipo, patron in PATRONES:
        for clave, modulo in ALGORITMOS.items():
            preproceso, tiempo_pre = medir(modulo.preprocesar, patron, repeticiones=REPETICIONES_PREPROCESAMIENTO)
            (coincidencias, comparaciones), tiempo_busqueda = medir(
                buscar_en_textos, modulo, textos, patron, preproceso, repeticiones=repeticiones_busqueda
            )
            filas.append({
                "escenario": nombre,
                "n": n,
                "tipo_patron": tipo,
                "patron": patron,
                "m": len(patron),
                "clave": clave,
                "nombre": modulo.NOMBRE,
                "tiempo_preprocesamiento_ms": tiempo_pre,
                "tiempo_busqueda_ms": tiempo_busqueda,
                "comparaciones": comparaciones,
                "comparaciones_por_caracter": comparaciones / n if n else 0,
                "coincidencias": coincidencias,
            })
    return {"escenario": nombre, "n": n, "repeticiones_busqueda": repeticiones_busqueda, "filas": filas}


def imprimir_tabla(escenario):
    """Imprime la tabla de un escenario en consola."""
    print(f"\n=== {escenario['escenario']} (n = {escenario['n']} caracteres) ===")
    print(f"{'patrón':<38}{'algoritmo':<20}{'prep. ms':>10}{'búsq. ms':>11}{'comparac.':>11}{'comp/n':>8}{'ocurr.':>8}")
    for fila in escenario["filas"]:
        print(
            f"{fila['patron']:<38}{fila['nombre']:<20}{fila['tiempo_preprocesamiento_ms']:>10.4f}"
            f"{fila['tiempo_busqueda_ms']:>11.3f}{fila['comparaciones']:>11}"
            f"{fila['comparaciones_por_caracter']:>8.3f}{fila['coincidencias']:>8}"
        )


def main():
    """Ejecuta el benchmark completo y guarda el JSON de resultados."""
    textos = [a_minusculas(articulo["abstract"]) for articulo in cargar_corpus()]
    # Texto grande: el corpus concatenado ×50 para que las diferencias sean visibles
    texto_grande = " ".join(textos) * FACTOR_TEXTO_GRANDE
    escenarios = [
        medir_escenario("Corpus (20 abstracts)", textos, 10),
        medir_escenario(f"Corpus concatenado ×{FACTOR_TEXTO_GRANDE}", [texto_grande], 1),
    ]
    for escenario in escenarios:
        imprimir_tabla(escenario)
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump({"complejidad": COMPLEJIDAD, "escenarios": escenarios}, archivo, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
