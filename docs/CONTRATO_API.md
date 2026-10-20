# Contrato de la API

Base: `http://localhost:8000/api`. Todas las respuestas son JSON. Los errores
usan el formato estándar de FastAPI `{"detail": "mensaje"}` con código 400/404/422.
Los tiempos siempre están en milisegundos (`float`). Las similitudes están en `[0, 1]`.

## Corpus

### `GET /articulos`
```json
[{"id": 1, "titulo": "…", "autores": ["…"], "anio": 2022, "revista": "…",
  "archivo": "1. Artificial ….pdf", "palabras_abstract": 182}]
```

### `GET /articulos/{id}`
Igual que el anterior más `"abstract": "texto completo"`.

## Req. 1 — Similitud

Claves de algoritmo: `levenshtein`, `needleman_wunsch`, `coseno_tfidf`,
`jaccard` (tipo `clasico`) y `word2vec`, `sbert` (tipo `ia`).

### `POST /similitud`
Entrada: `{"ids": [1, 5, 9], "algoritmos": ["levenshtein", "sbert"]}`
(`ids` con 2 o más elementos; `algoritmos` opcional = todos).
```json
{
  "articulos": [{"id": 1, "titulo": "…"}],
  "resultados": [
    {"clave": "levenshtein", "nombre": "Levenshtein", "tipo": "clasico",
     "matriz": [[1.0, 0.31], [0.31, 1.0]],
     "tiempo_ms": 12.4}
  ]
}
```
`matriz[i][j]` es la similitud entre `articulos[i]` y `articulos[j]` (simétrica, diagonal 1).

### `POST /similitud/traza`
Entrada: `{"id_a": 1, "id_b": 5, "algoritmo": "levenshtein"}`.
```json
{
  "clave": "levenshtein", "nombre": "Levenshtein", "tipo": "clasico",
  "similitud": 0.31,
  "formula": "sim = 1 - d / max(|A|, |B|)",
  "pasos": ["Texto: se trabaja a nivel de palabras…", "…"],
  "detalle": { }
}
```
Contenido de `detalle` según el algoritmo:

- `levenshtein`, `needleman_wunsch` (a nivel de **palabras** del texto preprocesado):
  `{"secuencia_a": ["…"], "secuencia_b": ["…"], "matriz": [[int]], "truncado": true,
    "camino": [[i, j], …], "distancia": 120, "puntaje": -40,
    "parametros": {"match": 1, "mismatch": -1, "gap": -1}}`
  La matriz se recorta a las primeras 12×12 palabras para visualizarla
  (`truncado` indica si se recortó); `distancia`/`puntaje` son del texto completo.
  `puntaje` y `parametros` solo en Needleman-Wunsch; `distancia` solo en Levenshtein.
- `coseno_tfidf`:
  `{"terminos": [{"termino": "learning", "tf_a": 0.02, "tf_b": 0.0, "idf": 1.4,
     "peso_a": 0.028, "peso_b": 0.0}], "producto_punto": 0.12, "norma_a": 0.4,
     "norma_b": 0.38, "angulo_grados": 72.3}`
  (`terminos` ordenados por `peso_a * peso_b` descendente, máximo 25).
- `jaccard`:
  `{"interseccion": ["…"], "solo_a": ["…"], "solo_b": ["…"],
    "tam_interseccion": 14, "tam_union": 120}`
- `word2vec`, `sbert`:
  `{"modelo": "all-MiniLM-L6-v2", "dimensiones": 384,
    "vector_a": [primeras 16 componentes], "vector_b": [primeras 16],
    "coseno": 0.71, "distancia_euclidiana": 0.76, "producto_punto": 0.71,
    "norma_a": 1.0, "norma_b": 1.0, "cobertura_a": 0.93, "cobertura_b": 0.9}`
  (`cobertura_*` solo en word2vec: fracción de palabras con vector en el modelo).

## Req. 2 — Clustering jerárquico

