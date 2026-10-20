// Motor de los mocks: reimplementa en TypeScript, de forma simplificada, los cálculos
// del backend para que el frontend pueda desarrollarse sin la API. Los valores son
// coherentes entre sí pero NO sustituyen a la implementación oficial en Python.
import type {
  ArticuloRef,
  ClaveBusqueda,
  ClaveEnlace,
  ClaveOrden,
  ClaveSimilitud,
  Fusion,
  MetodoClustering,
  MetricaBusqueda,
  NodoArbol,
  PasoBusqueda,
  PeticionBusqueda,
  PeticionTrazaBusqueda,
  Representacion,
  RespuestaBenchmark,
  RespuestaBusqueda,
  RespuestaClustering,
  RespuestaRanking,
  RespuestaSimilitud,
  ResultadoBusqueda,
  TerminoFrecuencia,
  TrazaBusqueda,
  TrazaSimilitud,
} from "../tipos";
import { ARTICULOS_MOCK, crearAleatorio } from "./corpus";

// ---------------- Preprocesamiento ----------------
const VACIAS = new Set(
  "the a an and or of in on to for with by from as at is are was were be been this that these those it its we our their which such than also into using used use most few each new still how what where".split(" "),
);

export function preprocesar(texto: string): string[] {
  return texto
    .toLowerCase()
    .replace(/[^a-z\s-]/g, " ")
    .split(/[\s-]+/)
    .filter((p) => p.length > 2 && !VACIAS.has(p));
}

const TOKENS = new Map<number, string[]>(ARTICULOS_MOCK.map((a) => [a.id, preprocesar(a.abstract)]));
// Los artículos subidos en modo mocks se preprocesan la primera vez que se piden.
const tokens = (id: number) => {
  let t = TOKENS.get(id);
  if (!t) {
    const a = ARTICULOS_MOCK.find((x) => x.id === id);
    t = a ? preprocesar(a.abstract) : [];
    if (a) TOKENS.set(id, t);
  }
  return t;
};
const ref = (id: number): ArticuloRef => {
  const a = ARTICULOS_MOCK.find((x) => x.id === id);
  if (!a) throw new Error(`Artículo ${id} no encontrado`);
  return { id: a.id, titulo: a.titulo };
};

function medir<T>(fn: () => T): [T, number] {
  const t0 = performance.now();
  const r = fn();
  // Se garantiza un tiempo mínimo distinto de cero para la visualización.
  return [r, Math.max(performance.now() - t0, 0.001)];
}

// ---------------- Similitud: edición ----------------
function levenshtein(a: string[], b: string[]): number[][] {
  const m: number[][] = Array.from({ length: a.length + 1 }, (_, i) =>
    Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0)),
  );
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      m[i][j] = Math.min(m[i - 1][j] + 1, m[i][j - 1] + 1, m[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return m;
}

const NW = { match: 1, mismatch: -1, gap: -1 };
function needleman(a: string[], b: string[]): number[][] {
  const m: number[][] = Array.from({ length: a.length + 1 }, (_, i) =>
    Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j * NW.gap : j === 0 ? i * NW.gap : 0)),
  );
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      m[i][j] = Math.max(
        m[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? NW.match : NW.mismatch),
        m[i - 1][j] + NW.gap,
        m[i][j - 1] + NW.gap,
      );
  return m;
}

// Reconstruye el camino óptimo desde la esquina inferior derecha hasta (0, 0).
function camino(m: number[][], a: string[], b: string[], modo: "lev" | "nw"): [number, number][] {
  let i = a.length;
  let j = b.length;
  const ruta: [number, number][] = [[i, j]];
  while (i > 0 || j > 0) {
    const igual = i > 0 && j > 0 && a[i - 1] === b[j - 1];
    if (modo === "lev") {
      if (i > 0 && j > 0 && m[i][j] === m[i - 1][j - 1] + (igual ? 0 : 1)) { i--; j--; }
      else if (i > 0 && m[i][j] === m[i - 1][j] + 1) i--;
      else j--;
    } else {
      if (i > 0 && j > 0 && m[i][j] === m[i - 1][j - 1] + (igual ? NW.match : NW.mismatch)) { i--; j--; }
      else if (i > 0 && m[i][j] === m[i - 1][j] + NW.gap) i--;
      else j--;
    }
    ruta.push([i, j]);
  }
  return ruta.reverse();
}

const simLev = (a: string[], b: string[]) => 1 - levenshtein(a, b)[a.length][b.length] / Math.max(a.length, b.length, 1);
const simNw = (a: string[], b: string[]) => {
  const largo = Math.max(a.length, b.length, 1);
  const p = needleman(a, b)[a.length][b.length];
  return Math.min(1, Math.max(0, (p + largo) / (2 * largo)));
};

// ---------------- Similitud: TF-IDF y Jaccard ----------------
const N = ARTICULOS_MOCK.length;
const DF = new Map<string, number>();
for (const t of TOKENS.values()) for (const p of new Set(t)) DF.set(p, (DF.get(p) ?? 0) + 1);
const idf = (p: string) => Math.log(N / (DF.get(p) ?? 1)) + 1;
const VOCABULARIO = [...DF.keys()].sort();

