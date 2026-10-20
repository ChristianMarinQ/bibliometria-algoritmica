"""Cálculo de embeddings en el servidor para los artículos subidos.

Los modelos se cargan de forma perezosa (una sola vez, al primer artículo subido)
y solo si config.IA_EN_SERVIDOR está activo; el arranque nunca importa gensim.
"""

import logging
import threading

from app import config
from app.nucleo import modelos_ia

registro = logging.getLogger(__name__)

_modelos = {"word2vec": None, "sbert": None}
_lock_modelos = threading.Lock()


def modelo(clave):
    """Devuelve el modelo pedido ("word2vec" o "sbert"), cargándolo la primera vez."""
    with _lock_modelos:
        if _modelos[clave] is None:
            registro.info("Cargando modelo de IA '%s' en el servidor...", clave)
            if clave == "word2vec":
                # Mismo límite de palabras que scripts/generar_embeddings.py
                _modelos[clave] = modelos_ia.cargar_word2vec(modelos_ia.MODELO_WORD2VEC,
                                                             modelos_ia.LIMITE_WORD2VEC)
            else:
                _modelos[clave] = modelos_ia.cargar_sbert(modelos_ia.MODELO_SBERT)
        return _modelos[clave]


def calcular_embeddings(abstract):
    """Calcula los vectores de un abstract con ambos modelos.

    Devuelve {"word2vec": {"vector", "cobertura", "modelo", "dimensiones"} | None,
              "sbert": {"vector", "modelo", "dimensiones"} | None, "avisos": [str]}.
    Si la IA está desactivada o un modelo falla, esa clave queda en None con un aviso.
    """
    resultado = {"word2vec": None, "sbert": None, "avisos": []}
    if not config.IA_EN_SERVIDOR:
        resultado["avisos"].append("La IA no está activa en el servidor: el artículo no tendrá "
                                   "vectores Word2Vec ni SBERT.")
        return resultado
    try:
        vector, cobertura = modelos_ia.word2vec_abstract(abstract, modelo("word2vec"))
        resultado["word2vec"] = {"vector": vector, "cobertura": cobertura,
                                 "modelo": modelos_ia.MODELO_WORD2VEC, "dimensiones": len(vector)}
    except Exception as error:  # noqa: BLE001 - un fallo del modelo no debe impedir guardar
        registro.exception("Error al calcular Word2Vec")
        resultado["avisos"].append(f"No se pudo calcular Word2Vec: {error}")
    try:
        vector = modelos_ia.sbert_abstracts([abstract], modelo("sbert"))[0]
        resultado["sbert"] = {"vector": vector, "modelo": modelos_ia.MODELO_SBERT,
                              "dimensiones": len(vector)}
    except Exception as error:  # noqa: BLE001
        registro.exception("Error al calcular SBERT")
        resultado["avisos"].append(f"No se pudo calcular SBERT: {error}")
    return resultado
