"""Alineamiento global de Needleman-Wunsch con programación dinámica.

Se aplica a secuencias de PALABRAS del texto preprocesado (~200×200 celdas por
par de abstracts, frente a ~1500×1500 si fuera por caracteres).
"""

LIMITE_TRAZA = 12
MATCH = 1
MISMATCH = -1
GAP = -1


def matriz_needleman_wunsch(a, b, match=MATCH, mismatch=MISMATCH, gap=GAP):
    """Construye la matriz de puntajes F de (n+1)×(m+1). F[i][j] = mejor alineamiento de a[:i] con b[:j].

    Complejidad: O(n·m) en tiempo y memoria.
    """
    n = len(a)
    m = len(b)
    matriz = [[0] * (m + 1) for _ in range(n + 1)]
    # Caso base: alinear un prefijo contra nada obliga a usar solo huecos.
    for i in range(n + 1):
        matriz[i][0] = i * gap
    for j in range(m + 1):
        matriz[0][j] = j * gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            puntaje = match if a[i - 1] == b[j - 1] else mismatch
            matriz[i][j] = max(
                matriz[i - 1][j - 1] + puntaje,  # alinear a[i-1] con b[j-1]
                matriz[i - 1][j] + gap,          # hueco en b
                matriz[i][j - 1] + gap,          # hueco en a
            )
    return matriz


def puntaje_needleman_wunsch(a, b, match=MATCH, mismatch=MISMATCH, gap=GAP):
    """Puntaje óptimo del alineamiento global usando solo dos filas.

    Complejidad: O(n·m) en tiempo, O(m) en memoria.
    """
    m = len(b)
    anterior = [j * gap for j in range(m + 1)]
    for i in range(1, len(a) + 1):
        elemento_a = a[i - 1]
        izquierda = i * gap  # F[i][j-1]
        actual = [izquierda]
        # Se recorren a la vez b[j-1], F[i-1][j-1] (diagonal) y F[i-1][j] (arriba)
        # para evitar indexar en el bucle interno, que domina el tiempo total.
        for elemento_b, diagonal, arriba in zip(b, anterior, anterior[1:]):
            alinear = diagonal + (match if elemento_a == elemento_b else mismatch)
            hueco_b = arriba + gap
            hueco_a = izquierda + gap
            # Máximo de los tres con comparaciones directas (más rápido que max())
            mejor = hueco_b if hueco_b > hueco_a else hueco_a
            izquierda = alinear if alinear > mejor else mejor
            actual.append(izquierda)
        anterior = actual
    return anterior[m]


def normalizar_puntaje(puntaje, n, m):
    """Lleva el puntaje a [0, 1] con (puntaje - mínimo) / (máximo - mínimo).

    Con match=+1, mismatch=-1 y gap=-1:
    - máximo posible = min(n, m) - |n - m| (todas las parejas coinciden y sobran huecos);
    - mínimo posible = -max(n, m) (todo falla; el alineamiento diagonal ya lo garantiza).
    El denominador queda 2·min(n, m). Vale 1 solo si las secuencias son idénticas.
    Complejidad: O(1).
    """
    if n == 0 and m == 0:
        return 1.0
    if n == 0 or m == 0:
        return 0.0
    maximo = min(n, m) - abs(n - m)
    minimo = -max(n, m)
    valor = (puntaje - minimo) / (maximo - minimo)
    return max(0.0, min(1.0, valor))


def similitud_needleman_wunsch(a, b):
    """Similitud normalizada en [0, 1] según normalizar_puntaje.

    Complejidad: O(n·m).
    """
    return normalizar_puntaje(puntaje_needleman_wunsch(a, b), len(a), len(b))