function tf(t: string[]): Map<string, number> {
  const c = new Map<string, number>();
  for (const p of t) c.set(p, (c.get(p) ?? 0) + 1 / t.length);
  return c;
}
function vectorTfidf(id: number): number[] {
  const f = tf(tokens(id));
  return VOCABULARIO.map((p) => (f.get(p) ?? 0) * idf(p));
}
const punto = (u: number[], v: number[]) => u.reduce((s, x, k) => s + x * v[k], 0);
const norma = (u: number[]) => Math.sqrt(punto(u, u));
const coseno = (u: number[], v: number[]) => punto(u, v) / (norma(u) * norma(v) || 1);

function jaccard(a: string[], b: string[]) {
  const A = new Set(a);
  const B = new Set(b);
  const inter = [...A].filter((x) => B.has(x));
  return inter.length / new Set([...A, ...B]).size;
}

// ---------------- Similitud: embeddings simulados ----------------
// Cada palabra recibe un vector pseudoaleatorio estable (hash → semilla); el
// documento es el promedio normalizado, lo que imita el comportamiento de un embedding.
function hash(s: string): number {
  let h = 2166136261;
  for (let k = 0; k < s.length; k++) h = Math.imul(h ^ s.charCodeAt(k), 16777619);
  return h >>> 0;
}
const CACHE_PALABRA = new Map<string, number[]>();
function vectorPalabra(p: string, dim: number): number[] {
  const clave = `${dim}:${p}`;
  let v = CACHE_PALABRA.get(clave);
  if (!v) {
    const azar = crearAleatorio(hash(p) + dim);
    v = Array.from({ length: dim }, () => azar() * 2 - 1);
    CACHE_PALABRA.set(clave, v);
  }
  return v;
}
function embedding(id: number, modelo: "word2vec" | "sbert") {
  const dim = modelo === "sbert" ? 384 : 100;
  const t = tokens(id);
  // word2vec: algunas palabras quedan fuera del vocabulario del modelo.
  const conVector = modelo === "word2vec" ? t.filter((p) => hash(p) % 11 !== 0) : t;
  const suma = new Array(dim).fill(0);
  for (const p of conVector) vectorPalabra(p, dim).forEach((x, k) => (suma[k] += x));
  // Componente compartida que simula el "tema general" que captura un modelo de oraciones.
  const tema = vectorPalabra("__tema__", dim);
  const peso = modelo === "sbert" ? conVector.length * 0.35 : conVector.length * 0.15;
  tema.forEach((x, k) => (suma[k] += x * peso));
  const n = norma(suma) || 1;
  return { vector: suma.map((x) => x / n), cobertura: conVector.length / (t.length || 1), dim };
}

// ---------------- Req. 1: endpoints ----------------
const NOMBRES: Record<ClaveSimilitud, [string, "clasico" | "ia"]> = {
  levenshtein: ["Levenshtein", "clasico"],
  needleman_wunsch: ["Needleman-Wunsch", "clasico"],
  coseno_tfidf: ["Coseno TF-IDF", "clasico"],
  jaccard: ["Jaccard", "clasico"],
  word2vec: ["Word2Vec (promedio)", "ia"],
  sbert: ["Sentence-BERT", "ia"],
};
const TODOS: ClaveSimilitud[] = ["levenshtein", "needleman_wunsch", "coseno_tfidf", "jaccard", "word2vec", "sbert"];

function similitudPar(clave: ClaveSimilitud, a: number, b: number): number {
  switch (clave) {
    case "levenshtein": return simLev(tokens(a), tokens(b));
    case "needleman_wunsch": return simNw(tokens(a), tokens(b));
    case "coseno_tfidf": return coseno(vectorTfidf(a), vectorTfidf(b));
    case "jaccard": return jaccard(tokens(a), tokens(b));
    case "word2vec":
    case "sbert": return Math.max(0, punto(embedding(a, clave).vector, embedding(b, clave).vector));
  }
}

export function similitud(ids: number[], algoritmos?: ClaveSimilitud[]): RespuestaSimilitud {
  if (ids.length < 2) throw new Error("Se requieren al menos 2 artículos");
  const claves = algoritmos?.length ? algoritmos : TODOS;
  return {
    articulos: ids.map(ref),
    resultados: claves.map((clave) => {
      const [matriz, tiempo_ms] = medir(() =>
        ids.map((a, i) => ids.map((b, j) => (i === j ? 1 : similitudPar(clave, a, b)))),
      );
      return { clave, nombre: NOMBRES[clave][0], tipo: NOMBRES[clave][1], matriz, tiempo_ms };
    }),
  };
}

const r4 = (x: number) => Math.round(x * 10000) / 10000;

