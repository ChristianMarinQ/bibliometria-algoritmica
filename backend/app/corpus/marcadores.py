"""Configuración estática para la extracción del corpus.

Contiene las revistas conocidas (para detectar nombre y año desde el texto) y los
marcadores por artículo cuando la heurística general no basta.
"""

# Revistas presentes en el corpus. Cada entrada indica:
# - "patron": expresión que identifica la revista en el texto de la página 1.
# - "nombre": nombre normalizado que se guarda en corpus.json.
# - "patron_anio": expresión con un grupo que captura el año de publicación.
REVISTAS = [
    {
        "patron": r"Computers and Education: Artificial Intelligence",
        "nombre": "Computers and Education: Artificial Intelligence",
        "patron_anio": r"Computers and Education: Artificial Intelligence \d+ \((\d{4})\)",
    },
    {
        "patron": r"Int(?:ernational)? J(?:ournal of)? Educ(?:ational)? Technol(?:ogy in)? High(?:er)? Educ",
        "nombre": "International Journal of Educational Technology in Higher Education",
        "patron_anio": r"\((\d{4})\)\s*\d+:\d+",
    },
    {
        "patron": r"Journal for STEM Education Research",
        "nombre": "Journal for STEM Education Research",
        "patron_anio": r"Journal for STEM Education Research \((\d{4})\)",
    },
    {
        # Emerald codifica el "+" del nombre como "þ" en la fuente del PDF.
        "patron": r"Education [þ+] Training",
        "nombre": "Education + Training",
        "patron_anio": r"Vol\. \d+ No\. \d+, (\d{4})",
    },
    {
        "patron": r"European Journal of Education",
        "nombre": "European Journal of Education",
        "patron_anio": r"Eur J Educ\. (\d{4});",
    },
    {
        "patron": r"Educ\. Sci\.",
        "nombre": "Education Sciences",
        "patron_anio": r"Educ\. Sci\.\s+(\d{4}),",
    },
    {
        "patron": r"Sustainability \d{4},",
        "nombre": "Sustainability",
        "patron_anio": r"Sustainability (\d{4}),",
    },
]

# Marcadores de inicio y fin del abstract que reemplazan a los generales.
# "inicio": texto tras el cual empieza el abstract (se busca después del marcador
#           general "A B S T R A C T"/"Abstract").
# "fin": texto donde termina el abstract (no se incluye).
MARCADORES_ARTICULO = {
    # Art. 7 (Elsevier): "A B S T R A C T" aparece antes del bloque de keywords,
    # así que el abstract empieza después de la última palabra clave.
    7: {"inicio": "Ethical considerations"},
    # Art. 9 (Elsevier): no tiene "1. Introduction"; la introducción empieza
    # directamente con esta frase.
    9: {"fin": "Since Alan Turing"},
}

# Correcciones manuales de metadatos (vacío: todo se obtiene del texto).
CORRECCIONES = {}
