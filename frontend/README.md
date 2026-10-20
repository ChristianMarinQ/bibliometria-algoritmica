# Frontend — Bibliometría algorítmica

Interfaz React + Vite + TypeScript para el proyecto de Análisis de Algoritmos (Universidad del Quindío).
Consume la API FastAPI descrita en `../docs/CONTRATO_API.md`.

## Cómo correrlo

```bash
cd frontend
npm install

npm run dev:mocks   # sin backend: corpus real + cálculos simulados en el navegador
npm run dev         # contra la API real (por defecto http://localhost:8000/api)
npm run build       # verificación de tipos (tsc) + compilación de producción en dist/
npm run preview     # sirve la compilación de dist/ en http://localhost:4173
npm run mocks:sync  # copia data/corpus.json a src/api/mocks/corpus.json
```

Para usar la API real, primero levante el backend:

```bash
cd backend
python -m uvicorn app.main:app --port 8000
```

El servidor de desarrollo usa siempre el puerto **5173** y `vite preview` el **4173**
(`strictPort`), porque el backend solo habilita CORS para esos orígenes
(`ORIGENES_CORS` en `backend/app/config.py`).

## Variables de entorno

Copie `.env.example` a `.env` (o `.env.local`) y ajuste:

| Variable          | Por defecto                  | Uso                                                  |
| ----------------- | ---------------------------- | ---------------------------------------------------- |
| `VITE_API_URL`    | `http://localhost:8000/api`  | URL base de la API (incluye el prefijo `/api`).      |
| `VITE_USAR_MOCKS` | `false`                      | `true` responde con los mocks de `src/api/mocks`.    |

`npm run dev:mocks` carga `.env.mocks`, que ya define `VITE_USAR_MOCKS=true`. La barra lateral
indica la fuente («Cálculos simulados» o «API en vivo»).

Los mocks usan los **datos reales** del corpus (títulos, autores, revistas, años y abstracts),
copiados de `data/corpus.json` a `src/api/mocks/corpus.json` con `npm run mocks:sync`; repita el
comando si se regenera el corpus. Lo que sí es simulado son los **cálculos** (similitud, embeddings,
clustering, búsqueda, ordenamiento): se reimplementan en TypeScript de forma simplificada solo para
desarrollar la interfaz sin backend. Los resultados oficiales son los de la API en Python.

## Despliegue

1. Defina la URL pública de la API **antes** de compilar (Vite la incrusta en el paquete):

   ```bash
   # Linux/macOS
   VITE_API_URL=https://mi-servidor/api npm run build
   # Windows PowerShell
   $env:VITE_API_URL="https://mi-servidor/api"; npm run build
   ```

   (o escríbala en `.env.production`).
2. Publique el contenido de `dist/` en cualquier hosting estático (Netlify, Vercel, GitHub Pages,
   Nginx…). Es una SPA con rutas del lado del cliente (`/similitud`, `/busqueda`…): configure el
   servidor para que toda ruta desconocida devuelva `index.html` (p. ej. `try_files $uri /index.html;`
   en Nginx o una regla `/* /index.html 200` en Netlify).
3. Agregue el dominio del frontend a `ORIGENES_CORS` en `backend/app/config.py`.

Para probar la compilación localmente: `npm run build && npm run preview` (con el backend en el
puerto 8000).

## Estructura

```
src/
├── api/             cliente HTTP, tipos del contrato, funciones `api.*` y mocks
├── componentes/
│   ├── ui/          primitivas: Boton, Tarjeta, Selector, Tabla, Pestanas, Icono, Estado, Dato, Tooltip, LimiteError
│   └── graficos/    MapaCalor, Dendrograma, BarrasHorizontales, MatrizDP, GraficoLineas, DiagramaConjuntos
├── hooks/           usePeticion (+ useEjecucion), useTema, useReproductor, useMedida
├── vistas/          Corpus, Similitud (+ PasoSimilitud), Clustering, Busqueda (+ VisualizadorTraza), Ranking
└── estilos/         tokens.css (diseño), base.css, componentes.css, vistas.css
scripts/
└── sincronizar-mocks.mjs   genera src/api/mocks/corpus.json desde ../data/corpus.json
```
