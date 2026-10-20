// Vista Req. 2 — Clustering jerárquico: tres dendrogramas (single, complete, average),
// selector de representación, métricas Silhouette y correlación cofenética.
import { useState } from "react";
import { api, type MetodoClustering, type Representacion } from "../api";
import { Dendrograma } from "../componentes/graficos/Dendrograma";
import { Dato, formato, formatoMs } from "../componentes/ui/Dato";
import { EncabezadoVista } from "../componentes/ui/EncabezadoVista";
import { Aparecer, Cargando, MensajeError } from "../componentes/ui/Estado";
import { Segmentado } from "../componentes/ui/Selector";
import { Tabla } from "../componentes/ui/Tabla";
import { Tarjeta } from "../componentes/ui/Tarjeta";
import { usePeticion } from "../hooks/usePeticion";

// La Silhouette necesita grupos: el backend corta el árbol en este número fijo de grupos.
const GRUPOS_SILHOUETTE = 4;

const DESCRIPCION: Record<string, string> = {
  single: "Distancia mínima entre miembros: tiende a encadenar grupos.",
  complete: "Distancia máxima entre miembros: grupos compactos.",
  average: "Promedio de todas las distancias (UPGMA): equilibrio entre ambos.",
};

export function VistaClustering() {
  const [representacion, setRepresentacion] = useState<Representacion>("tfidf");
  const { datos, cargando, error, recargar } = usePeticion((senal) => api.clustering(representacion, GRUPOS_SILHOUETTE, senal), [representacion]);

  return (
    <div className="vista">
      <EncabezadoVista antetitulo="Requerimiento 2" titulo="Agrupamiento jerárquico">
        <p>
          Se construye la matriz de distancias (1 − coseno) y se fusionan iterativamente los grupos más cercanos con tres
          criterios de enlace. La correlación cofenética mide cuán fielmente el árbol preserva las distancias originales.
        </p>
      </EncabezadoVista>

      <div className="barra-herramientas">
        <div className="control">
          <span className="rotulo">Representación</span>
          <Segmentado
            etiqueta="Representación"
            valor={representacion}
            onCambio={setRepresentacion}
            opciones={[
              { valor: "tfidf", etiqueta: "TF-IDF" },
              { valor: "sbert", etiqueta: "SBERT" },
            ]}
          />
        </div>
      </div>

      {error && <MensajeError mensaje={error} reintentar={recargar} />}
      {cargando && !datos && <Cargando alto={360} />}

      {datos && (
        <Aparecer className={cargando ? "es-recargando" : ""}>
          <Tarjeta titulo="Comparación de métodos" descripcion={`Criterio: ${datos.criterio}.`}>
            <Tabla
              titulo="Métricas por método de enlace"
              filas={datos.metodos}
              claveFila={(m) => m.clave}
              resaltar={(m) => m.clave === datos.mejor_metodo}
              columnas={[
                {
                  clave: "n",
                  titulo: "Método",
                  celda: (m) => (
                    <>
                      {m.nombre} {m.clave === datos.mejor_metodo && <span className="insignia insignia--acento">Mejor</span>}
                    </>
                  ),
                },
                { clave: "c", titulo: "Corr. cofenética", numerica: true, celda: (m) => <Metrica v={m.correlacion_cofenetica} max={maximo(datos.metodos, "correlacion_cofenetica")} /> },
                { clave: "s", titulo: "Silhouette", numerica: true, celda: (m) => <Metrica v={m.silhouette} max={maximo(datos.metodos, "silhouette")} /> },
                { clave: "t", titulo: "Tiempo", numerica: true, celda: (m) => formatoMs(m.tiempo_ms) },
              ]}
            />
          </Tarjeta>

          <div className="dendrogramas">
            {datos.metodos.map((m) => (
              <Tarjeta
                key={m.clave}
                className={m.clave === datos.mejor_metodo ? "tarjeta--destacada" : ""}
                titulo={
                  <>
                    {m.nombre} {m.clave === datos.mejor_metodo && <span className="insignia insignia--acento">Mejor método</span>}
                  </>
                }
                descripcion={DESCRIPCION[m.clave]}
                acciones={
                  <div className="fila-datos fila-datos--mini">
                    <Dato rotulo="Cofenética" valor={formato(m.correlacion_cofenetica)} />
                    <Dato rotulo="Silhouette" valor={formato(m.silhouette)} />
                  </div>
                }
              >
                <Dendrograma titulo={`Dendrograma ${m.nombre}`} arbol={m.arbol} />
                <details className="desplegable">
                  <summary>Secuencia de fusiones ({m.fusiones.length})</summary>
                  <Tabla
                    titulo={`Fusiones ${m.nombre}`}
                    densa
                    filas={m.fusiones}
                    claveFila={(f) => f.paso}
                    columnas={[
                      { clave: "p", titulo: "Paso", numerica: true, celda: (f) => f.paso },
                      { clave: "a", titulo: "Grupo A", numerica: true, celda: (f) => etiquetaNodo(f.a, datos.articulos.length, datos.articulos) },
                      { clave: "b", titulo: "Grupo B", numerica: true, celda: (f) => etiquetaNodo(f.b, datos.articulos.length, datos.articulos) },
                      { clave: "nuevo", titulo: "Nuevo", numerica: true, celda: (f) => `G${f.nuevo}` },
                      { clave: "d", titulo: "Distancia", numerica: true, celda: (f) => f.distancia.toFixed(4) },
                      { clave: "t", titulo: "Tamaño", numerica: true, celda: (f) => f.tamano },
                    ]}
                  />
                </details>
              </Tarjeta>
            ))}
          </div>
          <p className="nota-grafico">Pase el cursor sobre una hoja para ver el título del artículo.</p>
        </Aparecer>
      )}
    </div>
  );
}

function maximo(metodos: MetodoClustering[], campo: "silhouette" | "correlacion_cofenetica") {
  return Math.max(...metodos.map((m) => m[campo]));
}

// Los ids < n son hojas (artículos); el resto son grupos formados en fusiones previas.
function etiquetaNodo(id: number, n: number, articulos: { id: number }[]) {
  return id < n ? `#${articulos[id]?.id ?? id}` : `G${id}`;
}

function Metrica({ v, max }: { v: number; max: number }) {
  return <span className={v === max ? "texto-acento negrita" : ""}>{v.toFixed(4)}</span>;
}
