"""Knuth-Morris-Pratt: búsqueda exacta de patrones con la función de fallo (LPS).

Se implementa desde cero usando solo índices y comparaciones de caracteres.
"""

CLAVE = "kmp"
NOMBRE = "Knuth-Morris-Pratt"


def preprocesar(patron):
    """Calcula el arreglo LPS (prefijo propio más largo que también es sufijo).

    lps[k] = longitud del borde más largo de patron[0..k].
    Complejidad: O(m)
    """
    m = len(patron)
    lps = [0] * m
    longitud = 0
    k = 1
    while k < m:
        if patron[k] == patron[longitud]:
            longitud += 1
            lps[k] = longitud
            k += 1
        elif longitud > 0:
            # Se prueba el siguiente borde más corto sin avanzar k
            longitud = lps[longitud - 1]
        else:
            lps[k] = 0
            k += 1
    return lps


def preprocesar_con_traza(patron):
    """Igual que preprocesar, pero devuelve (lps, pasos_lps) con cada decisión en texto.

    Complejidad: O(m)
    """
    m = len(patron)
    lps = [0] * m
    pasos = []
    if m > 0:
        pasos.append(f"lps[0] = 0 (un solo carácter '{patron[0]}' no tiene borde propio)")
    longitud = 0
    k = 1
    while k < m:
        if patron[k] == patron[longitud]:
            longitud += 1
            lps[k] = longitud
            pasos.append(
                f"k={k}: patron[{k}]='{patron[k]}' = patron[{longitud - 1}]='{patron[longitud - 1]}'"
                f" → el borde crece, lps[{k}] = {longitud}"
            )
            k += 1
        elif longitud > 0:
            anterior = longitud
            longitud = lps[longitud - 1]
            pasos.append(
                f"k={k}: patron[{k}]='{patron[k]}' ≠ patron[{anterior}]='{patron[anterior]}'"
                f" → se retrocede al borde anterior: longitud = lps[{anterior - 1}] = {longitud}"
            )
        else:
            lps[k] = 0
            pasos.append(
                f"k={k}: patron[{k}]='{patron[k]}' ≠ patron[0]='{patron[0]}' y longitud=0 → lps[{k}] = 0"
            )
            k += 1
    pasos.append(f"LPS final: {lps}")
    return lps, pasos


def buscar_preprocesado(texto, patron, lps):
    """Busca el patrón usando un LPS ya calculado. Devuelve (posiciones, comparaciones).

    El índice del texto nunca retrocede; ante un fallo solo se reubica j con lps.
    Complejidad: O(n)
    """
    n = len(texto)
    m = len(patron)
    posiciones = []
    comparaciones = 0
    i = 0
    j = 0
    # Se continúa mientras el resto del texto alcance para completar el patrón
    while n - i >= m - j:
        comparaciones += 1
        if texto[i] == patron[j]:
            i += 1
            j += 1
            if j == m:
                posiciones.append(i - m)
                # Coincidencia completa: se reutiliza el borde para permitir solapamientos
                j = lps[j - 1]
        elif j > 0:
            j = lps[j - 1]
        else:
            i += 1
    return posiciones, comparaciones


def buscar(texto, patron):
    """Localiza todas las ocurrencias exactas (incluso solapadas). Devuelve (posiciones, comparaciones).

    Complejidad: O(n + m) — O(m) preprocesamiento + O(n) búsqueda.
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    return buscar_preprocesado(texto, patron, preprocesar(patron))


def buscar_con_traza(texto, patron):
    """Búsqueda KMP que registra cada alineación, sus comparaciones y el desplazamiento.

    Devuelve el diccionario del contrato: clave, nombre, texto, patron,
    preprocesamiento {lps, pasos_lps}, pasos, posiciones y total_comparaciones.
    Complejidad: O(n + m)
    """
    if len(patron) == 0:
        raise ValueError("El patrón no puede estar vacío")
    lps, pasos_lps = preprocesar_con_traza(patron)
    n = len(texto)
    m = len(patron)
    pasos = []
    posiciones = []
    total = 0
    i = 0
    j = 0
    while n - i >= m - j:
        alineacion = i - j
        comparaciones = []
        # Comparaciones de izquierda a derecha en la alineación actual
        while True:
            igual = texto[i] == patron[j]
            comparaciones.append({"i": i, "j": j, "igual": igual})
            total += 1
            if not igual:
                break
            i += 1
            j += 1
            if j == m:
                break
        if j == m:
            posiciones.append(alineacion)
            borde = lps[m - 1]
            desplazamiento = m - borde
            motivo = (
                f"Coincidencia completa en la posición {alineacion}. El borde más largo del patrón"
                f" mide lps[{m - 1}] = {borde}, se desplaza {m} − {borde} = {desplazamiento}"
                f" y se continúa con j = {borde} (sin retroceder en el texto)."
            )
            coincidencia = True
            j = borde
        elif j > 0:
            borde = lps[j - 1]
            desplazamiento = j - borde
            motivo = (
                f"Fallo en i={i}, j={j}: '{texto[i]}' ≠ '{patron[j]}'. Ya coincidían {j} caracteres;"
                f" lps[{j - 1}] = {borde}, así que se desplaza {j} − {borde} = {desplazamiento}"
                f" y j pasa a {borde} (esos {borde} caracteres no se vuelven a comparar)."
            )
            coincidencia = False
            j = borde
        else:
            desplazamiento = 1
            motivo = (
                f"Fallo en el primer carácter: '{texto[i]}' ≠ '{patron[0]}'."
                f" No hay prefijo reutilizable, se avanza 1 posición en el texto."
            )
            coincidencia = False
            i += 1
        pasos.append({
            "alineacion": alineacion,
            "comparaciones": comparaciones,
            "coincidencia": coincidencia,
            "desplazamiento": desplazamiento,
            "motivo": motivo,
            "hash_ventana": None,
        })
    return {
        "clave": CLAVE,
        "nombre": NOMBRE,
        "texto": texto,
        "patron": patron,
        "preprocesamiento": {"lps": lps, "pasos_lps": pasos_lps},
        "pasos": pasos,
        "posiciones": posiciones,
        "total_comparaciones": total,
    }