export function trazaSimilitud(id_a: number, id_b: number, clave: ClaveSimilitud): TrazaSimilitud {
  const A = tokens(id_a);
  const B = tokens(id_b);
  const base = { nombre: NOMBRES[clave][0], tipo: NOMBRES[clave][1] };
  if (clave === "levenshtein" || clave === "needleman_wunsch") {
    const esLev = clave === "levenshtein";
    const completa = esLev ? levenshtein(A, B) : needleman(A, B);
    const valor = completa[A.length][B.length];
    const ruta = camino(completa, A, B, esLev ? "lev" : "nw");
    // Alineamiento de dos filas (solo NW) a partir del camino completo.
    const al = { a: [] as string[], b: [] as string[] };
    for (let k = 1; k < ruta.length; k++) {
      const [i0, j0] = ruta[k - 1];
      const [i1, j1] = ruta[k];
      al.a.push(i1 > i0 ? A[i1 - 1] : "-");
      al.b.push(j1 > j0 ? B[j1 - 1] : "-");
    }
    return {
      ...base,
      clave,
      similitud: r4(esLev ? simLev(A, B) : simNw(A, B)),
      formula: esLev ? "sim = 1 - d / max(|A|, |B|)" : "sim = (S + max(|A|,|B|)) / (2 · max(|A|,|B|))",
      pasos: [
        `Texto: se trabaja a nivel de palabras del texto preprocesado (|A| = ${A.length}, |B| = ${B.length}).`,
        esLev
          ? "Se inicializa la primera fila y columna con 0, 1, 2, … (costo de insertar o borrar)."
          : `Se inicializa la primera fila y columna con múltiplos de la penalización gap = ${NW.gap}.`,
        esLev
          ? "Cada celda D[i][j] = mín(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + costo), con costo 0 si las palabras coinciden."
          : "Cada celda F[i][j] = máx(F[i-1][j-1] + s(a,b), F[i-1][j] + gap, F[i][j-1] + gap).",
        esLev ? `Distancia total sobre el texto completo: d = ${valor}.` : `Puntaje global de alineamiento: S = ${valor}.`,
        "El camino resaltado reconstruye las operaciones óptimas desde la esquina final.",
      ],
      detalle: {
        secuencia_a: A,
        secuencia_b: B,
        matriz: completa.slice(0, 13).map((f) => f.slice(0, 13)),
        truncado: A.length > 12 || B.length > 12,
        camino: ruta,
        ...(esLev ? { distancia: valor } : { puntaje: valor, parametros: NW, alineamiento: al }),
      },
    };
  }
  if (clave === "coseno_tfidf") {
    const fa = tf(A);
    const fb = tf(B);
    const terminos = [...new Set([...A, ...B])]
      .map((t) => {
        const i = idf(t);
        const ta = fa.get(t) ?? 0;
        const tb = fb.get(t) ?? 0;
        return { termino: t, tf_a: r4(ta), tf_b: r4(tb), idf: r4(i), peso_a: r4(ta * i), peso_b: r4(tb * i) };
      })
      .sort((x, y) => y.peso_a * y.peso_b - x.peso_a * x.peso_b || y.peso_a + y.peso_b - (x.peso_a + x.peso_b))
      .slice(0, 25);
    const va = vectorTfidf(id_a);
    const vb = vectorTfidf(id_b);
    const pp = punto(va, vb);
    const na = norma(va);
    const nb = norma(vb);
    const s = pp / (na * nb);
    return {
      ...base,
      clave,
      similitud: r4(s),
      formula: "cos θ = (A · B) / (‖A‖ · ‖B‖)",
      pasos: [
        "Se calcula la frecuencia relativa tf de cada término en cada abstract.",
        `Se pondera con idf = ln(N / df) + 1, con N = ${N} documentos.`,
        `Producto punto A · B = ${r4(pp)}.`,
        `Normas ‖A‖ = ${r4(na)}, ‖B‖ = ${r4(nb)}.`,
        `cos θ = ${r4(s)} → θ = ${(Math.acos(Math.min(1, s)) * 180 / Math.PI).toFixed(1)}°.`,
      ],
      detalle: { terminos, producto_punto: r4(pp), norma_a: r4(na), norma_b: r4(nb), angulo_grados: r4((Math.acos(Math.min(1, s)) * 180) / Math.PI) },
    };
  }
  if (clave === "jaccard") {
    const SA = new Set(A);
    const SB = new Set(B);
    const interseccion = [...SA].filter((x) => SB.has(x)).sort();
    const solo_a = [...SA].filter((x) => !SB.has(x)).sort();
    const solo_b = [...SB].filter((x) => !SA.has(x)).sort();
    const union = interseccion.length + solo_a.length + solo_b.length;
    return {
      ...base,
      clave,
      similitud: r4(interseccion.length / union),
      formula: "J(A, B) = |A ∩ B| / |A ∪ B|",
      pasos: [
        "Cada abstract se convierte en el conjunto de sus términos (sin repeticiones).",
        `|A| = ${SA.size}, |B| = ${SB.size}.`,
        `|A ∩ B| = ${interseccion.length}, |A ∪ B| = ${union}.`,
        `J = ${interseccion.length} / ${union} = ${r4(interseccion.length / union)}.`,
      ],
      detalle: { interseccion, solo_a, solo_b, tam_interseccion: interseccion.length, tam_union: union },
    };
  }
  const ea = embedding(id_a, clave);
  const eb = embedding(id_b, clave);
  const cos = punto(ea.vector, eb.vector);
  const eucl = Math.sqrt(ea.vector.reduce((s, x, k) => s + (x - eb.vector[k]) ** 2, 0));
  return {
    ...base,
    clave,
    similitud: r4(Math.max(0, cos)),
    formula: "sim = cos(u, v) = (u · v) / (‖u‖ · ‖v‖)",
    pasos: [
      clave === "sbert"
        ? "El modelo codifica cada abstract completo en un vector de 384 dimensiones."
        : "Cada palabra se reemplaza por su vector del modelo y se promedian (palabras sin vector se omiten).",
      "Los vectores se normalizan a norma 1.",
      `Producto punto u · v = ${r4(cos)}; al tener norma 1, coincide con el coseno.`,
      `Distancia euclidiana ‖u − v‖ = ${r4(eucl)}.`,
    ],
    detalle: {
      modelo: clave === "sbert" ? "all-MiniLM-L6-v2" : "word2vec-google-news-300 (simulado)",
      dimensiones: ea.dim,
      vector_a: ea.vector.slice(0, 16).map(r4),
      vector_b: eb.vector.slice(0, 16).map(r4),
      coseno: r4(cos),
      distancia_euclidiana: r4(eucl),
      producto_punto: r4(cos),
      norma_a: 1,
      norma_b: 1,
      ...(clave === "word2vec" ? { cobertura_a: r4(ea.cobertura), cobertura_b: r4(eb.cobertura) } : {}),
    },
  };
}

