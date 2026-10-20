# Imagen única: compila el frontend con Node y lo sirve junto a la API con Python.

# --- Etapa 1: compilación del frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# La API queda en el mismo dominio, por eso la ruta es relativa
ENV VITE_API_URL=/api
RUN npm run build

# --- Etapa 2: servidor FastAPI ---
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY data/corpus.json data/embeddings.json data/
COPY --from=frontend /app/frontend/dist frontend/dist
# Render asigna el puerto en la variable PORT
CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
