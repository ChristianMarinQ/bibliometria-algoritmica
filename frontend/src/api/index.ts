// Punto único de acceso a la API. Con VITE_USAR_MOCKS=true las funciones responden
// con el motor local (src/api/mocks) y una latencia simulada; si no, llaman al backend.
// `senal` (AbortSignal) permite cancelar la petición si la vista ya no la necesita.
import { enviar, obtener, USAR_MOCKS } from "./cliente";
import type {
  Articulo,
  ArticuloDetalle,
  ClaveSimilitud,
  PeticionBusqueda,
  PeticionTrazaBusqueda,
  Representacion,
  RespuestaBenchmark,
  RespuestaBusqueda,
  RespuestaClustering,
  RespuestaRanking,
  RespuestaSimilitud,
  TrazaBusqueda,
  TrazaSimilitud,
} from "./tipos";

export * from "./tipos";
export { ErrorApi, URL_API, USAR_MOCKS } from "./cliente";

// Carga perezosa: el motor de mocks no entra en el paquete principal si no se usa.
const motor = () => import("./mocks/motor");
const corpus = () => import("./mocks/corpus");

async function simular<T>(fn: () => T | Promise<T>, latencia = 220): Promise<T> {
  await new Promise((r) => setTimeout(r, latencia));
  return fn();
}

export const api = {
  articulos(senal?: AbortSignal): Promise<Articulo[]> {
    if (USAR_MOCKS)
      return simular(async () => (await corpus()).ARTICULOS_MOCK.map(({ abstract: _omitido, ...a }) => a));
    return obtener("/articulos", undefined, senal);
  },

  articulo(id: number, senal?: AbortSignal): Promise<ArticuloDetalle> {
    if (USAR_MOCKS)
      return simular(async () => {
        const a = (await corpus()).ARTICULOS_MOCK.find((x) => x.id === id);
        if (!a) throw new Error("Artículo no encontrado");
        return a;
      }, 120);
    return obtener(`/articulos/${id}`, undefined, senal);
  },

  similitud(ids: number[], algoritmos?: ClaveSimilitud[], senal?: AbortSignal): Promise<RespuestaSimilitud> {
    if (USAR_MOCKS) return simular(async () => (await motor()).similitud(ids, algoritmos));
    return enviar("/similitud", algoritmos?.length ? { ids, algoritmos } : { ids }, senal);
  },

  trazaSimilitud(id_a: number, id_b: number, algoritmo: ClaveSimilitud, senal?: AbortSignal): Promise<TrazaSimilitud> {
    if (USAR_MOCKS) return simular(async () => (await motor()).trazaSimilitud(id_a, id_b, algoritmo), 160);
    return enviar("/similitud/traza", { id_a, id_b, algoritmo }, senal);
  },

  clustering(representacion: Representacion, k: number, senal?: AbortSignal): Promise<RespuestaClustering> {
    if (USAR_MOCKS) return simular(async () => (await motor()).clustering(representacion, k), 300);
    return obtener("/clustering", { representacion, k }, senal);
  },

  busqueda(peticion: PeticionBusqueda, senal?: AbortSignal): Promise<RespuestaBusqueda> {
    if (USAR_MOCKS) return simular(async () => (await motor()).busqueda(peticion), 180);
    return enviar("/busqueda", peticion, senal);
  },

  trazaBusqueda(peticion: PeticionTrazaBusqueda, senal?: AbortSignal): Promise<TrazaBusqueda> {
    if (USAR_MOCKS) return simular(async () => (await motor()).trazaBusqueda(peticion), 160);
    return enviar("/busqueda/traza", peticion, senal);
  },

  ranking(top = 15, senal?: AbortSignal): Promise<RespuestaRanking> {
    if (USAR_MOCKS) return simular(async () => (await motor()).ranking(top));
    return obtener("/ranking", { top }, senal);
  },

  benchmark(repeticiones = 50, senal?: AbortSignal): Promise<RespuestaBenchmark> {
    if (USAR_MOCKS) return simular(async () => (await motor()).benchmark(repeticiones), 300);
    return obtener("/ranking/benchmark", { repeticiones }, senal);
  },
};
