// Vista Seguimiento — Ranking de términos: top 15 por Counting, Radix y Bucket Sort,
// tiempos, benchmark con repeticiones y gráfico de escalamiento.
import { useState } from "react";
import { api, type ClaveOrden } from "../api";
import { BarrasHorizontales } from "../componentes/graficos/BarrasHorizontales";
import { GraficoLineas } from "../componentes/graficos/GraficoLineas";
import { Dato, entero, formatoMs } from "../componentes/ui/Dato";
import { EncabezadoVista } from "../componentes/ui/EncabezadoVista";
import { Aparecer, Cargando, MensajeError } from "../componentes/ui/Estado";
import { Pestanas } from "../componentes/ui/Pestanas";
import { Tabla } from "../componentes/ui/Tabla";
import { Tarjeta } from "../componentes/ui/Tarjeta";
import { usePeticion } from "../hooks/usePeticion";

export function VistaRanking() {
  const ranking = usePeticion((senal) => api.ranking(15, senal), []);
  const bench = usePeticion((senal) => api.benchmark(50, senal), []);
  const [activo, setActivo] = useState<ClaveOrden>("counting_sort");
  const datos = ranking.datos;
  const algoritmo = datos?.algoritmos.find((a) => a.clave === activo) ?? datos?.algoritmos[0];

  return (
    <div className="vista">
      <EncabezadoVista antetitulo="Seguimiento" titulo="Ranking de términos">
        <p>
          Las frecuencias de los términos son enteros acotados, así que pueden ordenarse en tiempo lineal sin comparaciones.
          Los tres algoritmos deben producir el mismo ranking estable: frecuencia descendente y, en empate, orden alfabético.
        </p>
      </EncabezadoVista>

      {ranking.error && (
        <MensajeError
          mensaje={ranking.error}
          reintentar={() => {
            // Si falló el ranking, el benchmark (que se muestra dentro) también se reintenta.
            ranking.recargar();
            if (bench.error) bench.recargar();
          }}
        />
      )}
      {ranking.cargando && !datos && <Cargando alto={300} />}

      {datos && algoritmo && (
        <Aparecer>
          <div className="fila-datos">
            <Dato rotulo="Tokens" valor={entero(datos.total_tokens)} />
            <Dato rotulo="Términos distintos (n)" valor={entero(datos.terminos_distintos)} />
            <Dato rotulo="Frecuencia máxima (k)" valor={entero(datos.frecuencia_maxima)} />
            <Dato
              rotulo="Consistencia"
              valor={datos.coinciden ? "Idénticos" : "Difieren"}
              nota={datos.coinciden ? "los tres rankings coinciden" : "revisar estabilidad"}
              destacado={!datos.coinciden}
            />
          </div>

          <Tarjeta
            titulo="Top 15 términos"
            acciones={
              <span className="mono texto-pequeno tenue">
                {algoritmo.complejidad} · {formatoMs(algoritmo.tiempo_ms)}
              </span>
            }
          >
            <Pestanas
              etiqueta="Algoritmo de ordenamiento"
              activa={algoritmo.clave}
              onCambio={setActivo}
              pestanas={datos.algoritmos.map((a) => ({ clave: a.clave, etiqueta: a.nombre }))}
            />
            <div className="rejilla-ranking">
              <Tabla
                titulo={`Top 15 según ${algoritmo.nombre}`}
                densa
                filas={algoritmo.top}
                claveFila={(t) => t.termino}
                columnas={[
                  { clave: "r", titulo: "#", numerica: true, ancho: "3rem", celda: (_, i) => i + 1 },
                  { clave: "t", titulo: "Término", celda: (t) => <span className="mono">{t.termino}</span> },
                  { clave: "f", titulo: "Frecuencia", numerica: true, celda: (t) => t.frecuencia },
                ]}
              />
              <BarrasHorizontales
                key={algoritmo.clave}
                titulo="Frecuencia de los 15 términos principales"
                maximo={datos.frecuencia_maxima}
                barras={algoritmo.top.map((t, i) => ({ clave: t.termino, etiqueta: t.termino, valor: t.frecuencia, destacada: i < 3 }))}
              />
            </div>
          </Tarjeta>

          <div className="rejilla-dos">
            <Tarjeta titulo="Tiempo de una ejecución" descripcion="Ordenar los n términos una vez.">
              <BarrasHorizontales
                titulo="Tiempo por algoritmo"
                formato={formatoMs}
                barras={datos.algoritmos.map((a) => ({
                  clave: a.clave,
                  etiqueta: a.nombre,
                  valor: a.tiempo_ms,
                  destacada: a.tiempo_ms === Math.min(...datos.algoritmos.map((x) => x.tiempo_ms)),
                }))}
              />
            </Tarjeta>
            <Tarjeta
              titulo="Benchmark"
              descripcion={bench.datos ? `${bench.datos.repeticiones} repeticiones sobre n = ${entero(bench.datos.n)} términos.` : "Midiendo…"}
            >
              {bench.error && <MensajeError mensaje={bench.error} reintentar={bench.recargar} />}
              {bench.cargando && !bench.datos && <Cargando lineas={3} />}
              {bench.datos && (
                <Tabla
                  titulo="Resultados del benchmark"
                  densa
                  filas={bench.datos.algoritmos}
                  claveFila={(a) => a.clave}
                  columnas={[
                    { clave: "n", titulo: "Algoritmo", celda: (a) => datos.algoritmos.find((x) => x.clave === a.clave)?.nombre ?? a.clave },
                    { clave: "p", titulo: "Promedio", numerica: true, celda: (a) => formatoMs(a.promedio_ms) },
                    { clave: "mi", titulo: "Mínimo", numerica: true, celda: (a) => formatoMs(a.minimo_ms) },
                    { clave: "ma", titulo: "Máximo", numerica: true, celda: (a) => formatoMs(a.maximo_ms) },
                  ]}
                />
              )}
            </Tarjeta>
          </div>

          {bench.datos && (
            <Tarjeta titulo="Escalamiento" descripcion="La lista se duplica (×1, ×2, ×4, ×8): un crecimiento aproximadamente lineal confirma O(n + k).">
              <GraficoLineas
                titulo="Tiempo frente a tamaño de la entrada"
                etiquetaX="n (términos)"
                etiquetaY="ms"
                series={datos.algoritmos.map((a) => ({
                  clave: a.clave,
                  nombre: a.nombre,
                  puntos: bench.datos!.escalamiento.map((e) => ({ x: e.n, y: e[a.clave] })),
                }))}
              />
            </Tarjeta>
          )}
        </Aparecer>
      )}
    </div>
  );
}
