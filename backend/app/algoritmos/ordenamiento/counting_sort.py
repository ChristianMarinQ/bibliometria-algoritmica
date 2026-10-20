"""Counting Sort estable y descendente para pares (termino, frecuencia).

No compara elementos entre sí: usa la frecuencia como índice de un arreglo de conteo.
"""


def ordenar_por_clave_descendente(pares, clave, k):
    """Ordena pares de forma estable y descendente según clave(par), un entero en [0, k].

    Es el núcleo compartido por Counting Sort (clave = frecuencia) y por
    Radix Sort (clave = un dígito de la frecuencia, k = base - 1).
    Complejidad: O(n + k).
    """
    n = len(pares)
    if n == 0:
        return []

    # Paso 1: conteo de cuántos elementos tiene cada valor de clave.
    conteo = [0] * (k + 1)
    for par in pares:
        conteo[clave(par)] += 1

    # Paso 2: suma de prefijos de mayor a menor. Al terminar, conteo[v] es la
    # cantidad de elementos con clave >= v, es decir, la posición final (exclusiva)
    # del último elemento con clave v en el orden descendente.
    for valor in range(k - 1, -1, -1):
        conteo[valor] += conteo[valor + 1]

    # Paso 3: recorrido inverso de la entrada. Como se llena cada grupo desde su
    # última posición hacia atrás, los empates conservan su orden original (estable).
    salida = [None] * n
    for indice in range(n - 1, -1, -1):
        par = pares[indice]
        valor = clave(par)
        conteo[valor] -= 1
        salida[conteo[valor]] = par
    return salida


def _frecuencia(par):
    """Devuelve la frecuencia de un par (termino, frecuencia)."""
    return par[1]


def counting_sort(pares):
    """Ordena pares (termino, frecuencia) por frecuencia descendente, de forma estable.

    k es la frecuencia máxima: el arreglo de conteo tiene k + 1 casillas.
    Complejidad: O(n + k).
    """
    if not pares:
        return []
    # Búsqueda lineal del máximo para dimensionar el arreglo de conteo.
    k = 0
    for par in pares:
        if par[1] > k:
            k = par[1]
    return ordenar_por_clave_descendente(pares, _frecuencia, k)
