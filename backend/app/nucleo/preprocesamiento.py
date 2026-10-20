"""Preprocesamiento de texto compartido por todos los requerimientos.

Todo se implementa con estructuras básicas (cadenas, listas, diccionarios)
para que el comportamiento sea transparente y analizable.
"""

# Palabras vacías del inglés (los abstracts del corpus están en inglés).
STOPWORDS = {
    "a", "about", "above", "across", "after", "again", "against", "all", "almost",
    "also", "although", "always", "am", "among", "an", "and", "another", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "during", "each", "either", "else", "etc", "even", "ever", "every",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "however", "i",
    "ie", "if", "in", "into", "is", "it", "its", "itself", "just", "may", "me",
    "might", "more", "most", "much", "must", "my", "myself", "neither", "no",
    "nor", "not", "now", "of", "off", "often", "on", "once", "one", "only", "or",
    "other", "others", "our", "ours", "ourselves", "out", "over", "own", "per",
    "rather", "same", "several", "shall", "she", "should", "since", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "though", "through",
    "thus", "to", "too", "toward", "towards", "under", "until", "up", "upon",
    "us", "very", "via", "was", "we", "well", "were", "what", "when", "where",
    "whereas", "whether", "which", "while", "who", "whom", "whose", "why",
    "will", "with", "within", "without", "would", "yet", "you", "your", "yours",
    "eg", "et", "al", "two", "three", "four", "five", "six", "first", "second",
    "third", "new", "used", "using", "use", "based",
}

# Ligaduras tipográficas frecuentes en PDFs que deben normalizarse.
LIGADURAS = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "­": "",
}

LONGITUD_MINIMA = 3


def normalizar(texto):
    """Reemplaza ligaduras y comillas tipográficas y pasa a minúsculas."""
    resultado = []
    for caracter in texto:
        resultado.append(LIGADURAS.get(caracter, caracter))
    return "".join(resultado).lower()


def tokenizar(texto):
    """Divide el texto en palabras formadas solo por letras a-z.

    Recorre el texto carácter por carácter; cualquier símbolo que no sea
    letra actúa como separador, por lo que "problem-solving" produce
    los tokens "problem" y "solving".
    """
    tokens = []
    actual = []
    for caracter in normalizar(texto):
        if "a" <= caracter <= "z":
            actual.append(caracter)
        else:
            if actual:
                tokens.append("".join(actual))
                actual = []
    if actual:
        tokens.append("".join(actual))
    return tokens


def limpiar_tokens(tokens):
    """Elimina palabras vacías y palabras muy cortas."""
    limpios = []
    for token in tokens:
        if len(token) >= LONGITUD_MINIMA and token not in STOPWORDS:
            limpios.append(token)
    return limpios


def preprocesar(texto):
    """Pipeline completo: normalizar -> tokenizar -> limpiar."""
    return limpiar_tokens(tokenizar(texto))


def frecuencias(tokens):
    """Cuenta cuántas veces aparece cada token. Devuelve un diccionario."""
    conteo = {}
    for token in tokens:
        conteo[token] = conteo.get(token, 0) + 1
    return conteo
