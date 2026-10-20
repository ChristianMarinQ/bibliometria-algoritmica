// Corpus del modo mocks: los 20 artículos REALES (títulos, autores, revistas y abstracts)
// copiados de data/corpus.json con `npm run mocks:sync`. Solo los cálculos del motor son simulados.
import type { ArticuloDetalle } from "../tipos";
import datos from "./corpus.json";

// `palabras_abstract` se calcula igual que el backend: número de palabras separadas por espacios.
export const ARTICULOS_MOCK: ArticuloDetalle[] = datos.map((a) => ({
  ...a,
  origen: "base" as const,
  palabras_abstract: a.abstract.split(/\s+/).filter(Boolean).length,
}));

// Generador pseudoaleatorio determinista (mulberry32) para que los mocks sean estables.
export function crearAleatorio(semilla: number): () => number {
  let a = semilla >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
