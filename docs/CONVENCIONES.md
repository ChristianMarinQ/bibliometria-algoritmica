# Convenciones del proyecto

## Estructura (arquitectura por capas)

```
ProyectoAlgorit/
├── data/
│   ├── articulos/          # 20 PDFs originales (corpus estático)
│   ├── corpus.json         # abstracts + metadatos extraídos (generado)
│   └── embeddings.json     # vectores IA precalculados (generado)
├── backend/                # Python 3.10 + FastAPI
│   ├── app/
│   │   ├── main.py         # punto de entrada, registra las rutas
│   │   ├── config.py       # rutas de archivos y parámetros globales
│   │   ├── nucleo/         # código compartido: preprocesamiento, TF-IDF, corpus, medición
│   │   ├── corpus/         # extracción de abstracts/títulos/autores desde PDF
│   │   ├── algoritmos/     # implementaciones puras, sin FastAPI ni E/S
│   │   │   ├── similitud/
│   │   │   ├── clustering/
│   │   │   ├── busqueda/
│   │   │   └── ordenamiento/
│   │   ├── servicios/      # orquestan corpus + algoritmos + medición
│   │   └── api/            # rutas HTTP delgadas (rutas_<modulo>.py)
│   ├── scripts/            # tareas offline: extraer corpus, generar embeddings
│   └── tests/              # pytest, un archivo por módulo
├── frontend/               # React + Vite + TypeScript + D3
└── docs/                   # documento técnico, contrato de API, convenciones
```

Flujo de dependencias: `api -> servicios -> algoritmos / nucleo`. Los algoritmos
no importan nada de `api` ni `servicios`, y no leen archivos.

## Reglas de implementación

1. **Algoritmos desde cero.** Solo estructuras básicas del lenguaje: listas,
   diccionarios, bucles, aritmética. Prohibido para los algoritmos solicitados:
   `str.find`, `str.index`, `in` sobre cadenas para buscar patrones, `re`,
   `sorted()`/`list.sort()` dentro de los algoritmos de ordenamiento, `scipy`,
   `sklearn`, `numpy` para las fórmulas evaluadas. `sorted()` sí se permite en
   código auxiliar (por ejemplo ordenar el vocabulario).
2. **Trazas.** Cada algoritmo ofrece una función normal (rápida) y, cuando el
   requerimiento pide demostración paso a paso, una función `*_con_traza` que
   devuelve además los pasos intermedios en estructuras serializables a JSON.
3. **Medición.** Los tiempos se miden con `app.nucleo.medicion.medir` en milisegundos.
4. **Preprocesamiento único.** Todos usan `app.nucleo.preprocesamiento.preprocesar`
   y `app.nucleo.vectorizacion.tfidf`; no se duplican.

## Estilo de código y comentarios

- Todo en **español**: nombres de funciones, variables, comentarios y docstrings
  (`calcular_distancia`, `matriz`, `patron`, `desplazamiento`).
- Cada módulo empieza con un docstring de una a tres líneas que dice qué contiene.
- Cada función pública tiene un docstring corto: qué hace y qué devuelve.
  En los algoritmos se agrega una línea con la complejidad, p. ej. `Complejidad: O(n·m)`.
- Comentarios en línea solo para explicar *por qué* o el paso del algoritmo
  (`# Regla del carácter malo: alinear la última aparición`), no para repetir el código.
- `snake_case` para funciones y variables, `MAYUSCULAS` para constantes.
- Sin tipos complejos; los type hints son opcionales y simples.
- Frontend: componentes en `PascalCase`, comentarios en español, mismo criterio.