// ---------------- Req. 2: clustering jerárquico ----------------
function agrupar(dist: number[][], enlace: ClaveEnlace) {
  const n = dist.length;
  // Cada grupo activo guarda su id (estilo scipy: hojas 0..n-1, nuevos n, n+1, …) y sus hojas.
  let grupos = Array.from({ length: n }, (_, k) => ({ id: k, hojas: [k] }));
  const fusiones: Fusion[] = [];
  const dGrupo = (x: number[], y: number[]) => {
    const ds = x.flatMap((i) => y.map((j) => dist[i][j]));
    if (enlace === "single") return Math.min(...ds);
    if (enlace === "complete") return Math.max(...ds);
    return ds.reduce((s, d) => s + d, 0) / ds.length;
  };
  let siguiente = n;
  while (grupos.length > 1) {
    let mejor = [0, 1, Infinity];
    for (let i = 0; i < grupos.length; i++)
      for (let j = i + 1; j < grupos.length; j++) {
        const d = dGrupo(grupos[i].hojas, grupos[j].hojas);
        if (d < mejor[2]) mejor = [i, j, d];
      }
    const [i, j, d] = mejor;
    const nuevo = { id: siguiente++, hojas: [...grupos[i].hojas, ...grupos[j].hojas] };
    fusiones.push({ paso: fusiones.length + 1, a: grupos[i].id, b: grupos[j].id, nuevo: nuevo.id, distancia: r4(d), tamano: nuevo.hojas.length });
    grupos = grupos.filter((_, k) => k !== i && k !== j).concat(nuevo);
  }
  return fusiones;
}

function construirArbol(fusiones: Fusion[], ids: number[]): NodoArbol {
  const nodos = new Map<number, NodoArbol>();
  ids.forEach((aid, k) => nodos.set(k, { id: k, articulo_id: aid, titulo: ref(aid).titulo, distancia: 0, tamano: 1 }));
  for (const f of fusiones)
    nodos.set(f.nuevo, { id: f.nuevo, distancia: f.distancia, tamano: f.tamano, hijos: [nodos.get(f.a)!, nodos.get(f.b)!] });
  return nodos.get(fusiones[fusiones.length - 1].nuevo)!;
}

function pearson(x: number[], y: number[]): number {
  const mx = x.reduce((s, v) => s + v, 0) / x.length;
  const my = y.reduce((s, v) => s + v, 0) / y.length;
  let sxy = 0, sxx = 0, syy = 0;
  x.forEach((v, k) => { sxy += (v - mx) * (y[k] - my); sxx += (v - mx) ** 2; syy += (y[k] - my) ** 2; });
  return sxy / Math.sqrt(sxx * syy || 1);
}

