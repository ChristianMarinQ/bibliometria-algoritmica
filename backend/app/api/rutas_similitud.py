"""Rutas HTTP del Req. 1 (similitud textual entre abstracts)."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.servicios import similitud as servicio

router = APIRouter()


class SolicitudSimilitud(BaseModel):
    """Entrada de POST /similitud."""
    ids: List[int]
    algoritmos: Optional[List[str]] = None


class SolicitudTraza(BaseModel):
    """Entrada de POST /similitud/traza."""
    id_a: int
    id_b: int
    algoritmo: str


def ejecutar(funcion, *args):
    """Traduce las excepciones del servicio a códigos HTTP del contrato."""
    try:
        return funcion(*args)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error.args[0]) if error.args else "No encontrado")
    except servicio.EmbeddingsNoDisponibles as error:
        raise HTTPException(status_code=503, detail=str(error))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Corpus no generado; ejecute el script de extracción del corpus")


@router.post("/similitud")
def similitud(solicitud: SolicitudSimilitud):
    """Matriz de similitud entre 2 o más artículos para cada algoritmo pedido."""
    return ejecutar(servicio.calcular_similitudes, solicitud.ids, solicitud.algoritmos)


@router.post("/similitud/traza")
def traza(solicitud: SolicitudTraza):
    """Demostración paso a paso de un algoritmo entre dos artículos."""
    return ejecutar(servicio.calcular_traza, solicitud.id_a, solicitud.id_b, solicitud.algoritmo)
