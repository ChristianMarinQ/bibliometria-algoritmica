// Hook que calcula estadísticas del corpus directamente en el cliente,
// sin hacer peticiones HTTP adicionales. Recibe la lista de artículos ya
// descargada (por ejemplo, la devuelta por usePeticion sobre /api/articulos)
// y devuelve un resumen memoizado que solo se recalcula cuando cambia la lista.
//
// Estadísticas calculadas:
//   total           — número de artículos en la lista.
//   caracteresPromedio — promedio de caracteres del campo `titulo` por artículo
//                        (el abstract no se expone en el tipo Articulo del cliente).
//   caracteresMin   — longitud mínima del título entre todos los artículos.
//   caracteresMax   — longitud máxima del título.
//   conAnio         — cuántos artículos tienen año registrado (anio !== null).
//   sinAnio         — cuántos artículos tienen año desconocido (anio === null).
//
// Uso:
//   const articulos = usePeticion(...)
//   const stats = useEstadisticasCorpus(articulos.datos ?? [])

import { useMemo } from "react";
import type { Articulo } from "../api/tipos";

/** Estadísticas básicas calculadas en el cliente sobre la lista de artículos. */
export interface EstadisticasCorpus {
  /** Número total de artículos en la lista. */
  total: number;
  /** Promedio de caracteres del título (redondeado a dos decimales). */
  caracteresPromedio: number;
  /** Número mínimo de caracteres del título. */
  caracteresMin: number;
  /** Número máximo de caracteres del título. */
  caracteresMax: number;
  /** Artículos con año de publicación conocido. */
  conAnio: number;
  /** Artículos sin año de publicación (campo null). */
  sinAnio: number;
}

/**
 * Calcula estadísticas del corpus directamente en el cliente.
 *
 * No realiza ninguna petición de red. Se recalcula solo cuando cambia
 * la referencia del arreglo `articulos` (memoizado con useMemo).
 *
 * @param articulos - Lista de artículos tal como la devuelve la API.
 * @returns Objeto con las estadísticas o valores en cero si la lista está vacía.
 */
export function useEstadisticasCorpus(articulos: Articulo[]): EstadisticasCorpus {
  return useMemo(() => {
    const total = articulos.length;

    // Lista vacía: devolver todo en cero para evitar divisiones por cero.
    if (total === 0) {
      return {
        total: 0,
        caracteresPromedio: 0,
        caracteresMin: 0,
        caracteresMax: 0,
        conAnio: 0,
        sinAnio: 0,
      };
    }

    let suma = 0;
    // Inicializar min y max con el primer elemento para no depender de Infinity.
    let minimo = articulos[0].titulo.length;
    let maximo = articulos[0].titulo.length;
    let conAnio = 0;
    let sinAnio = 0;

    for (const articulo of articulos) {
      const longitud = articulo.titulo.length;

      suma += longitud;
      if (longitud < minimo) minimo = longitud;
      if (longitud > maximo) maximo = longitud;

      // Contar artículos con y sin año de publicación registrado.
      if (articulo.anio !== null) {
        conAnio += 1;
      } else {
        sinAnio += 1;
      }
    }

    return {
      total,
      caracteresPromedio: Math.round((suma / total) * 100) / 100,
      caracteresMin: minimo,
      caracteresMax: maximo,
      conAnio,
      sinAnio,
    };
  }, [articulos]);
}