function metricas(fusiones: Fusion[], dist: number[][], k: number) {
  const n = dist.length;
  const miembros = new Map<number, number[]>(Array.from({ length: n }, (_, i) => [i, [i]]));
  const cof = dist.map((f) => f.map(() => 0));
  for (const f of fusiones) {
    const A = miembros.get(f.a)!;
    const B = miembros.get(f.b)!;
    for (const i of A) for (const j of B) cof[i][j] = cof[j][i] = f.distancia;
    miembros.set(f.nuevo, [...A, ...B]);
  }
  const orig: number[] = [];
  const coph: number[] = [];
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) { orig.push(dist[i][j]); coph.push(cof[i][j]); }

  // Corte en k grupos: se aplican solo las primeras n − k fusiones.
  const etiqueta = Array.from({ length: n }, (_, i) => i);
  const hojas = new Map<number, number[]>(Array.from({ length: n }, (_, i) => [i, [i]]));
  for (const f of fusiones.slice(0, n - k)) {
    const todas = [...hojas.get(f.a)!, ...hojas.get(f.b)!];
    hojas.set(f.nuevo, todas);
    for (const h of todas) etiqueta[h] = f.nuevo;
  }
  let suma = 0;
  for (let i = 0; i < n; i++) {
    const propio = etiqueta.map((e, j) => (e === etiqueta[i] && j !== i ? dist[i][j] : -1)).filter((d) => d >= 0);
    if (!propio.length) continue; // silhouette = 0 para grupos unitarios
    const a = propio.reduce((s, d) => s + d, 0) / propio.length;
    let b = Infinity;
    for (const e of new Set(etiqueta)) {
      if (e === etiqueta[i]) continue;
      const otros = etiqueta.map((x, j) => (x === e ? dist[i][j] : -1)).filter((d) => d >= 0);
      b = Math.min(b, otros.reduce((s, d) => s + d, 0) / otros.length);
    }
    suma += (b - a) / Math.max(a, b);
  }
  return { silhouette: r4(suma / n), correlacion_cofenetica: r4(pearson(orig, coph)) };
}

export function clustering(representacion: Representacion = "tfidf", k = 4): RespuestaClustering {
  const ids = ARTICULOS_MOCK.map((a) => a.id);
  const vectores = ids.map((id) => (representacion === "tfidf" ? vectorTfidf(id) : embedding(id, "sbert").vector));
  const dist = vectores.map((u) => vectores.map((v) => Math.max(0, 1 - coseno(u, v))));
  const nombres: Record<ClaveEnlace, string> = { single: "Single Linkage", complete: "Complete Linkage", average: "Average Linkage" };
  const metodos: MetodoClustering[] = (["single", "complete", "average"] as ClaveEnlace[]).map((clave) => {
    const [fusiones, tiempo_ms] = medir(() => agrupar(dist, clave));
    return { clave, nombre: nombres[clave], arbol: construirArbol(fusiones, ids), fusiones, ...metricas(fusiones, dist, k), tiempo_ms };
  });
  const mejor = [...metodos].sort((a, b) => b.correlacion_cofenetica - a.correlacion_cofenetica || b.silhouette - a.silhouette)[0];
  return {
    representacion,
    articulos: ids.map(ref),
    metodos,
    mejor_metodo: mejor.clave,
    criterio: "Mayor coeficiente de correlación cofenética; Silhouette como desempate",
  };
}

// ---------------- Req. 3: búsqueda de patrones ----------------
function tablaLps(p: string) {
  const lps = new Array(p.length).fill(0);
  const pasos: string[] = [];
  let largo = 0;
  for (let i = 1; i < p.length; ) {
    if (p[i] === p[largo]) {
      lps[i++] = ++largo;
      pasos.push(`P[${i - 1}] = '${p[i - 1]}' extiende el borde → LPS[${i - 1}] = ${largo}.`);
    } else if (largo > 0) {
      pasos.push(`P[${i}] ≠ P[${largo}]: se retrocede al borde LPS[${largo - 1}] = ${lps[largo - 1]}.`);
      largo = lps[largo - 1];
    } else {
      pasos.push(`P[${i}] = '${p[i]}' no tiene borde → LPS[${i}] = 0.`);
      lps[i++] = 0;
    }
  }
  return { lps, pasos_lps: pasos };
}

function caracterMalo(p: string): Record<string, number> {
  const t: Record<string, number> = {};
  for (let k = 0; k < p.length; k++) t[p[k]] = k;
  return t;
}

// Tabla del sufijo bueno (versión "fuerte") de longitud m + 1.
function sufijoBueno(p: string): number[] {
  const m = p.length;
  const despl = new Array(m + 1).fill(0);
  const borde = new Array(m + 1).fill(0);
  let i = m;
  let j = m + 1;
  borde[i] = j;
  while (i > 0) {
    while (j <= m && p[i - 1] !== p[j - 1]) {
      if (despl[j] === 0) despl[j] = j - i;
      j = borde[j];
    }
    borde[--i] = --j;
  }
  j = borde[0];
  for (i = 0; i <= m; i++) {
    if (despl[i] === 0) despl[i] = j;
    if (i === j) j = borde[j];
  }
  return despl;
}

const RK = { base: 256, modulo: 101 };