### `GET /clustering`
Parámetro opcional `?representacion=tfidf|sbert` (por defecto `tfidf`).
```json
{
  "representacion": "tfidf",
  "articulos": [{"id": 1, "titulo": "…"}],
  "metodos": [
    {"clave": "single", "nombre": "Single Linkage",
     "arbol": {"id": 38, "distancia": 0.91, "tamano": 20,
               "hijos": [{"id": 0, "articulo_id": 1, "titulo": "…", "distancia": 0, "tamano": 1}, {}]},
     "fusiones": [{"paso": 1, "a": 3, "b": 7, "nuevo": 20, "distancia": 0.42, "tamano": 2}],
     "silhouette": 0.08, "correlacion_cofenetica": 0.81,
     "tiempo_ms": 3.2}
  ],
  "mejor_metodo": "average",
  "criterio": "Mayor coeficiente de correlación cofenética; Silhouette como desempate"
}
```
Claves: `single`, `complete`, `average`. Las hojas tienen `articulo_id` y `titulo`;
los nodos internos tienen `hijos` (siempre 2). Distancia = 1 − similitud del coseno.
`silhouette` se calcula cortando el árbol en `k` grupos (`?k=4` por defecto).

## Req. 3 — Búsqueda de patrones

Claves: `kmp`, `boyer_moore`, `rabin_karp`.

### `POST /busqueda`
Entrada: `{"patron": "learning", "ids": null, "distinguir_mayusculas": false}`
(`ids` null = los 20 abstracts).
```json
{
  "patron": "learning",
  "algoritmos": [
    {"clave": "kmp", "nombre": "Knuth-Morris-Pratt",
     "tiempo_preprocesamiento_ms": 0.01, "tiempo_busqueda_ms": 0.8,
     "comparaciones": 15230, "total_coincidencias": 41}
  ],
  "coinciden": true,
  "resultados": [
    {"articulo_id": 1, "titulo": "…", "posiciones": [120, 455],
     "fragmentos": [{"posicion": 120, "antes": "…texto ", "coincidencia": "learning", "despues": " analytics…"}]}
  ]
}
```
`coinciden` indica si los tres algoritmos hallaron exactamente las mismas posiciones.
`resultados` solo incluye artículos con al menos una coincidencia.

### `POST /busqueda/traza`
Entrada: `{"patron": "learning", "algoritmo": "boyer_moore", "articulo_id": 1, "max_caracteres": 300}`
(se toma el primer párrafo del abstract recortado a `max_caracteres`).
```json
{
  "clave": "boyer_moore", "nombre": "Boyer-Moore",
  "texto": "…", "patron": "learning",
  "preprocesamiento": { },
  "pasos": [
    {"alineacion": 0, "comparaciones": [{"i": 7, "j": 7, "igual": false}],
     "coincidencia": false, "desplazamiento": 3,
     "motivo": "Carácter malo 'x': …", "hash_ventana": null}
  ],
  "posiciones": [120], "total_comparaciones": 98
}
```
`alineacion` = índice del texto donde empieza la ventana; en `comparaciones`,
`i` es índice del texto y `j` del patrón. Contenido de `preprocesamiento`:

- `kmp`: `{"lps": [0,0,1,…], "pasos_lps": ["…"]}`
- `boyer_moore`: `{"caracter_malo": {"l": 0, "e": 1, …}, "sufijo_bueno": [int, …], "pasos": ["…"]}`
- `rabin_karp`: `{"base": 256, "modulo": 101, "h": 52, "hash_patron": 17, "pasos": ["…"]}`
  y en cada paso `hash_ventana` con el valor, más `"colision": true` cuando el
  hash coincide pero los caracteres no.

## Seguimiento — Ranking de términos

### `GET /ranking?top=15`
```json
{
  "total_tokens": 3500, "terminos_distintos": 1200, "frecuencia_maxima": 85,
  "algoritmos": [
    {"clave": "counting_sort", "nombre": "Counting Sort", "tiempo_ms": 0.4,
     "complejidad": "O(n + k)", "top": [{"termino": "learning", "frecuencia": 85}]}
  ],
  "coinciden": true
}
```
Claves: `counting_sort`, `radix_sort`, `bucket_sort`. Orden: frecuencia descendente,
empates por término alfabético ascendente (orden estable).

