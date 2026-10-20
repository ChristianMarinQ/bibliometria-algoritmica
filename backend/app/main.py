"""Punto de entrada de la API (FastAPI).

Ejecutar en desarrollo desde la carpeta backend:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import rutas_busqueda, rutas_clustering, rutas_corpus, rutas_ranking, rutas_similitud
from app.config import CARPETA_FRONTEND, ORIGENES_CORS

app = FastAPI(
    title="Análisis de Algoritmos en Bibliometría",
    description="Similitud textual, clustering jerárquico, búsqueda de patrones y ranking de términos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_CORS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cada requerimiento registra sus rutas bajo el prefijo /api.
app.include_router(rutas_corpus.router, prefix="/api", tags=["Corpus"])
app.include_router(rutas_similitud.router, prefix="/api", tags=["Req. 1 - Similitud"])
app.include_router(rutas_clustering.router, prefix="/api", tags=["Req. 2 - Clustering"])
app.include_router(rutas_busqueda.router, prefix="/api", tags=["Req. 3 - Búsqueda"])
app.include_router(rutas_ranking.router, prefix="/api", tags=["Seguimiento - Ranking"])


@app.get("/api/salud", tags=["Sistema"])
def salud():
    """Verificación simple de que el servicio está activo."""
    return {"estado": "ok"}


# En producción el mismo servicio entrega el frontend compilado (frontend/dist).
if CARPETA_FRONTEND.is_dir():

    @app.get("/{ruta:path}", include_in_schema=False)
    def frontend(ruta: str):
        """Sirve los archivos estáticos y devuelve index.html para las rutas de la SPA."""
        if ruta.startswith("api/"):
            raise HTTPException(status_code=404, detail="Ruta de API no encontrada")
        archivo = (CARPETA_FRONTEND / ruta).resolve()
        # Solo se entregan archivos que estén dentro de la carpeta del frontend
        if ruta and archivo.is_file() and CARPETA_FRONTEND.resolve() in archivo.parents:
            return FileResponse(archivo)
        return FileResponse(CARPETA_FRONTEND / "index.html")