function buscarKmp(t: string, p: string, conTraza: boolean) {
  const { lps } = tablaLps(p);
  const m = p.length;
  const pasos: PasoBusqueda[] = [];
  const posiciones: number[] = [];
  let total = 0;
  let q = 0;
  for (let s = 0; s <= t.length - m; ) {
    const comps = [];
    while (q < m) {
      const igual = t[s + q] === p[q];
      total++;
      if (conTraza) comps.push({ i: s + q, j: q, igual });
      if (!igual) break;
      q++;
    }
    let desp: number;
    let nuevoQ: number;
    let motivo: string;
    if (q === m) {
      posiciones.push(s);
      desp = m - lps[m - 1];
      nuevoQ = lps[m - 1];
      motivo = `Coincidencia completa. Se reutiliza el borde LPS[${m - 1}] = ${lps[m - 1]} y se desplaza ${desp}.`;
    } else if (q === 0) {
      desp = 1;
      nuevoQ = 0;
      motivo = "Falla en el primer carácter del patrón: se avanza 1 posición.";
    } else {
      desp = q - lps[q - 1];
      nuevoQ = lps[q - 1];
      motivo = `Falla tras ${q} coincidencias. LPS[${q - 1}] = ${lps[q - 1]} → desplazamiento ${q} − ${lps[q - 1]} = ${desp}, sin re-comparar ${lps[q - 1]} caracteres.`;
    }
    if (conTraza) pasos.push({ alineacion: s, comparaciones: comps, coincidencia: q === m, desplazamiento: desp, motivo, hash_ventana: null });
    s += desp;
    q = nuevoQ;
  }
  return { pasos, posiciones, total };
}

function buscarBoyerMoore(t: string, p: string, conTraza: boolean) {
  const malo = caracterMalo(p);
  const bueno = sufijoBueno(p);
  const m = p.length;
  const pasos: PasoBusqueda[] = [];
  const posiciones: number[] = [];
  let total = 0;
  for (let s = 0; s <= t.length - m; ) {
    const comps = [];
    let j = m - 1;
    while (j >= 0) {
      const igual = p[j] === t[s + j];
      total++;
      if (conTraza) comps.push({ i: s + j, j, igual });
      if (!igual) break;
      j--;
    }
    let desp: number;
    let motivo: string;
    if (j < 0) {
      posiciones.push(s);
      desp = bueno[0];
      motivo = `Coincidencia completa. Regla del sufijo bueno: se desplaza ${desp}.`;
    } else {
      const c = t[s + j];
      const ultima = malo[c] ?? -1;
      const dMalo = Math.max(1, j - ultima);
      const dBueno = bueno[j + 1];
      desp = Math.max(dMalo, dBueno);
      motivo =
        `Carácter malo '${c}' en j = ${j}` +
        (ultima < 0 ? " no aparece en el patrón" : ` (última aparición ${ultima})`) +
        ` → ${dMalo}; sufijo bueno → ${dBueno}. Se toma el máximo: ${desp}.`;
    }
    if (conTraza) pasos.push({ alineacion: s, comparaciones: comps, coincidencia: j < 0, desplazamiento: desp, motivo, hash_ventana: null });
    s += desp;
  }
  return { pasos, posiciones, total };
}

function buscarRabinKarp(t: string, p: string, conTraza: boolean) {
  const { base, modulo } = RK;
  const m = p.length;
  let h = 1;
  for (let k = 0; k < m - 1; k++) h = (h * base) % modulo;
  let hp = 0;
  let hv = 0;
  for (let k = 0; k < m; k++) {
    hp = (base * hp + p.charCodeAt(k)) % modulo;
    hv = (base * hv + (t.charCodeAt(k) || 0)) % modulo;
  }
  const pasos: PasoBusqueda[] = [];
  const posiciones: number[] = [];
  let total = 0;
  for (let s = 0; s <= t.length - m; s++) {
    const comps = [];
    let coincide = false;
    let colision = false;
    let motivo: string;
    const calculo_hash =
      s === 0
        ? `hash(T[0..${m - 1}]) por Horner mod ${modulo} = ${hv}`
        : `(${base} · (h_ant − '${t[s - 1]}'·${h}) + '${t[s + m - 1]}') mod ${modulo} = ${hv}`;
    if (hv === hp) {
      let j = 0;
      while (j < m) {
        const igual = t[s + j] === p[j];
        total++;
        if (conTraza) comps.push({ i: s + j, j, igual });
        if (!igual) break;
        j++;
      }
      coincide = j === m;
      colision = !coincide;
      if (coincide) posiciones.push(s);
      motivo = coincide
        ? `hash(ventana) = ${hv} = hash(patrón): se verifican los caracteres y coinciden.`
        : `Colisión: hash(ventana) = ${hv} = hash(patrón) pero los caracteres difieren.`;
    } else {
      motivo = `hash(ventana) = ${hv} ≠ ${hp}: se descarta sin comparar caracteres.`;
    }
    if (conTraza) pasos.push({ alineacion: s, comparaciones: comps, coincidencia: coincide, desplazamiento: 1, motivo, hash_ventana: hv, colision, calculo_hash });
    // Hash rodante: se quita el carácter que sale y se agrega el que entra.
    if (s < t.length - m) {
      hv = (base * (hv - t.charCodeAt(s) * h) + t.charCodeAt(s + m)) % modulo;
      if (hv < 0) hv += modulo;
    }
  }
  return { pasos, posiciones, total, h, hp };
}

