"""Clustering jerárquico aglomerativo implementado desde cero.

Incluye Single, Complete y Average Linkage (UPGMA) usando la regla de
actualización de Lance-Williams, el registro de fusiones y el árbol anidado.
"""

# Claves de los métodos y su nombre para mostrar.
METODOS = {
    "single": "Single Linkage",
    "complete": "Complete Linkage",
    "average": "Average Linkage (UPGMA)",
}


def coeficientes_lance_williams(metodo, tamano_i, tamano_j):
    """Devuelve los coeficientes (alfa_i, alfa_j, beta, gamma) de Lance-Williams.

    Al fusionar los grupos i y j, la distancia del nuevo grupo a otro grupo k es:

        d(k, i∪j) = alfa_i·d(k,i) + alfa_j·d(k,j) + beta·d(i,j) + gamma·|d(k,i) − d(k,j)|

    - single:   alfa_i = alfa_j = 1/2, beta = 0, gamma = −1/2  -> min(d(k,i), d(k,j))
    - complete: alfa_i = alfa_j = 1/2, beta = 0, gamma = +1/2  -> max(d(k,i), d(k,j))
    - average:  alfa_i = |i|/(|i|+|j|), alfa_j = |j|/(|i|+|j|), beta = gamma = 0
                -> promedio ponderado por tamaño (UPGMA)
    Complejidad: O(1)
    """
    if metodo == "single":
        return 0.5, 0.5, 0.0, -0.5
    if metodo == "complete":
        return 0.5, 0.5, 0.0, 0.5
    if metodo == "average":
        total = tamano_i + tamano_j
        return tamano_i / total, tamano_j / total, 0.0, 0.0
    raise ValueError(f"Método de enlace desconocido: {metodo}")


def agrupar(distancias, metodo):
    """Ejecuta el clustering aglomerativo sobre una matriz de distancias n×n.

    Devuelve la lista de fusiones (equivalente a una matriz de enlace):
    [{"paso", "a", "b", "nuevo", "distancia", "tamano"}]. Las hojas son los
    nodos 0..n−1 y cada fusión crea el nodo n, n+1, …, 2n−2.
    En cada paso se busca el par activo más cercano (empates: el par de ids
    menores) y se actualizan sus distancias con Lance-Williams.
    Complejidad: O(n³) en tiempo (n−1 pasos × búsqueda O(n²)) y O(n²) en espacio.
    """
    if metodo not in METODOS:
        raise ValueError(f"Método de enlace desconocido: {metodo}")
    n = len(distancias)
    if n == 0:
        return []
    total_nodos = 2 * n - 1

    # Matriz de trabajo de (2n−1)×(2n−1): las filas nuevas se llenan al fusionar.
    matriz = [[0.0] * total_nodos for _ in range(total_nodos)]
    for i in range(n):
        for j in range(n):
            matriz[i][j] = float(distancias[i][j])

    tamanos = [1] * n + [0] * (n - 1)
    activos = list(range(n))
    fusiones = []

    for paso in range(1, n):
        # 1. Encontrar el par de grupos activos con menor distancia.
        mejor_a = -1
        mejor_b = -1
        mejor_distancia = None
        for posicion_i in range(len(activos)):
            i = activos[posicion_i]
            for posicion_j in range(posicion_i + 1, len(activos)):
                j = activos[posicion_j]
                if mejor_distancia is None or matriz[i][j] < mejor_distancia:
                    mejor_distancia = matriz[i][j]
                    mejor_a, mejor_b = i, j

        # 2. Crear el nuevo nodo y registrar la fusión.
        nuevo = n + paso - 1
        tamanos[nuevo] = tamanos[mejor_a] + tamanos[mejor_b]
        fusiones.append({
            "paso": paso,
            "a": mejor_a,
            "b": mejor_b,
            "nuevo": nuevo,
            "distancia": mejor_distancia,
            "tamano": tamanos[nuevo],
        })

        # 3. Actualizar distancias del nuevo grupo con la regla de Lance-Williams.
        alfa_a, alfa_b, beta, gamma = coeficientes_lance_williams(
            metodo, tamanos[mejor_a], tamanos[mejor_b])
        restantes = []
        for k in activos:
            if k == mejor_a or k == mejor_b:
                continue
            d_ka = matriz[k][mejor_a]
            d_kb = matriz[k][mejor_b]
            diferencia = d_ka - d_kb if d_ka >= d_kb else d_kb - d_ka
            valor = alfa_a * d_ka + alfa_b * d_kb + beta * mejor_distancia + gamma * diferencia
            matriz[k][nuevo] = valor
            matriz[nuevo][k] = valor
            restantes.append(k)
        restantes.append(nuevo)
        activos = restantes

    return fusiones


def construir_arbol(fusiones, hojas):
    """Arma el árbol anidado del contrato a partir de las fusiones.

    `hojas` es una lista con un diccionario por elemento (p. ej.
    {"articulo_id": 1, "titulo": "…"}) que se copia en cada hoja.
    Devuelve la raíz: los nodos internos tienen "hijos" (siempre 2).
    Complejidad: O(n)
    """
    nodos = {}
    for indice in range(len(hojas)):
        hoja = {"id": indice}
        for clave in hojas[indice]:
            hoja[clave] = hojas[indice][clave]
        hoja["distancia"] = 0
        hoja["tamano"] = 1
        nodos[indice] = hoja
    if not fusiones:
        return nodos.get(0)

    for fusion in fusiones:
        nodos[fusion["nuevo"]] = {
            "id": fusion["nuevo"],
            "distancia": fusion["distancia"],
            "tamano": fusion["tamano"],
            "hijos": [nodos.pop(fusion["a"]), nodos.pop(fusion["b"])],
        }
    return nodos[fusiones[-1]["nuevo"]]
