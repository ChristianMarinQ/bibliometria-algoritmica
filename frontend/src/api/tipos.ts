// Tipos de la API según docs/CONTRATO_API.md (fuente de verdad).
// Tiempos en milisegundos; similitudes en [0, 1].

// ---------- Corpus ----------
export interface Articulo {
  id: number;
  titulo: string;
  autores: string[];
  anio: number | null;
  revista: string;
  archivo: string;
  palabras_abstract: number;
  /** "base" para los 20 originales, "subido" para los agregados por el usuario. */
  origen?: OrigenArticulo;
}

export type OrigenArticulo = "base" | "subido";

// ---------- Sistema y subida de artículos ----------
export interface InfoSistema {
  subida_habilitada: boolean;
  requiere_clave: boolean;
  ia_en_servidor: boolean;
  total_articulos: number;
  articulos_base: number;
  tamano_maximo_mb: number;
}

/** Resultado de POST /articulos/extraer: lo extraído del PDF, para revisar antes de guardar. */
export interface ArticuloExtraido {
  archivo: string;
  titulo: string;
  autores: string[];
  anio: number | null;
  revista: string;
  abstract: string;
  palabras_abstract: number;
  advertencias: string[];
}

export interface ArticuloNuevo {
  titulo: string;
  autores: string[];
  anio: number | null;
  revista: string;
  abstract: string;
  archivo: string;
}

export interface ArticuloGuardado extends ArticuloDetalle {
  embeddings?: { word2vec: boolean; sbert: boolean };
}

export interface ArticuloDetalle extends Articulo {
  abstract: string;
}

export interface ArticuloRef {
  id: number;
  titulo: string;
}

// ---------- Req. 1: Similitud ----------
export type ClaveSimilitud =
  | "levenshtein"
  | "needleman_wunsch"
  | "coseno_tfidf"
  | "jaccard"
  | "word2vec"
  | "sbert";

export type TipoAlgoritmo = "clasico" | "ia";

export interface ResultadoSimilitud {
  clave: ClaveSimilitud;
  nombre: string;
  tipo: TipoAlgoritmo;
  matriz: number[][];
  tiempo_ms: number;
}

export interface RespuestaSimilitud {
  articulos: ArticuloRef[];
  resultados: ResultadoSimilitud[];
  /** Avisos del backend (p. ej. embeddings no disponibles: se omiten los IA). */
  avisos?: string[];
}

// Las secuencias y el camino son COMPLETOS; solo `matriz` viene recortada a 13×13
// (filas/columnas 0..12, con la fila/columna 0 de la cadena vacía).
export interface DetalleEdicion {
  secuencia_a: string[];
  secuencia_b: string[];
  matriz: number[][];
  truncado: boolean;
  camino: [number, number][];
  /** Solo Needleman-Wunsch: alineamiento con huecos "-". */
  alineamiento?: { a: string[]; b: string[] };
  distancia?: number;
  puntaje?: number;
  parametros?: { match: number; mismatch: number; gap: number };
}

export interface TerminoTfidf {
  termino: string;
  tf_a: number;
  tf_b: number;
  idf: number;
  peso_a: number;
  peso_b: number;
}

export interface DetalleCoseno {
  terminos: TerminoTfidf[];
  producto_punto: number;
  norma_a: number;
  norma_b: number;
  angulo_grados: number;
}

export interface DetalleJaccard {
  interseccion: string[];
  solo_a: string[];
  solo_b: string[];
  tam_interseccion: number;
  tam_union: number;
}

export interface DetalleEmbedding {
  modelo: string;
  dimensiones: number;
  vector_a: number[];
  vector_b: number[];
  coseno: number;
  distancia_euclidiana: number;
  producto_punto: number;
  norma_a: number;
  norma_b: number;
  cobertura_a?: number;
  cobertura_b?: number;
}

interface TrazaBase {
  nombre: string;
  tipo: TipoAlgoritmo;
  similitud: number;
  formula: string;
  pasos: string[];
}

// Unión discriminada por `clave` para que cada panel conozca su `detalle`.
export type TrazaSimilitud =
  | (TrazaBase & { clave: "levenshtein" | "needleman_wunsch"; detalle: DetalleEdicion })
  | (TrazaBase & { clave: "coseno_tfidf"; detalle: DetalleCoseno })
  | (TrazaBase & { clave: "jaccard"; detalle: DetalleJaccard })
  | (TrazaBase & { clave: "word2vec" | "sbert"; detalle: DetalleEmbedding });

// ---------- Req. 2: Clustering ----------
export type Representacion = "tfidf" | "sbert";
export type ClaveEnlace = "single" | "complete" | "average";