const NOMBRES_BUSQUEDA: Record<ClaveBusqueda, string> = { kmp: "Knuth-Morris-Pratt", boyer_moore: "Boyer-Moore", rabin_karp: "Rabin-Karp" };
const BUSCADORES = { kmp: buscarKmp, boyer_moore: buscarBoyerMoore, rabin_karp: buscarRabinKarp };

export function busqueda({ patron, ids, distinguir_mayusculas }: PeticionBusqueda): RespuestaBusqueda {
  if (!patron.trim()) throw new Error("El patrón no puede estar vacío");
  const articulos = ARTICULOS_MOCK.filter((a) => !ids || ids.includes(a.id));
  const norm = (s: string) => (distinguir_mayusculas ? s : s.toLowerCase());
  const p = norm(patron);
  const porAlgoritmo = new Map<ClaveBusqueda, number[][]>();
  const algoritmos: MetricaBusqueda[] = (Object.keys(BUSCADORES) as ClaveBusqueda[]).map((clave) => {
    const [, tPre] = medir(() => (clave === "kmp" ? tablaLps(p) : clave === "boyer_moore" ? sufijoBueno(p) : null));
    let comparaciones = 0;
    const [pos, tBus] = medir(() =>
      articulos.map((a) => {
        const r = BUSCADORES[clave](norm(a.abstract), p, false);
        comparaciones += r.total;
        return r.posiciones;
      }),
    );
    porAlgoritmo.set(clave, pos);
    return {
      clave,
      nombre: NOMBRES_BUSQUEDA[clave],
      tiempo_preprocesamiento_ms: tPre,
      tiempo_busqueda_ms: tBus,
      comparaciones,
      total_coincidencias: pos.reduce((s, l) => s + l.length, 0),
    };
  });
  const ref0 = porAlgoritmo.get("kmp")!;
  const coinciden = [...porAlgoritmo.values()].every((l) => JSON.stringify(l) === JSON.stringify(ref0));
  const resultados: ResultadoBusqueda[] = articulos
    .map((a, k) => ({
      articulo_id: a.id,
      titulo: a.titulo,
      posiciones: ref0[k],
      fragmentos: ref0[k].map((pos) => ({
        posicion: pos,
        antes: (pos > 40 ? "…" : "") + a.abstract.slice(Math.max(0, pos - 40), pos),
        coincidencia: a.abstract.slice(pos, pos + patron.length),
        despues: a.abstract.slice(pos + patron.length, pos + patron.length + 40) + (pos + patron.length + 40 < a.abstract.length ? "…" : ""),
      })),
    }))
    .filter((r) => r.posiciones.length > 0);
  return { patron, algoritmos, coinciden, resultados };
}

export function trazaBusqueda({
  patron: original,
  algoritmo: clave,
  articulo_id,
  max_caracteres = 300,
  distinguir_mayusculas = false,
}: PeticionTrazaBusqueda): TrazaBusqueda {
  const articulo = ARTICULOS_MOCK.find((a) => a.id === articulo_id);
  if (!articulo) throw new Error("Artículo no encontrado");
  if (!original.trim()) throw new Error("El patrón no puede estar vacío");
  const norm = (s: string) => (distinguir_mayusculas ? s : s.toLowerCase());
  const patron = norm(original);
  const completo = norm(articulo.abstract);
  // Igual que el backend: si la primera ocurrencia queda fuera del recorte, se centra en ella.
  const primera = completo.indexOf(patron);
  let inicio = 0;
  if (primera >= 0 && primera + patron.length > max_caracteres) {
    inicio = Math.max(0, Math.min(primera - Math.floor((max_caracteres - patron.length) / 2), completo.length - max_caracteres));
  }
  const texto = completo.slice(inicio, inicio + max_caracteres);
  const base = { nombre: NOMBRES_BUSQUEDA[clave], texto, patron, articulo_id, inicio_texto: inicio };
  if (clave === "kmp") {
    const r = buscarKmp(texto, patron, true);
    return { ...base, clave, preprocesamiento: tablaLps(patron), pasos: r.pasos, posiciones: r.posiciones, total_comparaciones: r.total };
  }
  if (clave === "boyer_moore") {
    const r = buscarBoyerMoore(texto, patron, true);
    const malo = caracterMalo(patron);
    return {
      ...base,
      clave,
      preprocesamiento: {
        caracter_malo: malo,
        sufijo_bueno: sufijoBueno(patron),
        pasos: [
          "Carácter malo: para cada carácter del patrón se guarda su última posición.",
          "Sufijo bueno: para cada posición se calcula cuánto desplazar si el sufijo ya comparado coincide.",
          "En cada falla se usa el máximo de ambas reglas.",
        ],
      },
      pasos: r.pasos,
      posiciones: r.posiciones,
      total_comparaciones: r.total,
    };
  }
  const r = buscarRabinKarp(texto, patron, true);
  return {
    ...base,
    clave,
    total_colisiones: r.pasos.filter((p) => p.colision).length,
    preprocesamiento: {
      ...RK,
      h: r.h,
      hash_patron: r.hp,
      pasos: [
        `h = base^(m−1) mod q = ${RK.base}^${patron.length - 1} mod ${RK.modulo} = ${r.h}.`,
        `hash(patrón) = ${r.hp}, calculado con el método de Horner.`,
        "Cada ventana nueva se obtiene en O(1) quitando el carácter saliente y sumando el entrante.",
      ],
    },
    pasos: r.pasos,
    posiciones: r.posiciones,
    total_comparaciones: r.total,
  };
}

