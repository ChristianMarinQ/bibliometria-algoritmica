"""Rutas HTTP de la subida de artículos (corpus dinámico) y del estado del sistema."""

from typing import List, Optional

from fastapi import APIRouter, File, Header, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app import config
from app.servicios import subida

router = APIRouter()


class SolicitudArticulo(BaseModel):
    """Entrada de POST /articulos: datos revisados por el usuario."""
    titulo: str = ""
    autores: List[str] = []
    anio: Optional[int] = None
    revista: str = ""
    abstract: str = ""
    archivo: str = ""


def ejecutar(funcion, *args):
    """Traduce ErrorSubida a HTTPException con su código."""
    try:
        return funcion(*args)
    except subida.ErrorSubida as error:
        raise HTTPException(status_code=error.codigo, detail=str(error))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="No existe data/corpus.json; ejecute la extracción del corpus.")


@router.get("/sistema")
def sistema():
    """Capacidades del servidor: subida habilitada, clave requerida, IA y totales."""
    return subida.estado_sistema()


@router.post("/articulos/extraer")
async def extraer(archivo: UploadFile = File(...), x_clave_subida: Optional[str] = Header(None)):
    """Extrae título, autores, año, revista y abstract de un PDF sin guardarlo."""
    ejecutar(subida.verificar_permiso, x_clave_subida)
    # Se lee un byte más del máximo para detectar archivos demasiado grandes sin cargarlos completos.
    limite = config.TAMANO_MAXIMO_MB * 1024 * 1024
    contenido = await archivo.read(limite + 1)
    return ejecutar(subida.extraer_pdf, archivo.filename, contenido)


@router.post("/articulos", status_code=201)
def crear(solicitud: SolicitudArticulo, x_clave_subida: Optional[str] = Header(None)):
    """Guarda el artículo revisado en el corpus y calcula sus embeddings."""
    ejecutar(subida.verificar_permiso, x_clave_subida)
    return ejecutar(subida.guardar_articulo, solicitud.model_dump())


@router.delete("/articulos/{id_articulo}", status_code=204)
def borrar(id_articulo: int, x_clave_subida: Optional[str] = Header(None)):
    """Borra un artículo subido (403 para los artículos base)."""
    ejecutar(subida.verificar_permiso, x_clave_subida)
    ejecutar(subida.borrar_articulo, id_articulo)
    return Response(status_code=204)
