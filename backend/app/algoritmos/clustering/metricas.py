"""Métricas de evaluación interna del clustering jerárquico, implementadas a mano.

Incluye el corte del árbol en k grupos, el coeficiente Silhouette y la
correlación cofenética (matriz cofenética + correlación de Pearson).
"""

import math


def cortar_arbol(fusiones, n, k):
    """Corta el dendrograma en k grupos aplicando solo las primeras n−k fusiones.

    Devuelve una lista de n etiquetas (0..k−1) numeradas en el orden en que
    aparece la primera hoja de cada grupo.
    Complejidad: O(n²) en el peor caso (copia de miembros al fusionar).
    """
    if k < 1 or k > n:
        raise ValueError(f"k debe estar entre 1 y {n}")
    miembros = {}
    for hoja in range(n):
        miembros[hoja] = [hoja]
    for fusion in fusiones[: n - k]:
        miembros[fusion["nuevo"]] = miembros.pop(fusion["a"]) + miembros.pop(fusion["b"])

    # Asignar a cada hoja el nodo raíz de su grupo.
    grupo_de = [0] * n
    for nodo in miembros:
        for hoja in miembros[nodo]:
            grupo_de[hoja] = nodo

    etiquetas = [0] * n
    numeracion = {}
    for hoja in range(n):
        if grupo_de[hoja] not in numeracion:
            numeracion[grupo_de[hoja]] = len(numeracion)
        etiquetas[hoja] = numeracion[grupo_de[hoja]]
    return etiquetas


def silhouette(distancias, etiquetas):
    """Coeficiente Silhouette promedio, medida de cohesión y separación de grupos.

    Para cada elemento i se calculan dos valores:
      a(i) = distancia media de i a todos los demás elementos de su mismo grupo
             (cohesión interna: cuanto más pequeño, mejor integrado está i).
      b(i) = distancia media más pequeña de i a los elementos de cualquier otro
             grupo (separación: cuanto más grande, más alejado está del grupo vecino).

    Con a(i) y b(i) se obtiene el coeficiente individual:
      s(i) = (b(i) − a(i)) / max(a(i), b(i))

    Rango: s(i) ∈ [−1, 1].
      s(i) ≈  1  → i está bien asignado (lejos de los vecinos, cerca de los suyos).
      s(i) ≈  0  → i está en la frontera entre dos grupos.
      s(i) ≈ −1  → i probablemente debería pertenecer a otro grupo.

    Por convención, los elementos que están solos en su grupo tienen s(i) = 0
    porque a(i) no está definido.

    El coeficiente Silhouette global es el promedio de todos los s(i).
    Complejidad: O(n²)
    """
    n = len(etiquetas)
    grupos = {}
    for i in range(n):
        grupos.setdefault(etiquetas[i], []).append(i)
    if len(grupos) < 2:
        return 0.0

    total = 0.0
    for i in range(n):
        propio = etiquetas[i]
        if len(grupos[propio]) == 1:
            continue  # s(i) = 0 por convención (a(i) indefinido en grupos unitarios)
        # Sumar distancias de i hacia cada grupo.
        sumas = {}
        for j in range(n):
            if j != i:
                sumas[etiquetas[j]] = sumas.get(etiquetas[j], 0.0) + distancias[i][j]
        # a(i): distancia media dentro del grupo propio (n_propio − 1 elementos).
        a = sumas.get(propio, 0.0) / (len(grupos[propio]) - 1)
        # b(i): la menor distancia media a cualquier grupo ajeno.
        b = None
        for etiqueta in grupos:
            if etiqueta == propio:
                continue
            media = sumas.get(etiqueta, 0.0) / len(grupos[etiqueta])
            if b is None or media < b:
                b = media
        mayor = a if a > b else b
        total += (b - a) / mayor if mayor > 0 else 0.0
    return total / n


def matriz_cofenetica(fusiones, n):
    """Matriz cofenética: c(i, j) = altura de la fusión donde i y j se unen por primera vez.

    Complejidad: O(n²) (cada par de hojas se asigna exactamente una vez).
    """
    cofenetica = [[0.0] * n for _ in range(n)]
    miembros = {}
    for hoja in range(n):
        miembros[hoja] = [hoja]
    for fusion in fusiones:
        grupo_a = miembros.pop(fusion["a"])
        grupo_b = miembros.pop(fusion["b"])
        for x in grupo_a:
            for y in grupo_b:
                cofenetica[x][y] = fusion["distancia"]
                cofenetica[y][x] = fusion["distancia"]
        miembros[fusion["nuevo"]] = grupo_a + grupo_b
    return cofenetica


def correlacion_pearson(x, y):
    """Coeficiente de correlación de Pearson entre dos listas del mismo tamaño.

    Devuelve 0.0 si alguna de las listas tiene varianza cero. Rango [−1, 1].
    Complejidad: O(m)
    """
    m = len(x)
    if m == 0:
        return 0.0
    media_x = sum(x) / m
    media_y = sum(y) / m
    covarianza = 0.0
    varianza_x = 0.0
    varianza_y = 0.0
    for indice in range(m):
        dx = x[indice] - media_x
        dy = y[indice] - media_y
        covarianza += dx * dy
        varianza_x += dx * dx
        varianza_y += dy * dy
    if varianza_x == 0 or varianza_y == 0:
        return 0.0
    r = covarianza / math.sqrt(varianza_x * varianza_y)
    # Recortar errores de redondeo fuera del rango teórico.
    return max(-1.0, min(1.0, r))


def correlacion_cofenetica(distancias, fusiones):
    """Correlación cofenética: qué tan fielmente el dendrograma preserva las distancias originales.

    La correlación cofenética es el coeficiente de Pearson entre dos vectores
    de longitud C(n,2) = n(n−1)/2 (todos los pares i < j):
      - distancias originales d(i, j): las distancias de la matriz de entrada.
      - distancias cofenéticas c(i, j): la altura (distancia de fusión) a la
        que i y j se unen por primera vez en el dendrograma.

    Un valor cercano a 1 indica que el dendrograma representa fielmente la
    estructura de distancias del corpus. Se recomienda un valor > 0.75.
    Un valor bajo sugiere que el criterio de enlace elegido distorsiona
    bastante la geometría real de los datos.

    Mide qué tan fielmente el dendrograma preserva las distancias reales
    (solo se usan los pares i < j). Rango [−1, 1]; más alto es mejor.
    Complejidad: O(n²)
    """
    n = len(distancias)
    cofenetica = matriz_cofenetica(fusiones, n)
    originales = []
    cofeneticas = []
    for i in range(n):
        for j in range(i + 1, n):
            originales.append(distancias[i][j])
            cofeneticas.append(cofenetica[i][j])
    return correlacion_pearson(originales, cofeneticas)
