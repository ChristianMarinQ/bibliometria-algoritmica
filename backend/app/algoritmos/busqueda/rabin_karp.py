"""Rabin-Karp: búsqueda exacta con hash rodante (rolling hash) y aritmética modular.

Cuando el hash de la ventana iguala al del patrón se verifica carácter a carácter,
así una colisión de hash nunca produce un falso positivo.
"""

CLAVE = "rabin_karp"
NOMBRE = "Rabin-Karp"

BASE = 256
# Primo grande para la búsqueda normal (colisiones muy improbables)
MODULO = 1_000_000_007
# Primo pequeño para la traza, de modo que aparezcan colisiones demostrables
MODULO_TRAZA = 101


def preprocesar(patron, base=BASE, modulo=MODULO):
    """Calcula h = base^(m-1) mod q y el hash del patrón. Devuelve un diccionario.

    Complejidad: O(m)
    """
    m = len(patron)
    h = 1
    for _ in range(m - 1):
        h = (h * base) % modulo
    hash_patron = 0
    for k in range(m):
        # Método de Horner: hash = (base·hash + código) mod q
        hash_patron = (base * hash_patron + ord(patron[k])) % modulo
    return {"base": base, "modulo": modulo, "h": h, "hash_patron": hash_patron}


def buscar_preprocesado(texto, patron, datos):
    """Busca con los datos de preprocesar. Devuelve (posiciones, comparaciones).

    comparaciones = 1 comparación de hash por ventana + comparaciones de caracteres
    hechas al verificar candidatos.
    Complejidad: O(n + m) promedio, O(n·m) peor caso (muchas colisiones).
    """
    base = datos["base"]
    modulo = datos["modulo"]
    h = datos["h"]
    hash_patron = datos["hash_patron"]
    n = len(texto)
    m = len(patron)
    posiciones = []
    comparaciones = 0
    if m > n:
        return posiciones, comparaciones
    hash_ventana = 0
    for k in range(m):
        hash_ventana = (base * hash_ventana + ord(texto[k])) % modulo
    s = 0
    while True:
        comparaciones += 1
        if hash_ventana == hash_patron:
            # Verificación carácter a carácter para descartar colisiones
            j = 0
            while j < m:
                comparaciones += 1
                if texto[s + j] != patron[j]:
                    break
                j += 1
            if j == m:
                posiciones.append(s)
        if s == n - m:
            break
        # Hash rodante: quitar el carácter que sale y agregar el que entra
        hash_ventana = (base * (hash_ventana - ord(texto[s]) * h) + ord(texto[s + m])) % modulo
        s += 1
    return posiciones, comparaciones


def buscar(texto, patron, modulo=MODULO):
    """Localiza todas las ocurrencias exactas (incluso solapadas). Devuelve (posiciones, comparaciones).

    Complejidad: O(m) preprocesamiento; búsqueda O(n + m) promedio, O(n·m) peor caso.
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    return buscar_preprocesado(texto, patron, preprocesar(patron, BASE, modulo))


def buscar_con_traza(texto, patron, modulo=MODULO_TRAZA):
    """Búsqueda Rabin-Karp que registra el hash de cada ventana, su cálculo y las colisiones.

    Por defecto usa un módulo pequeño (101) para que las colisiones sean visibles.
    Devuelve el diccionario del contrato con preprocesamiento {base, modulo, h, hash_patron, pasos}.
    Complejidad: igual que buscar.
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    base = BASE
    n = len(texto)
    m = len(patron)

    # Preprocesamiento con cada operación registrada
    pasos_pre = [f"Base = {base}, módulo primo q = {modulo}, m = {m}"]
    h = 1
    pasos_pre.append("h = base^(m−1) mod q, calculado iterativamente:")
    for k in range(m - 1):
        nuevo = (h * base) % modulo
        pasos_pre.append(f"  iteración {k + 1}: h = ({h}·{base}) mod {modulo} = {nuevo}")
        h = nuevo
    pasos_pre.append(f"h = {h}")
    pasos_pre.append("Hash del patrón por Horner: p = (base·p + código) mod q")
    hash_patron = 0
    for k in range(m):
        nuevo = (base * hash_patron + ord(patron[k])) % modulo
        pasos_pre.append(
            f"  '{patron[k]}' (código {ord(patron[k])}): p = ({base}·{hash_patron} + {ord(patron[k])}) mod {modulo} = {nuevo}"
        )
        hash_patron = nuevo
    pasos_pre.append(f"hash_patron = {hash_patron}")

    pasos = []
    posiciones = []
    total = 0
    total_colisiones = 0
    if m <= n:
        hash_ventana = 0
        for k in range(m):
            hash_ventana = (base * hash_ventana + ord(texto[k])) % modulo
        calculo = f"hash inicial de la ventana [0..{m - 1}] por Horner = {hash_ventana}"
        s = 0
        while True:
            total += 1
            comparaciones = []
            coincidencia = False
            colision = False
            if hash_ventana == hash_patron:
                j = 0
                while j < m:
                    igual = texto[s + j] == patron[j]
                    comparaciones.append({"i": s + j, "j": j, "igual": igual})
                    total += 1
                    if not igual:
                        break
                    j += 1
                if j == m:
                    coincidencia = True
                    posiciones.append(s)
                    motivo = (
                        f"hash(ventana) = {hash_ventana} = hash(patrón): se verifican los {m} caracteres"
                        f" y todos coinciden → ocurrencia en {s}."
                    )
                else:
                    colision = True
                    total_colisiones += 1
                    motivo = (
                        f"Colisión: hash(ventana) = {hash_ventana} = hash(patrón) pero en j={j}"
                        f" '{texto[s + j]}' ≠ '{patron[j]}'. La verificación evita el falso positivo."
                    )
            else:
                motivo = (
                    f"hash(ventana) = {hash_ventana} ≠ hash(patrón) = {hash_patron}:"
                    f" se descarta sin comparar caracteres."
                )
            ultimo = s == n - m
            pasos.append({
                "alineacion": s,
                "comparaciones": comparaciones,
                "coincidencia": coincidencia,
                "desplazamiento": 1,
                "motivo": motivo,
                "hash_ventana": hash_ventana,
                "calculo_hash": calculo,
                "colision": colision,
            })
            if ultimo:
                break
            sale = ord(texto[s])
            entra = ord(texto[s + m])
            anterior = hash_ventana
            hash_ventana = (base * (hash_ventana - sale * h) + entra) % modulo
            calculo = (
                f"({base}·({anterior} − {sale}·{h}) + {entra}) mod {modulo} = {hash_ventana}"
                f" (sale '{texto[s]}', entra '{texto[s + m]}')"
            )
            s += 1
    return {
        "clave": CLAVE,
        "nombre": NOMBRE,
        "texto": texto,
        "patron": patron,
        "preprocesamiento": {
            "base": base,
            "modulo": modulo,
            "h": h,
            "hash_patron": hash_patron,
            "pasos": pasos_pre,
        },
        "pasos": pasos,
        "posiciones": posiciones,
        "total_comparaciones": total,
        "total_colisiones": total_colisiones,
    }