def reconstruir_alineamiento(matriz, a, b, match=MATCH, mismatch=MISMATCH, gap=GAP):
    """Traceback desde (n, m) hasta (0, 0). Devuelve (camino, alineado_a, alineado_b).

    En el alineamiento los huecos se representan con "-". Ante empates se
    prefiere la diagonal, luego hueco en b, luego hueco en a.
    Complejidad: O(n + m).
    """
    i = len(a)
    j = len(b)
    camino = [[i, j]]
    alineado_a = []
    alineado_b = []
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            puntaje = match if a[i - 1] == b[j - 1] else mismatch
            if matriz[i][j] == matriz[i - 1][j - 1] + puntaje:
                alineado_a.append(a[i - 1])
                alineado_b.append(b[j - 1])
                i -= 1
                j -= 1
                camino.append([i, j])
                continue
        if i > 0 and matriz[i][j] == matriz[i - 1][j] + gap:
            alineado_a.append(a[i - 1])
            alineado_b.append("-")
            i -= 1
        else:
            alineado_a.append("-")
            alineado_b.append(b[j - 1])
            j -= 1
        camino.append([i, j])
    camino.reverse()
    alineado_a.reverse()
    alineado_b.reverse()
    return camino, alineado_a, alineado_b


def needleman_wunsch_con_traza(a, b, limite=LIMITE_TRAZA):
    """Calcula la similitud y devuelve (similitud, pasos, detalle) con matriz, camino y alineamiento.

    La matriz del detalle se recorta a las primeras `limite` palabras (más la
    fila/columna 0); puntaje, camino y alineamiento son del texto completo.
    Complejidad: O(n·m).
    """
    n = len(a)
    m = len(b)
    matriz = matriz_needleman_wunsch(a, b)
    puntaje = matriz[n][m]
    similitud = normalizar_puntaje(puntaje, n, m)
    camino, alineado_a, alineado_b = reconstruir_alineamiento(matriz, a, b)

    coincidencias = 0
    discrepancias = 0
    huecos = 0
    for k in range(len(alineado_a)):
        if alineado_a[k] == "-" or alineado_b[k] == "-":
            huecos += 1
        elif alineado_a[k] == alineado_b[k]:
            coincidencias += 1
        else:
            discrepancias += 1

    filas = min(n, limite) + 1
    columnas = min(m, limite) + 1
    recorte = [fila[:columnas] for fila in matriz[:filas]]

    maximo = min(n, m) - abs(n - m)
    minimo = -max(n, m)
    pasos = [
        f"Se alinean secuencias de palabras: A tiene {n} palabras y B tiene {m} palabras.",
        f"Parámetros: coincidencia = {MATCH}, discrepancia = {MISMATCH}, hueco = {GAP}.",
        f"Se crea la matriz F de {n + 1}×{m + 1}; la fila 0 y la columna 0 valen i·hueco (solo huecos).",
        "Recurrencia: F[i][j] = max(F[i-1][j-1] + s(a_i, b_j), F[i-1][j] + hueco, F[i][j-1] + hueco).",
    ]
    if n > 0 and m > 0:
        s = MATCH if a[0] == b[0] else MISMATCH
        pasos.append(
            f"Ejemplo, celda F[1][1]: '{a[0]}' vs '{b[0]}' (s = {s}) → "
            f"max({matriz[0][0]} + {s}, {matriz[0][1]} + {GAP}, {matriz[1][0]} + {GAP}) = {matriz[1][1]}."
        )
    pasos.append(f"Puntaje óptimo del alineamiento global: F[{n}][{m}] = {puntaje}.")
    pasos.append(
        f"Traceback: alineamiento de {len(alineado_a)} columnas con {coincidencias} coincidencias, "
        f"{discrepancias} discrepancias y {huecos} huecos."
    )
    if n > 0 and m > 0:
        pasos.append(
            f"Normalización: máximo posible = min({n},{m}) - |{n}-{m}| = {maximo}; mínimo posible = -max({n},{m}) = {minimo}."
        )
        pasos.append(f"Similitud = ({puntaje} - ({minimo})) / ({maximo} - ({minimo})) = {similitud:.4f}.")
    else:
        pasos.append(f"Una de las secuencias está vacía; similitud = {similitud:.4f}.")

    detalle = {
        "secuencia_a": list(a),
        "secuencia_b": list(b),
        "matriz": recorte,
        "truncado": n > limite or m > limite,
        "camino": camino,
        "puntaje": puntaje,
        "parametros": {"match": MATCH, "mismatch": MISMATCH, "gap": GAP},
        "alineamiento": {"a": alineado_a, "b": alineado_b},
    }
    return similitud, pasos, detalle
