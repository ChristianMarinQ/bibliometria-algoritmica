"""Coeficiente de Jaccard entre conjuntos de tokens preprocesados."""


def a_conjunto(tokens):
    """Convierte la lista de tokens en un conjunto (elimina repeticiones).

    Complejidad: O(t).
    """
    conjunto = set()
    for token in tokens:
        conjunto.add(token)
    return conjunto


def interseccion(conjunto_a, conjunto_b):
    """Elementos presentes en ambos conjuntos, recorriendo el más pequeño.

    Complejidad: O(min(|A|, |B|)) con búsqueda en tabla hash O(1).
    """
    if len(conjunto_a) > len(conjunto_b):
        conjunto_a, conjunto_b = conjunto_b, conjunto_a
    comunes = set()
    for elemento in conjunto_a:
        if elemento in conjunto_b:
            comunes.add(elemento)
    return comunes


def similitud_jaccard(tokens_a, tokens_b):
    """J(A, B) = |A ∩ B| / |A ∪ B|, con |A ∪ B| = |A| + |B| - |A ∩ B|. Dos vacíos valen 1.

    Complejidad: O(|A| + |B|).
    """
    conjunto_a = a_conjunto(tokens_a)
    conjunto_b = a_conjunto(tokens_b)
    tam_interseccion = len(interseccion(conjunto_a, conjunto_b))
    tam_union = len(conjunto_a) + len(conjunto_b) - tam_interseccion
    if tam_union == 0:
        return 1.0
    return tam_interseccion / tam_union


def jaccard_con_traza(tokens_a, tokens_b):
    """Calcula la similitud y devuelve (similitud, pasos, detalle) con los conjuntos.

    Complejidad: O(|A| + |B| + k·log k) por ordenar los términos mostrados.
    """
    conjunto_a = a_conjunto(tokens_a)
    conjunto_b = a_conjunto(tokens_b)
    comunes = interseccion(conjunto_a, conjunto_b)
    solo_a = [t for t in conjunto_a if t not in comunes]
    solo_b = [t for t in conjunto_b if t not in comunes]
    tam_interseccion = len(comunes)
    tam_union = len(conjunto_a) + len(conjunto_b) - tam_interseccion
    similitud = 1.0 if tam_union == 0 else tam_interseccion / tam_union

    pasos = [
        f"A tiene {len(tokens_a)} tokens, de los cuales {len(conjunto_a)} son distintos; B tiene {len(tokens_b)} tokens y {len(conjunto_b)} distintos.",
        f"Intersección |A ∩ B| = {tam_interseccion} términos compartidos.",
        f"Unión |A ∪ B| = |A| + |B| - |A ∩ B| = {len(conjunto_a)} + {len(conjunto_b)} - {tam_interseccion} = {tam_union}.",
        f"J(A, B) = {tam_interseccion} / {tam_union} = {similitud:.4f}.",
    ]
    detalle = {
        "interseccion": sorted(comunes),
        "solo_a": sorted(solo_a),
        "solo_b": sorted(solo_b),
        "tam_interseccion": tam_interseccion,
        "tam_union": tam_union,
    }
    return similitud, pasos, detalle
