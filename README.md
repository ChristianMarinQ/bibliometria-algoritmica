# Bibliometría algorítmica

Proyecto final de Análisis de Algoritmos (Universidad del Quindío, 2026-2): análisis
computacional de 20 abstracts sobre IA en educación.

| Requerimiento | Algoritmos |
|---|---|
| 1. Similitud textual | Levenshtein, Needleman-Wunsch, coseno TF-IDF, Jaccard, Word2Vec, SBERT |
| 2. Clustering jerárquico | Single, Complete y Average Linkage + correlación cofenética y Silhouette |
| 3. Búsqueda de patrones | KMP, Boyer-Moore, Rabin-Karp |
| Seguimiento | Ranking de términos con Counting, Radix y Bucket Sort |

Todos los algoritmos están implementados desde cero (ver `docs/CONVENCIONES.md`).

## Estructura

- `backend/` — API en Python 3.10 + FastAPI (`api → servicios → algoritmos / nucleo`)
- `frontend/` — React + Vite + TypeScript + D3
- `data/` — `corpus.json` (abstracts extraídos) y `embeddings.json` (vectores precalculados)
- `docs/` — contrato de la API, convenciones y resultados de benchmarks

## Ejecutar en local

```bash
pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Abrir http://localhost:5173. Pruebas del backend: `cd backend && python -m pytest`.

## Regenerar datos (opcional)

Los PDFs originales no se versionan. Con los PDFs en `data/articulos/`:

```bash
python backend/scripts/extraer_corpus.py
pip install -r backend/requirements-ia.txt
python backend/scripts/generar_embeddings.py
```

## Despliegue

El `Dockerfile` compila el frontend y lo sirve junto con la API en un solo servicio.
En Render: New → Blueprint → seleccionar este repositorio (usa `render.yaml`).
