"""Rutas HTTP del módulo de corpus: listado y detalle de artículos."""

from fastapi import APIRouter, HTTPException

from app.nucleo.corpus import cargar_corpus, obtener_articulo

router = APIRouter()

CORPUS_NO_DISPONIBLE = "No existe data/corpus.json; ejecute la extracción del corpus."


def resumir_articulo(articulo):
    """Devuelve los metadatos del artículo con el conteo de palabras del abstract."""
    return {
        "id": articulo["id"],
        "titulo": articulo["titulo"],
        "autores": articulo["autores"],
        "anio": articulo["anio"],
        "revista": articulo["revista"],
        "archivo": articulo["archivo"],
        # Palabras separadas por espacios, según el contrato de la API.
        "palabras_abstract": len(articulo["abstract"].split()),
        "origen": articulo.get("origen", "base"),
    }


@router.get("/articulos")
def listar_articulos():
    """Lista todos los artículos del corpus (sin el abstract completo)."""
    try:
        return [resumir_articulo(articulo) for articulo in cargar_corpus()]
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=CORPUS_NO_DISPONIBLE)


@router.get("/articulos/{id_articulo}")
def detalle_articulo(id_articulo: int):
    """Devuelve un artículo con su abstract completo. 404 si no existe."""
    try:
        articulo = obtener_articulo(id_articulo)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=CORPUS_NO_DISPONIBLE)
    if articulo is None:
        raise HTTPException(status_code=404, detail=f"No existe el artículo con id {id_articulo}")
    detalle = resumir_articulo(articulo)
    detalle["abstract"] = articulo["abstract"]
    return detalle
