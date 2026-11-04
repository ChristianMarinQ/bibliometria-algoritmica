"""Utilidades compartidas para convertir distancias en similitudes normalizadas.

Los algoritmos Levenshtein y Needleman-Wunsch normalizan sus distancias cada uno
con su propia lógica ad hoc. Este módulo centraliza las tres variantes de
normalización que aparecen en el proyecto para que puedan reutilizarse y
documentarse en un único lugar.

Ninguna función de este módulo modifica el comportamiento de los algoritmos
existentes; es un complemento documentativo y utilitario.
"""


def normalizar_lineal(distancia, maximo):
    """Convierte una distancia en similitud con la fórmula 1 − d / max.

    Usada por `similitud_levenshtein`: el denominador es la longitud de la
    secuencia más larga, que es la distancia máxima posible (reemplazar todo y
    añadir el resto).

    Parámetros
    ----------
    distancia : número >= 0
        Distancia entre las dos secuencias.
    maximo : número > 0
        Distancia máxima posible (normalmente max(|A|, |B|)).

    Devuelve
    --------
    float en [0, 1]. Cuando distancia == 0 el resultado es 1.0 (idénticos);
    cuando distancia == maximo el resultado es 0.0 (completamente distintos).

    Complejidad: O(1).
    """
    if maximo == 0:
        return 1.0
    return 1.0 - distancia / maximo


def normalizar_minmax(valor, minimo, maximo):
    """Lleva un puntaje al rango [0, 1] con (valor − mínimo) / (máximo − mínimo).

    Usada por `similitud_needleman_wunsch`: el puntaje de alineamiento puede ser
    negativo, por lo que primero se traslada al origen y luego se escala.

    Parámetros
    ----------
    valor   : número
        Puntaje a normalizar.
    minimo  : número
        Puntaje mínimo posible (p. ej. −max(|A|, |B|) con penalización −1).
    maximo  : número
        Puntaje máximo posible (p. ej. min(|A|, |B|) − |A−B| con +1 en matches).

    Devuelve
    --------
    float en [0, 1], recortado para absorber errores de redondeo.
    Devuelve 1.0 cuando mínimo == máximo (caso degenerado: secuencias idénticas
    vacías, donde no existe rango válido).

    Complejidad: O(1).
    """
    denominador = maximo - minimo
    if denominador == 0:
        return 1.0
    resultado = (valor - minimo) / denominador
    # Recortar errores de punto flotante que saquen el resultado del rango teórico.
    return max(0.0, min(1.0, resultado))


def a_similitud(distancia, maximo):
    """Convierte una distancia no negativa en similitud, con guarda de caso vacío.

    Variante robusta de `normalizar_lineal` que acepta maximo == 0 (p. ej. cuando
    ambas secuencias están vacías) y devuelve 1.0 en ese caso.

    Parámetros
    ----------
    distancia : número >= 0
    maximo    : número >= 0

    Devuelve
    --------
    float en [0, 1].

    Complejidad: O(1).
    """
    return normalizar_lineal(distancia, maximo)

