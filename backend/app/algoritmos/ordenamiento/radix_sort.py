"""Radix Sort LSD en base 10 para pares (termino, frecuencia), descendente y estable.

Ordena dígito por dígito (unidades, decenas, ...) con un Counting Sort estable.
Basado en https://www.geeksforgeeks.org/dsa/radix-sort/ (LSD con un Counting Sort
por dígito), adaptado a pares y a orden descendente.
"""

from app.algoritmos.ordenamiento.counting_sort import ordenar_por_clave_descendente

BASE = 10


def _clave_digito(divisor):
    """Devuelve una función que extrae el dígito de la frecuencia en la posición indicada."""
    def clave(par):
        return (par[1] // divisor) % BASE
    return clave


def radix_sort(pares):
    """Ordena pares (termino, frecuencia) por frecuencia descendente, de forma estable.

    d es la cantidad de dígitos de la frecuencia máxima y b = 10 la base.
    Complejidad: O(d·(n + b)).
    """
    if not pares:
        return []
    maximo = 0
    for par in pares:
        if par[1] > maximo:
            maximo = par[1]

    resultado = pares
    divisor = 1
    # Una pasada por dígito, del menos significativo al más significativo.
    # La estabilidad de cada pasada garantiza que el orden de los dígitos
    # anteriores (y el alfabético de la entrada) se conserve en los empates.
    while True:
        resultado = ordenar_por_clave_descendente(resultado, _clave_digito(divisor), BASE - 1)
        divisor *= BASE
        if maximo // divisor == 0:
            break
    return resultado