export interface NodoArbol {
  id: number;
  distancia: number;
  tamano: number;
  articulo_id?: number;
  titulo?: string;
  hijos?: NodoArbol[];
}

export interface Fusion {
  paso: number;
  a: number;
  b: number;
  nuevo: number;
  distancia: number;
  tamano: number;
}

export interface MetodoClustering {
  clave: ClaveEnlace;
  nombre: string;
  arbol: NodoArbol;
  fusiones: Fusion[];
  silhouette: number;
  correlacion_cofenetica: number;
  tiempo_ms: number;
}

export interface RespuestaClustering {
  representacion: Representacion;
  articulos: ArticuloRef[];
  metodos: MetodoClustering[];
  mejor_metodo: ClaveEnlace;
  criterio: string;
}

// ---------- Req. 3: Búsqueda de patrones ----------
export type ClaveBusqueda = "kmp" | "boyer_moore" | "rabin_karp";

export interface MetricaBusqueda {
  clave: ClaveBusqueda;
  nombre: string;
  tiempo_preprocesamiento_ms: number;
  tiempo_busqueda_ms: number;
  comparaciones: number;
  total_coincidencias: number;
}

export interface Fragmento {
  posicion: number;
  antes: string;
  coincidencia: string;
  despues: string;
}

export interface ResultadoBusqueda {
  articulo_id: number;
  titulo: string;
  posiciones: number[];
  fragmentos: Fragmento[];
}

export interface RespuestaBusqueda {
  patron: string;
  algoritmos: MetricaBusqueda[];
  coinciden: boolean;
  resultados: ResultadoBusqueda[];
}

export interface PeticionBusqueda {
  patron: string;
  ids: number[] | null;
  distinguir_mayusculas: boolean;
}

export interface PeticionTrazaBusqueda {
  patron: string;
  algoritmo: ClaveBusqueda;
  articulo_id: number;
  max_caracteres?: number;
  distinguir_mayusculas?: boolean;
}

export interface Comparacion {
  i: number;
  j: number;
  igual: boolean;
}

export interface PasoBusqueda {
  alineacion: number;
  comparaciones: Comparacion[];
  coincidencia: boolean;
  desplazamiento: number;
  motivo: string;
  hash_ventana: number | null;
  /** Solo Rabin-Karp. */
  colision?: boolean;
  /** Solo Rabin-Karp: fórmula con números del hash rodante. */
  calculo_hash?: string;
}

export interface PreprocesoKmp {
  lps: number[];
  pasos_lps: string[];
}
export interface PreprocesoBoyerMoore {
  caracter_malo: Record<string, number>;
  sufijo_bueno: number[];
  bordes?: number[];
  pasos: string[];
}
export interface PreprocesoRabinKarp {
  base: number;
  modulo: number;
  h: number;
  hash_patron: number;
  pasos: string[];
}

interface TrazaBusquedaBase {
  nombre: string;
  texto: string;
  patron: string;
  pasos: PasoBusqueda[];
  posiciones: number[];
  total_comparaciones: number;
  articulo_id?: number;
  /** Desplazamiento del recorte dentro del abstract. */
  inicio_texto?: number;
  /** Solo Rabin-Karp. */
  total_colisiones?: number;
}

export type TrazaBusqueda =
  | (TrazaBusquedaBase & { clave: "kmp"; preprocesamiento: PreprocesoKmp })
  | (TrazaBusquedaBase & { clave: "boyer_moore"; preprocesamiento: PreprocesoBoyerMoore })
  | (TrazaBusquedaBase & { clave: "rabin_karp"; preprocesamiento: PreprocesoRabinKarp });

// ---------- Seguimiento: Ranking ----------
export type ClaveOrden = "counting_sort" | "radix_sort" | "bucket_sort";

export interface TerminoFrecuencia {
  termino: string;
  frecuencia: number;
}

export interface AlgoritmoRanking {
  clave: ClaveOrden;
  nombre: string;
  tiempo_ms: number;
  complejidad: string;
  top: TerminoFrecuencia[];
}

export interface RespuestaRanking {
  total_tokens: number;
  terminos_distintos: number;
  frecuencia_maxima: number;
  algoritmos: AlgoritmoRanking[];
  coinciden: boolean;
}

export interface RespuestaBenchmark {
  n: number;
  repeticiones: number;
  algoritmos: { clave: ClaveOrden; promedio_ms: number; minimo_ms: number; maximo_ms: number }[];
  escalamiento: ({ n: number } & Record<ClaveOrden, number>)[];
}
