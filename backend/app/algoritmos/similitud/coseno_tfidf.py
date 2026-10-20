"""Similitud del coseno entre vectores TF-IDF dispersos.

Los pesos TF-IDF se calculan con app.nucleo.vectorizacion; el IDF se recibe ya
calculado sobre todo el corpus para que los pesos no dependan de la selección.
"""

import math

from app.nucleo.vectorizacion import frecuencia_termino, norma, producto_punto

MAXIMO_TERMINOS_TRAZA = 25


def vector_tfidf(tokens, idf):
    """Vector disperso {termino: tf · idf} de un documento.

    Un término que no esté en el IDF (no visto en el corpus) recibe idf = 1.
    Complejidad: O(t), con t el número de tokens.
    """
    tf = frecuencia_termino(tokens)
    vector = {}
    for termino in tf:
        vector[termino] = tf[termino] * idf.get(termino, 1.0)
    return vector


def similitud_coseno(vector_a, vector_b):
    """cos(θ) = (A·B) / (‖A‖·‖B‖) entre vectores dispersos; 0 si alguno es nulo.

    Con pesos no negativos el resultado ya está en [0, 1].
    Complejidad: O(|A| + |B|).
    """
    norma_a = norma(vector_a)
    norma_b = norma(vector_b)
    if norma_a == 0 or norma_b == 0:
        return 0.0
    valor = producto_punto(vector_a, vector_b) / (norma_a * norma_b)
    return max(0.0, min(1.0, valor))


def coseno_tfidf_con_traza(tokens_a, tokens_b, idf, maximo_terminos=MAXIMO_TERMINOS_TRAZA):
    """Calcula la similitud y devuelve (similitud, pasos, detalle) con la tabla de pesos y el ángulo.

    Complejidad: O(|A| + |B| + k·log k), donde k es el número de términos de la tabla.
    """
    tf_a = frecuencia_termino(tokens_a)
    tf_b = frecuencia_termino(tokens_b)
    vector_a = vector_tfidf(tokens_a, idf)
    vector_b = vector_tfidf(tokens_b, idf)
    punto = producto_punto(vector_a, vector_b)
    norma_a = norma(vector_a)
    norma_b = norma(vector_b)
    similitud = similitud_coseno(vector_a, vector_b)
    angulo = math.degrees(math.acos(similitud))

    # Tabla: primero los términos que más aportan al producto punto.
    terminos = []
    todos = set(vector_a) | set(vector_b)
    for termino in todos:
        terminos.append({
            "termino": termino,
            "tf_a": round(tf_a.get(termino, 0.0), 6),
            "tf_b": round(tf_b.get(termino, 0.0), 6),
            "idf": round(idf.get(termino, 1.0), 6),
            "peso_a": round(vector_a.get(termino, 0.0), 6),
            "peso_b": round(vector_b.get(termino, 0.0), 6),
        })
    terminos = sorted(
        terminos,
        key=lambda fila: (-vector_a.get(fila["termino"], 0.0) * vector_b.get(fila["termino"], 0.0),
                          -(vector_a.get(fila["termino"], 0.0) + vector_b.get(fila["termino"], 0.0)),
                          fila["termino"]),
    )[:maximo_terminos]

    comunes = 0
    for termino in vector_a:
        if termino in vector_b:
            comunes += 1

    pasos = [
        f"A tiene {len(tokens_a)} tokens ({len(vector_a)} términos distintos) y B tiene {len(tokens_b)} tokens ({len(vector_b)} distintos).",
        "TF(t, d) = apariciones de t en d / total de tokens de d.",
        "IDF(t) = ln((1 + N) / (1 + df(t))) + 1, calculado sobre todos los abstracts del corpus.",
        "Peso(t, d) = TF(t, d) · IDF(t).",
    ]
    if terminos:
        fila = terminos[0]
        pasos.append(
            f"Ejemplo '{fila['termino']}': peso_A = {fila['tf_a']:.4f} · {fila['idf']:.4f} = {fila['peso_a']:.4f}; "
            f"peso_B = {fila['tf_b']:.4f} · {fila['idf']:.4f} = {fila['peso_b']:.4f}."
        )
    pasos.append(f"Términos compartidos: {comunes}; solo ellos aportan al producto punto A·B = {punto:.6f}.")
    pasos.append(f"Normas: ‖A‖ = {norma_a:.6f}, ‖B‖ = {norma_b:.6f}.")
    pasos.append(f"cos(θ) = {punto:.6f} / ({norma_a:.6f} · {norma_b:.6f}) = {similitud:.4f}.")
    pasos.append(f"Ángulo entre los vectores: θ = arccos({similitud:.4f}) = {angulo:.2f}°.")

    detalle = {
        "terminos": terminos,
        "producto_punto": punto,
        "norma_a": norma_a,
        "norma_b": norma_b,
        "angulo_grados": angulo,
    }
    return similitud, pasos, detalle
