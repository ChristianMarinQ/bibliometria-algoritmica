"""Rutas HTTP del Req. 3: búsqueda de patrones (KMP, Boyer-Moore, Rabin-Karp)."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.servicios import busqueda

router = APIRouter()


class SolicitudBusqueda(BaseModel):
    patron: str
    ids: Optional[List[int]] = None
    distinguir_mayusculas: bool = False


class SolicitudTraza(BaseModel):
    patron: str
    algoritmo: str
    articulo_id: int
    max_caracteres: int = Field(300, ge=10, le=5000)
    distinguir_mayusculas: bool = False


def _validar_patron(patron):
    """Responde 400 si el patrón está vacío o supera la longitud máxima."""
    if len(patron.strip()) == 0:
        raise HTTPException(status_code=400, detail="El patrón no puede estar vacío")
    if len(patron) > busqueda.LONGITUD_MAXIMA_PATRON:
        raise HTTPException(
            status_code=400,
            detail=f"El patrón no puede superar {busqueda.LONGITUD_MAXIMA_PATRON} caracteres",
        )


def _corpus_no_disponible():
    """Error cuando aún no se ha generado data/corpus.json."""
    return HTTPException(status_code=503, detail="El corpus no está disponible (falta data/corpus.json)")


@router.post("/busqueda")
def buscar(solicitud: SolicitudBusqueda):
    """Busca el patrón en los abstracts con los tres algoritmos y compara sus tiempos."""
    _validar_patron(solicitud.patron)
    if solicitud.ids is not None and len(solicitud.ids) == 0:
        raise HTTPException(status_code=400, detail="La lista de ids no puede estar vacía")
    try:
        return busqueda.buscar_patron(solicitud.patron, solicitud.ids, solicitud.distinguir_mayusculas)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error.args[0]))
    except FileNotFoundError:
        raise _corpus_no_disponible()


@router.post("/busqueda/traza")
def traza(solicitud: SolicitudTraza):
    """Devuelve la traza paso a paso de un algoritmo sobre un fragmento del abstract."""
    _validar_patron(solicitud.patron)
    if solicitud.algoritmo not in busqueda.ALGORITMOS:
        raise HTTPException(status_code=400, detail=f"Algoritmo desconocido: {solicitud.algoritmo}")
    try:
        return busqueda.traza_busqueda(
            solicitud.patron,
            solicitud.algoritmo,
            solicitud.articulo_id,
            solicitud.max_caracteres,
            solicitud.distinguir_mayusculas,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error.args[0]))
    except FileNotFoundError:
        raise _corpus_no_disponible()
