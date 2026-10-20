"""Rutas HTTP del Req. 2: clustering jerárquico de los abstracts."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.servicios.clustering import DatosNoDisponibles, ejecutar_clustering

router = APIRouter()


@router.get("/clustering")
def obtener_clustering(
    representacion: Literal["tfidf", "sbert"] = Query("tfidf"),
    k: int = Query(4, ge=2, le=10),
):
    """Ejecuta single, complete y average linkage y devuelve árboles, fusiones y métricas."""
    try:
        return ejecutar_clustering(representacion, k)
    except DatosNoDisponibles as error:
        raise HTTPException(status_code=503, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
