"""Similitud entre vectores densos de modelos de IA (Word2Vec, Sentence-BERT).

Los vectores vienen precalculados (scripts/generar_embeddings.py); aquí solo se
implementan a mano el producto punto, la norma, el coseno y la distancia euclidiana.
"""

import math

COMPONENTES_TRAZA = 16


def producto_punto(a, b):
    """Suma de a_i · b_i entre dos listas de igual longitud.

    Complejidad: O(d), con d las dimensiones.
    """
    total = 0.0
    for i in range(len(a)):
        total += a[i] * b[i]
    return total


def norma(a):
    """Norma euclidiana ‖a‖ = raíz de la suma de cuadrados.

    Complejidad: O(d).
    """
    total = 0.0
    for valor in a:
        total += valor * valor
    return math.sqrt(total)


def coseno(a, b):
    """cos(θ) = (a·b) / (‖a‖·‖b‖) en [-1, 1]; 0 si algún vector es nulo.

    Complejidad: O(d).
    """
    norma_a = norma(a)
    norma_b = norma(b)
    if norma_a == 0 or norma_b == 0:
        return 0.0
    valor = producto_punto(a, b) / (norma_a * norma_b)
    return max(-1.0, min(1.0, valor))


def distancia_euclidiana(a, b):
    """‖a - b‖ = raíz de la suma de (a_i - b_i)².

    Complejidad: O(d).
    """
    total = 0.0
    for i in range(len(a)):
        diferencia = a[i] - b[i]
        total += diferencia * diferencia
    return math.sqrt(total)


def similitud_embeddings(a, b):
    """Similitud en [0, 1]: el coseno, truncando a 0 los valores negativos.

    Un coseno negativo (vectores opuestos) se interpreta como ausencia de similitud.
    Complejidad: O(d).
    """
    return max(0.0, coseno(a, b))


def embeddings_con_traza(a, b, modelo, cobertura_a=None, cobertura_b=None):
    """Calcula la similitud y devuelve (similitud, pasos, detalle) con coseno y distancia euclidiana.

    Complejidad: O(d).
    """
    punto = producto_punto(a, b)
    norma_a = norma(a)
    norma_b = norma(b)
    cos = coseno(a, b)
    euclidiana = distancia_euclidiana(a, b)
    similitud = max(0.0, cos)
    angulo = math.degrees(math.acos(cos))

    pasos = [
        f"Cada abstract se representa con un vector de {len(a)} dimensiones del modelo '{modelo}'.",
    ]
    if cobertura_a is not None:
        pasos.append(
            "Word2Vec: el vector del documento es el promedio de los vectores de sus palabras preprocesadas "
            f"presentes en el modelo (cobertura A = {cobertura_a:.1%}, B = {cobertura_b:.1%})."
        )
    else:
        pasos.append("Sentence-BERT: el modelo codifica el abstract completo en un único vector (mean pooling).")
    pasos += [
        f"Producto punto a·b = Σ a_i·b_i = {punto:.6f}.",
        f"Normas: ‖a‖ = {norma_a:.6f}, ‖b‖ = {norma_b:.6f}.",
        f"Coseno = {punto:.6f} / ({norma_a:.6f} · {norma_b:.6f}) = {cos:.4f} (ángulo {angulo:.2f}°).",
        f"Distancia euclidiana ‖a - b‖ = √Σ(a_i - b_i)² = {euclidiana:.4f}.",
        f"Similitud reportada = max(0, coseno) = {similitud:.4f}.",
    ]
    detalle = {
        "modelo": modelo,
        "dimensiones": len(a),
        "vector_a": list(a[:COMPONENTES_TRAZA]),
        "vector_b": list(b[:COMPONENTES_TRAZA]),
        "coseno": cos,
        "distancia_euclidiana": euclidiana,
        "producto_punto": punto,
        "norma_a": norma_a,
        "norma_b": norma_b,
    }
    if cobertura_a is not None:
        detalle["cobertura_a"] = cobertura_a
        detalle["cobertura_b"] = cobertura_b
    return similitud, pasos, detalle
