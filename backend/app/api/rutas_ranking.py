"""Rutas HTTP del seguimiento: ranking de términos con ordenamientos no comparativos."""

from fastapi import APIRouter, HTTPException, Query

from app.servicios import ranking

router = APIRouter()


@router.get("/ranking")
def obtener_ranking(top: int = Query(15, ge=1, le=100)):
    """Top de términos más frecuentes según Counting, Radix y Bucket Sort."""
    try:
        return ranking.generar_ranking(top)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="No existe data/corpus.json; ejecute la extracción del corpus.")


@router.get("/ranking/benchmark")
def obtener_benchmark(repeticiones: int = Query(50, ge=1, le=500)):
    """Tiempos promedio, mínimo y máximo y escalamiento ×1, ×2, ×4, ×8."""
    try:
        return ranking.generar_benchmark(repeticiones)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="No existe data/corpus.json; ejecute la extracción del corpus.")
