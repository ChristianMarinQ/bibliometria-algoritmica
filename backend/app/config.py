"""Rutas y parámetros globales de la aplicación."""

from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
RAIZ_PROYECTO = RAIZ_BACKEND.parent

CARPETA_DATOS = RAIZ_PROYECTO / "data"
CARPETA_ARTICULOS = CARPETA_DATOS / "articulos"
RUTA_CORPUS = CARPETA_DATOS / "corpus.json"
RUTA_EMBEDDINGS = CARPETA_DATOS / "embeddings.json"
CARPETA_FRONTEND = RAIZ_PROYECTO / "frontend" / "dist"

# Orígenes permitidos para el frontend (desarrollo local y despliegue).
ORIGENES_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # `npm run preview` (compilación de producción servida por Vite)
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
