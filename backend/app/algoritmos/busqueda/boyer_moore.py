"""Boyer-Moore: búsqueda exacta comparando de derecha a izquierda.

Combina la regla del carácter malo y la regla del sufijo bueno (versión fuerte,
casos 1 y 2) y en cada fallo aplica el mayor de los dos desplazamientos.
"""

CLAVE = "boyer_moore"
NOMBRE = "Boyer-Moore"


def tabla_caracter_malo(patron):
    """Construye {caracter: última posición en el patrón}.

    Un carácter que no está en el diccionario equivale a la posición -1.
    Complejidad: O(m)
    """
    tabla = {}
    for k in range(len(patron)):
        # Al recorrer de izquierda a derecha queda guardada la última aparición
        tabla[patron[k]] = k
    return tabla


def tabla_sufijo_bueno(patron):
    """Calcula (desplazamientos, bordes) de la regla del sufijo bueno.

    desplazamientos[j + 1] es el salto cuando falla patron[j] y ya coincidió
    el sufijo patron[j+1..m-1]; desplazamientos[0] es el salto tras una coincidencia
    completa. bordes[k] = inicio del borde más ancho del sufijo patron[k..m-1].
    Caso 1: el sufijo bueno aparece otra vez en el patrón precedido de otro carácter.
    Caso 2: solo un prefijo del patrón coincide con una parte del sufijo bueno.
    Complejidad: O(m)
    """
    desplazamientos, bordes, _ = _sufijo_bueno(patron, False)
    return desplazamientos, bordes


def _sufijo_bueno(patron, con_traza):
    """Implementación común del sufijo bueno; opcionalmente registra los pasos en texto."""
    m = len(patron)
    desplazamientos = [0] * (m + 1)
    bordes = [0] * (m + 1)
    pasos = []

    # Caso 1: recorrer el patrón de derecha a izquierda calculando bordes de cada sufijo
    k = m
    j = m + 1
    bordes[k] = j
    while k > 0:
        # Mientras el borde no se pueda extender, se registra el salto y se pasa al borde menor
        while j <= m and patron[k - 1] != patron[j - 1]:
            if desplazamientos[j] == 0:
                desplazamientos[j] = j - k
                if con_traza and j == m:
                    pasos.append(
                        f"Caso 1: fallo en el último carácter (sin sufijo coincidente);"
                        f" patron[{k - 1}]='{patron[k - 1]}' ≠ patron[{m - 1}]='{patron[m - 1]}'"
                        f" → sufijo_bueno[{m}] = {j} − {k} = {j - k}"
                    )
                elif con_traza:
                    pasos.append(
                        f"Caso 1: el sufijo '{patron[j:]}' reaparece en la posición {k}"
                        f" precedido de '{patron[k - 1]}' ≠ '{patron[j - 1]}'"
                        f" → sufijo_bueno[{j}] = {j} − {k} = {j - k}"
                    )
            j = bordes[j]
        k -= 1
        j -= 1
        bordes[k] = j

    # Caso 2: las posiciones sin salto usan el borde más ancho del patrón completo
    j = bordes[0]
    if con_traza and j >= m:
        pasos.append(
            f"Caso 2: el patrón no tiene borde (ningún prefijo propio es sufijo);"
            f" las posiciones restantes desplazan el patrón completo: {j}"
        )
    elif con_traza:
        pasos.append(
            f"Caso 2: el borde más ancho del patrón empieza en {j}"
            f" (prefijo '{patron[:m - j]}' que también es sufijo)"
        )
    for k in range(m + 1):
        if desplazamientos[k] == 0:
            desplazamientos[k] = j
            if con_traza:
                pasos.append(f"Caso 2: sufijo_bueno[{k}] = {j} (se alinea el prefijo del patrón con el sufijo)")
        if k == j:
            j = bordes[j]
    if con_traza:
        pasos.append(f"Tabla de sufijo bueno final: {desplazamientos}")
    return desplazamientos, bordes, pasos


def preprocesar(patron):
    """Calcula las dos tablas heurísticas. Devuelve (caracter_malo, sufijo_bueno).

    Complejidad: O(m)
    """
    desplazamientos, _ = tabla_sufijo_bueno(patron)
    return tabla_caracter_malo(patron), desplazamientos