### `GET /ranking/benchmark?repeticiones=50`
```json
{"n": 1200, "repeticiones": 50,
 "algoritmos": [{"clave": "counting_sort", "promedio_ms": 0.4, "minimo_ms": 0.3, "maximo_ms": 0.9}],
 "escalamiento": [{"n": 1200, "counting_sort": 0.4, "radix_sort": 0.7, "bucket_sort": 0.6}]}
```
`escalamiento` repite la medición duplicando la lista (×1, ×2, ×4, ×8) para
mostrar el crecimiento lineal.

## Subida de artículos (corpus dinámico)

El corpus = 20 artículos **base** (`data/corpus.json`, solo lectura) + artículos **subidos**
(guardados en `CARPETA_SUBIDOS`, por defecto `data/subidos/`, montada como volumen Docker).
Los ids de subidos empiezan en 21. Todas las vistas usan el corpus combinado.

### `GET /sistema`
```json
{"subida_habilitada": true, "requiere_clave": true, "ia_en_servidor": true,
 "total_articulos": 21, "articulos_base": 20, "tamano_maximo_mb": 15}
```
`subida_habilitada=false` (p. ej. en Render) → el frontend oculta la subida.
`ia_en_servidor=false` → los artículos subidos no tienen vectores IA (se avisa).

### `POST /articulos/extraer` (multipart, campo `archivo`: PDF)
Extrae sin guardar, para que el usuario revise:
```json
{"archivo": "mi-articulo.pdf", "titulo": "…", "autores": ["…"], "anio": 2024,
 "revista": "…", "abstract": "…", "palabras_abstract": 180, "advertencias": ["No se encontró el año"]}
```
Errores: 400 no es PDF / PDF ilegible / sin texto; 413 > tamaño máximo; 403 subida deshabilitada o clave inválida.

### `POST /articulos`
Entrada: `{"titulo", "autores": [str], "anio": int|null, "revista", "abstract", "archivo"}`
(lo revisado/corregido por el usuario). Respuesta 201: el artículo completo con
`"id"` asignado y `"origen": "subido"`, más `"embeddings": {"word2vec": bool, "sbert": bool}`.
Validación 422: título vacío, abstract con menos de 30 palabras o más de 1000.
409 si ya existe un artículo con el mismo título (comparación sin mayúsculas ni espacios extra).

### `DELETE /articulos/{id}`
Solo artículos subidos (403 para los 20 base). 204 sin cuerpo.

### Autorización
Si la variable de entorno `CLAVE_SUBIDA` está definida, `POST /articulos/extraer`,
`POST /articulos` y `DELETE /articulos/{id}` exigen la cabecera `X-Clave-Subida`
con ese valor (403 si falta o no coincide).

### Cambios en respuestas existentes
- `GET /articulos` y `GET /articulos/{id}` agregan `"origen": "base" | "subido"`.
- Similitud/clustering con artículos sin vectores IA: los algoritmos IA se omiten con
  un aviso en `avisos` (similitud) o 503 claro (clustering `representacion=sbert`).

## Campos adicionales (opcionales)

El backend agrega estos campos, que el cliente puede ignorar:

- `POST /similitud`: `avisos: [str]` cuando se piden todos los algoritmos y faltan
  los embeddings (los de IA se omiten en vez de fallar).
- `POST /similitud/traza` (`needleman_wunsch`): `detalle.alineamiento = {"a": [...], "b": [...]}`
  con huecos `"-"`.
- `POST /busqueda/traza`: entrada opcional `distinguir_mayusculas` (por defecto `false`);
  salida `articulo_id` e `inicio_texto` (índice del abstract donde empieza `texto`,
  que se centra en la primera ocurrencia si queda fuera de los primeros `max_caracteres`).
  Boyer-Moore añade `preprocesamiento.bordes`; Rabin-Karp añade `total_colisiones`
  y en cada paso `calculo_hash` (texto del cálculo del hash rodante) y `colision`.
- Si falta `data/corpus.json` o `data/embeddings.json` la API responde 503.
