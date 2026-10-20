// Subida simulada del modo mocks: los artículos agregados viven en memoria (ARTICULOS_MOCK)
// hasta recargar la página. Reproduce las validaciones y errores del contrato de la API.
import { ErrorApi } from "../cliente";
import type { ArticuloExtraido, ArticuloGuardado, ArticuloNuevo, InfoSistema } from "../tipos";
import { ARTICULOS_MOCK } from "./corpus";

/** Clave aceptada por el modo mocks (la API real usa la variable CLAVE_SUBIDA). */
export const CLAVE_MOCK = "demo";
const TAMANO_MAXIMO_MB = 15;
const BASE = 20;

const contar = (texto: string) => texto.split(/\s+/).filter(Boolean).length;
const normalizar = (t: string) => t.trim().toLowerCase().replace(/\s+/g, " ");

function exigirClave(clave: string) {
  if (clave !== CLAVE_MOCK) throw new ErrorApi("Clave de subida inválida", 403);
}

export function sistema(): InfoSistema {
  return {
    subida_habilitada: true,
    requiere_clave: true,
    ia_en_servidor: true,
    total_articulos: ARTICULOS_MOCK.length,
    articulos_base: BASE,
    tamano_maximo_mb: TAMANO_MAXIMO_MB,
  };
}

export function extraer(archivo: File, clave: string): ArticuloExtraido {
  exigirClave(clave);
  if (!archivo.name.toLowerCase().endsWith(".pdf")) throw new ErrorApi("El archivo no es un PDF", 400);
  if (archivo.size > TAMANO_MAXIMO_MB * 1024 * 1024) throw new ErrorApi("El archivo supera el tamaño máximo", 413);
  // No se lee el PDF: se arma un borrador a partir del nombre para poder probar la revisión.
  const titulo = archivo.name.replace(/\.pdf$/i, "").replace(/[-_]+/g, " ").trim();
  const abstract =
    "This simulated abstract stands in for the text extracted from the uploaded PDF. It discusses how generative " +
    "artificial intelligence tools support teachers and students in higher education, the ethical concerns they raise, " +
    "and the need for clear institutional guidelines on assessment and academic integrity.";
  return {
    archivo: archivo.name,
    titulo: titulo.charAt(0).toUpperCase() + titulo.slice(1),
    autores: ["Autor Simulado"],
    anio: null,
    revista: "",
    abstract,
    palabras_abstract: contar(abstract),
    advertencias: ["No se encontró el año", "No se encontró la revista", "Modo mocks: el contenido es simulado, no se leyó el PDF"],
  };
}

export function guardar(nuevo: ArticuloNuevo, clave: string): ArticuloGuardado {
  exigirClave(clave);
  const palabras = contar(nuevo.abstract);
  if (!nuevo.titulo.trim()) throw new ErrorApi("El título no puede estar vacío", 422);
  if (palabras < 30 || palabras > 1000) throw new ErrorApi("El abstract debe tener entre 30 y 1000 palabras", 422);
  if (ARTICULOS_MOCK.some((a) => normalizar(a.titulo) === normalizar(nuevo.titulo)))
    throw new ErrorApi("Ya existe un artículo con ese título", 409);
  const id = Math.max(BASE, ...ARTICULOS_MOCK.map((a) => a.id)) + 1;
  const articulo: ArticuloGuardado = {
    ...nuevo,
    titulo: nuevo.titulo.trim(),
    id,
    origen: "subido",
    palabras_abstract: palabras,
    embeddings: { word2vec: true, sbert: true },
  };
  ARTICULOS_MOCK.push(articulo);
  return articulo;
}

export function borrar(id: number, clave: string): void {
  exigirClave(clave);
  const k = ARTICULOS_MOCK.findIndex((a) => a.id === id);
  if (k < 0) throw new ErrorApi("Artículo no encontrado", 404);
  if (ARTICULOS_MOCK[k].origen !== "subido") throw new ErrorApi("Los artículos base no se pueden eliminar", 403);
  ARTICULOS_MOCK.splice(k, 1);
}