// ---------------- Seguimiento: ranking de términos ----------------
const FRECUENCIAS: TerminoFrecuencia[] = (() => {
  const c = new Map<string, number>();
  for (const t of TOKENS.values()) for (const p of t) c.set(p, (c.get(p) ?? 0) + 1);
  // Orden alfabético previo (auxiliar): los ordenamientos estables conservan los empates así.
  return [...c.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1)).map(([termino, frecuencia]) => ({ termino, frecuencia }));
})();
const MAXIMA = Math.max(...FRECUENCIAS.map((f) => f.frecuencia));

// Clave ascendente = MAXIMA − frecuencia, así el orden estable ascendente da frecuencia descendente.
function countingSort(l: TerminoFrecuencia[]) {
  const conteo = new Array(MAXIMA + 1).fill(0);
  for (const x of l) conteo[MAXIMA - x.frecuencia]++;
  for (let k = 1; k < conteo.length; k++) conteo[k] += conteo[k - 1];
  const salida = new Array(l.length);
  for (let k = l.length - 1; k >= 0; k--) salida[--conteo[MAXIMA - l[k].frecuencia]] = l[k];
  return salida as TerminoFrecuencia[];
}
function radixSort(l: TerminoFrecuencia[]) {
  let actual = l;
  for (let exp = 1; Math.floor(MAXIMA / exp) > 0; exp *= 10) {
    const cubetas: TerminoFrecuencia[][] = Array.from({ length: 10 }, () => []);
    for (const x of actual) cubetas[Math.floor((MAXIMA - x.frecuencia) / exp) % 10].push(x);
    actual = cubetas.flat();
  }
  return actual;
}
function bucketSort(l: TerminoFrecuencia[]) {
  const nc = Math.max(1, Math.ceil(Math.sqrt(l.length)));
  const cubetas: TerminoFrecuencia[][] = Array.from({ length: nc }, () => []);
  for (const x of l) cubetas[Math.min(nc - 1, Math.floor(((MAXIMA - x.frecuencia) / (MAXIMA + 1)) * nc))].push(x);
  for (const c of cubetas)
    for (let i = 1; i < c.length; i++) {
      const v = c[i];
      let j = i - 1;
      while (j >= 0 && c[j].frecuencia < v.frecuencia) { c[j + 1] = c[j]; j--; }
      c[j + 1] = v;
    }
  return cubetas.flat();
}
const ORDENADORES: Record<ClaveOrden, [string, string, (l: TerminoFrecuencia[]) => TerminoFrecuencia[]]> = {
  counting_sort: ["Counting Sort", "O(n + k)", countingSort],
  radix_sort: ["Radix Sort (LSD)", "O(d · (n + b))", radixSort],
  bucket_sort: ["Bucket Sort", "O(n + k) promedio", bucketSort],
};

export function ranking(top = 15): RespuestaRanking {
  const algoritmos = (Object.keys(ORDENADORES) as ClaveOrden[]).map((clave) => {
    const [nombre, complejidad, fn] = ORDENADORES[clave];
    const [orden, tiempo_ms] = medir(() => fn(FRECUENCIAS));
    return { clave, nombre, tiempo_ms, complejidad, top: orden.slice(0, top) };
  });
  const r0 = JSON.stringify(algoritmos[0].top);
  return {
    total_tokens: FRECUENCIAS.reduce((s, f) => s + f.frecuencia, 0),
    terminos_distintos: FRECUENCIAS.length,
    frecuencia_maxima: MAXIMA,
    algoritmos,
    coinciden: algoritmos.every((a) => JSON.stringify(a.top) === r0),
  };
}

export function benchmark(repeticiones = 50): RespuestaBenchmark {
  const claves = Object.keys(ORDENADORES) as ClaveOrden[];
  const algoritmos = claves.map((clave) => {
    const tiempos = Array.from({ length: repeticiones }, () => medir(() => ORDENADORES[clave][2](FRECUENCIAS))[1]);
    return {
      clave,
      promedio_ms: tiempos.reduce((s, t) => s + t, 0) / tiempos.length,
      minimo_ms: Math.min(...tiempos),
      maximo_ms: Math.max(...tiempos),
    };
  });
  const escalamiento = [1, 2, 4, 8].map((f) => {
    const lista = Array.from({ length: f }, () => FRECUENCIAS).flat();
    const fila = { n: lista.length } as { n: number } & Record<ClaveOrden, number>;
    for (const clave of claves) {
      const ts = Array.from({ length: 10 }, () => medir(() => ORDENADORES[clave][2](lista))[1]);
      fila[clave] = ts.reduce((s, t) => s + t, 0) / ts.length;
    }
    return fila;
  });
  return { n: FRECUENCIAS.length, repeticiones, algoritmos, escalamiento };
}
