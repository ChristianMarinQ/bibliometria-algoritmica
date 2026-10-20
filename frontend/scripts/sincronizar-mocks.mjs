// Copia los datos REALES del corpus (data/corpus.json, generado por el backend) al modo mocks.
// Uso: npm run mocks:sync  (repetir cada vez que se regenere el corpus).
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const origen = resolve(aqui, "../../data/corpus.json");
const destino = resolve(aqui, "../src/api/mocks/corpus.json");

const corpus = JSON.parse(readFileSync(origen, "utf-8"));
// Solo los campos que expone la API de corpus.
const articulos = corpus.map(({ id, titulo, autores, anio, revista, archivo, abstract }) => ({
  id,
  titulo,
  autores,
  anio,
  revista,
  archivo,
  abstract,
}));
writeFileSync(destino, JSON.stringify(articulos, null, 2) + "\n", "utf-8");
console.log(`Mocks sincronizados: ${articulos.length} artículos -> ${destino}`);