def buscar_preprocesado(texto, patron, tablas):
    """Busca con las tablas ya calculadas. Devuelve (posiciones, comparaciones).

    Complejidad: O(n·m) en el peor caso, O(n/m) en el mejor caso (sublineal).
    """
    caracter_malo, sufijo_bueno = tablas
    n = len(texto)
    m = len(patron)
    posiciones = []
    comparaciones = 0
    s = 0
    while s <= n - m:
        j = m - 1
        # Comparación de derecha a izquierda
        while j >= 0:
            comparaciones += 1
            if patron[j] != texto[s + j]:
                break
            j -= 1
        if j < 0:
            posiciones.append(s)
            s += sufijo_bueno[0]
        else:
            salto_malo = j - caracter_malo.get(texto[s + j], -1)
            salto_bueno = sufijo_bueno[j + 1]
            # Se toma el máximo de las dos reglas (el carácter malo puede ser negativo)
            s += salto_malo if salto_malo > salto_bueno else salto_bueno
    return posiciones, comparaciones


def buscar(texto, patron):
    """Localiza todas las ocurrencias exactas (incluso solapadas). Devuelve (posiciones, comparaciones).

    Complejidad: O(m + σ) preprocesamiento; búsqueda O(n·m) peor caso, O(n/m) mejor caso.
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    return buscar_preprocesado(texto, patron, preprocesar(patron))


def buscar_con_traza(texto, patron):
    """Búsqueda Boyer-Moore que registra cada alineación, comparaciones y el salto elegido.

    Devuelve el diccionario del contrato con preprocesamiento
    {caracter_malo, sufijo_bueno, bordes, pasos}.
    Complejidad: igual que buscar.
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    n = len(texto)
    m = len(patron)
    caracter_malo = tabla_caracter_malo(patron)
    sufijo_bueno, bordes, pasos_sufijo = _sufijo_bueno(patron, True)

    pasos_pre = ["Regla del carácter malo: se guarda la última posición de cada carácter del patrón."]
    for k in range(m):
        pasos_pre.append(f"'{patron[k]}' aparece en la posición {k} → caracter_malo['{patron[k]}'] = {k}")
    pasos_pre.append(f"Tabla de carácter malo final: {caracter_malo} (caracteres ausentes = -1)")
    pasos_pre.append("Regla del sufijo bueno (bordes de los sufijos del patrón):")
    pasos_pre.extend(pasos_sufijo)

    pasos = []
    posiciones = []
    total = 0
    s = 0
    while s <= n - m:
        comparaciones = []
        j = m - 1
        while j >= 0:
            igual = patron[j] == texto[s + j]
            comparaciones.append({"i": s + j, "j": j, "igual": igual})
            total += 1
            if not igual:
                break
            j -= 1
        if j < 0:
            posiciones.append(s)
            desplazamiento = sufijo_bueno[0]
            motivo = (
                f"Coincidencia completa en la posición {s}. Se aplica sufijo_bueno[0] = {desplazamiento}"
                f" (alinea el borde más ancho del patrón)."
            )
            coincidencia = True
        else:
            c = texto[s + j]
            ultima = caracter_malo.get(c, -1)
            salto_malo = j - ultima
            salto_bueno = sufijo_bueno[j + 1]
            desplazamiento = salto_malo if salto_malo > salto_bueno else salto_bueno
            if ultima >= 0:
                detalle_malo = f"'{c}' aparece por última vez en el patrón en {ultima} → {j} − {ultima} = {salto_malo}"
            else:
                detalle_malo = f"'{c}' no aparece en el patrón → {j} − (−1) = {salto_malo}"
            if j == m - 1:
                detalle_bueno = f"aún no hay sufijo coincidente → sufijo_bueno[{m}] = {salto_bueno}"
            else:
                detalle_bueno = f"sufijo '{patron[j + 1:]}' ya coincidió → sufijo_bueno[{j + 1}] = {salto_bueno}"
            regla = "carácter malo" if salto_malo > salto_bueno else "sufijo bueno"
            motivo = (
                f"Carácter malo '{c}' en i={s + j} (patrón tenía '{patron[j]}' en j={j}): {detalle_malo}."
                f" Sufijo bueno: {detalle_bueno}. Se toma el máximo: {desplazamiento} ({regla})."
            )
            coincidencia = False
        pasos.append({
            "alineacion": s,
            "comparaciones": comparaciones,
            "coincidencia": coincidencia,
            "desplazamiento": desplazamiento,
            "motivo": motivo,
            "hash_ventana": None,
        })
        s += desplazamiento
    return {
        "clave": CLAVE,
        "nombre": NOMBRE,
        "texto": texto,
        "patron": patron,
        "preprocesamiento": {
            "caracter_malo": caracter_malo,
            "sufijo_bueno": sufijo_bueno,
            "bordes": bordes,
            "pasos": pasos_pre,
        },
        "pasos": pasos,
        "posiciones": posiciones,
        "total_comparaciones": total,
    }
