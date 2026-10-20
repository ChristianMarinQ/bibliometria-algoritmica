"""Rutas y parámetros globales de la aplicación."""

import os
from importlib.util import find_spec
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
RAIZ_PROYECTO = RAIZ_BACKEND.parent

CARPETA_DATOS = RAIZ_PROYECTO / "data"
CARPETA_ARTICULOS = CARPETA_DATOS / "articulos"
RUTA_CORPUS = CARPETA_DATOS / "corpus.json"
RUTA_EMBEDDINGS = CARPETA_DATOS / "embeddings.json"
CARPETA_FRONTEND = RAIZ_PROYECTO / "frontend" / "dist"


def leer_booleano(nombre, por_defecto):
    """Lee una variable de entorno como booleano ("1", "true", "si"...). Devuelve el valor por defecto si no existe."""
    valor = os.environ.get(nombre)
    if valor is None or not valor.strip():
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


def carpeta_escribible(carpeta):
    """Indica si se puede escribir en la carpeta o, si no existe, en su ancestro existente más cercano."""
    actual = Path(carpeta)
    while not actual.exists() and actual.parent != actual:
        actual = actual.parent
    return os.access(actual, os.W_OK)


# ---------- Subida de artículos (corpus dinámico) ----------
# Carpeta persistente de los artículos subidos (volumen Docker en la VM).
CARPETA_SUBIDOS = Path(os.environ.get("CARPETA_SUBIDOS") or (CARPETA_DATOS / "subidos"))
# En Render (sin disco persistente) se define SUBIDA_HABILITADA=false.
SUBIDA_HABILITADA = leer_booleano("SUBIDA_HABILITADA", carpeta_escribible(CARPETA_SUBIDOS))
# Si está definida, subir y borrar exigen la cabecera X-Clave-Subida.
CLAVE_SUBIDA = os.environ.get("CLAVE_SUBIDA") or None
# Calcular embeddings en el servidor solo si las librerías de IA están instaladas
# (find_spec no importa el módulo, así el arranque sigue siendo liviano).
IA_EN_SERVIDOR = leer_booleano(
    "IA_EN_SERVIDOR", find_spec("gensim") is not None and find_spec("sentence_transformers") is not None
)
TAMANO_MAXIMO_MB = 15

# Orígenes permitidos para el frontend (desarrollo local y despliegue).
ORIGENES_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # `npm run preview` (compilación de producción servida por Vite)
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
