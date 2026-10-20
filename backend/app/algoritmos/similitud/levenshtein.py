"""Distancia de edición de Levenshtein con programación dinámica.

Funciona sobre cualquier secuencia indexable: cadenas (nivel de caracteres)
o listas de palabras. El Req. 1 usa PALABRAS del texto preprocesado: un abstract
tiene ~200 palabras (matriz ~200×200 = 40 mil celdas) frente a ~1500 caracteres
(~2.25 millones de celdas), y la palabra es la unidad con significado.
"""

LIMITE_TRAZA = 12


def distancia_levenshtein(a, b):
    """Número mínimo de inserciones, eliminaciones y sustituciones para convertir a en b.

    Solo guarda dos filas de la matriz porque cada celda depende de la fila anterior.
    Complejidad: O(n·m) en tiempo, O(m) en memoria.
    """
    n = len(a)
    m = len(b)
    anterior = list(range(m + 1))
    for i in range(1, n + 1):
        elemento_a = a[i - 1]
        actual = [i]
        izquierda = i  # D[i][j-1]
        # Se recorren a la vez b[j-1], D[i-1][j-1] (diagonal) y D[i-1][j] (arriba)
        # para evitar indexar en el bucle interno, que domina el tiempo total.
        for elemento_b, diagonal, arriba in zip(b, anterior, anterior[1:]):
            sustituir = diagonal if elemento_a == elemento_b else diagonal + 1  # sustituir o coincidir
            eliminar = arriba + 1        # eliminar a[i-1]
            insertar = izquierda + 1     # insertar b[j-1]
            # Mínimo de los tres con comparaciones directas (más rápido que min())
            mejor = eliminar if eliminar < insertar else insertar
            izquierda = sustituir if sustituir < mejor else mejor
            actual.append(izquierda)
        anterior = actual
    return anterior[m]


def similitud_levenshtein(a, b):
    """Similitud normalizada en [0, 1]: 1 - d / max(|A|, |B|).

    Se divide por la longitud mayor porque es la distancia máxima posible
    (sustituir todo y añadir el resto). Dos secuencias vacías valen 1.
    Complejidad: O(n·m).
    """
    mayor = max(len(a), len(b))
    if mayor == 0:
        return 1.0
    return 1.0 - distancia_levenshtein(a, b) / mayor


def matriz_levenshtein(a, b):
    """Construye la matriz completa D de (n+1)×(m+1). D[i][j] = distancia entre a[:i] y b[:j].

    Complejidad: O(n·m) en tiempo y memoria.
    """
    n = len(a)
    m = len(b)
    matriz = [[0] * (m + 1) for _ in range(n + 1)]
    # Caso base: convertir un prefijo en la secuencia vacía cuesta su longitud.
    for i in range(n + 1):
        matriz[i][0] = i
    for j in range(m + 1):
        matriz[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 1
            matriz[i][j] = min(
                matriz[i - 1][j] + 1,
                matriz[i][j - 1] + 1,
                matriz[i - 1][j - 1] + costo,
            )
    return matriz


def reconstruir_camino(matriz, a, b):
    """Recorre la matriz desde (n, m) hasta (0, 0) y devuelve (camino, operaciones).

    Se prefiere la diagonal (coincidencia/sustitución) ante empates.
    Complejidad: O(n + m).
    """
    i = len(a)
    j = len(b)
    camino = [[i, j]]
    operaciones = []
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            costo = 0 if a[i - 1] == b[j - 1] else 1
            if matriz[i][j] == matriz[i - 1][j - 1] + costo:
                operaciones.append("coincidencia" if costo == 0 else "sustitucion")
                i -= 1
                j -= 1
                camino.append([i, j])
                continue
        if i > 0 and matriz[i][j] == matriz[i - 1][j] + 1:
            operaciones.append("eliminacion")
            i -= 1
        else:
            operaciones.append("insercion")
            j -= 1
        camino.append([i, j])
    camino.reverse()
    operaciones.reverse()
    return camino, operaciones


def levenshtein_con_traza(a, b, limite=LIMITE_TRAZA):
    """Calcula la similitud y devuelve (similitud, pasos, detalle) para la demostración.

    La matriz del detalle se recorta a las primeras `limite` palabras de cada
    secuencia (más la fila/columna 0); distancia y camino son del texto completo.
    Complejidad: O(n·m).
    """
    n = len(a)
    m = len(b)
    matriz = matriz_levenshtein(a, b)
    distancia = matriz[n][m]
    mayor = max(n, m)
    similitud = 1.0 if mayor == 0 else 1.0 - distancia / mayor
    camino, operaciones = reconstruir_camino(matriz, a, b)

    conteo = {"coincidencia": 0, "sustitucion": 0, "insercion": 0, "eliminacion": 0}
    for operacion in operaciones:
        conteo[operacion] += 1

    filas = min(n, limite) + 1
    columnas = min(m, limite) + 1
    recorte = [fila[:columnas] for fila in matriz[:filas]]

    pasos = [
        f"Se comparan secuencias de palabras: A tiene {n} palabras y B tiene {m} palabras.",
        f"Se crea la matriz D de {n + 1}×{m + 1}; D[i][j] es la distancia entre las primeras i palabras de A y las primeras j de B.",
        f"Caso base: D[i][0] = i (eliminar i palabras) y D[0][j] = j (insertar j palabras).",
        "Recurrencia: D[i][j] = min(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + costo), con costo 0 si las palabras son iguales y 1 si no.",
    ]
    if n > 0 and m > 0:
        costo = 0 if a[0] == b[0] else 1
        pasos.append(
            f"Ejemplo, celda D[1][1]: '{a[0]}' vs '{b[0]}' (costo {costo}) → "
            f"min({matriz[0][1]} + 1, {matriz[1][0]} + 1, {matriz[0][0]} + {costo}) = {matriz[1][1]}."
        )
    pasos.append(f"Al llenar las {n * m} celdas, la distancia es D[{n}][{m}] = {distancia}.")
    pasos.append(
        f"Camino óptimo (traceback): {conteo['coincidencia']} coincidencias, {conteo['sustitucion']} sustituciones, "
        f"{conteo['eliminacion']} eliminaciones y {conteo['insercion']} inserciones."
    )
    pasos.append(f"Similitud = 1 - {distancia} / max({n}, {m}) = 1 - {distancia} / {mayor} = {similitud:.4f}.")

    detalle = {
        "secuencia_a": list(a),
        "secuencia_b": list(b),
        "matriz": recorte,
        "truncado": n > limite or m > limite,
        "camino": camino,
        "distancia": distancia,
    }
    return similitud, pasos, detalle
