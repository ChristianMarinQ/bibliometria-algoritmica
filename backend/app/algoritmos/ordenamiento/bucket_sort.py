"""Bucket Sort para pares (termino, frecuencia), descendente y estable.

Distribuye los pares en m = n cubetas según su frecuencia y concatena las
cubetas de mayor a menor; dentro de cada cubeta se ordena por inserción estable.
"""


def _insertar_estable(cubeta, par):
    """Inserta par en una cubeta ya ordenada descendentemente, después de sus empates.

    Solo desplaza elementos con frecuencia estrictamente menor, por eso es estable.
    Complejidad: O(tamaño de la cubeta).
    """
    cubeta.append(par)
    posicion = len(cubeta) - 1
    while posicion > 0 and cubeta[posicion - 1][1] < par[1]:
        cubeta[posicion] = cubeta[posicion - 1]
        posicion -= 1
    cubeta[posicion] = par


def bucket_sort(pares):
    """Ordena pares (termino, frecuencia) por frecuencia descendente, de forma estable.

    Usa m = n cubetas con índice ⌊(f − min)·m / (max − min + 1)⌋. Si los valores
    están repartidos de forma aproximadamente uniforme cada cubeta recibe O(1)
    elementos en promedio y la inserción interna cuesta O(1) por elemento.
    Cuando m >= max − min + 1 (lo usual en el corpus: n ≈ 1000 términos y
    frecuencias de 1 a ~100) cada cubeta contiene una sola frecuencia, la
    inserción nunca desplaza nada y el método se comporta como Counting Sort.
    Complejidad: O(n) en promedio, O(n²) en el peor caso.
    """
    n = len(pares)
    if n == 0:
        return []

    # Rango de frecuencias para normalizar el índice de cubeta.
    minimo = pares[0][1]
    maximo = pares[0][1]
    for par in pares:
        if par[1] < minimo:
            minimo = par[1]
        if par[1] > maximo:
            maximo = par[1]

    m = n
    rango = maximo - minimo + 1
    cubetas = [[] for _ in range(m)]

    # Distribución: el índice crece con la frecuencia y siempre queda en [0, m - 1].
    # Se recorre la entrada en orden, así los empates entran en su orden original.
    for par in pares:
        indice = (par[1] - minimo) * m // rango
        _insertar_estable(cubetas[indice], par)

    # Concatenación de la cubeta de mayor frecuencia a la de menor.
    salida = []
    for indice in range(m - 1, -1, -1):
        for par in cubetas[indice]:
            salida.append(par)
    return salida
