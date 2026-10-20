// Vista Req. 1 — Similitud textual: selección de artículos y algoritmos, mapas de calor por
// algoritmo, comparación clásico vs IA y panel paso a paso para un par elegido.
import { useEffect, useMemo, useState } from "react";
import { api, type ArticuloRef, type ClaveSimilitud, type RespuestaSimilitud } from "../api";
import { BarrasHorizontales } from "../componentes/graficos/BarrasHorizontales";
import { LeyendaCalor, MapaCalor } from "../componentes/graficos/MapaCalor";
import { Boton } from "../componentes/ui/Boton";
import { Dato, formato, formatoMs } from "../componentes/ui/Dato";
import { EncabezadoVista } from "../componentes/ui/EncabezadoVista";
import { Aparecer, Cargando, MensajeError } from "../componentes/ui/Estado";
import { Info } from "../componentes/ui/Icono";
import { Pestanas } from "../componentes/ui/Pestanas";
import { Chips, type Opcion } from "../componentes/ui/Selector";
import { Tabla, type Columna } from "../componentes/ui/Tabla";
import { Tarjeta } from "../componentes/ui/Tarjeta";
import { useEjecucion, usePeticion } from "../hooks/usePeticion";
import { PasoSimilitud } from "./PasoSimilitud";

const CLASICOS: Opcion<ClaveSimilitud>[] = [
  { valor: "levenshtein", etiqueta: "Levenshtein", detalle: "Distancia de edición entre secuencias de palabras" },
  { valor: "needleman_wunsch", etiqueta: "Needleman-Wunsch", detalle: "Alineamiento global con match/mismatch/gap" },
  { valor: "coseno_tfidf", etiqueta: "Coseno TF-IDF", detalle: "Ángulo entre vectores TF-IDF" },
  { valor: "jaccard", etiqueta: "Jaccard", detalle: "Intersección sobre unión de términos" },
];
const IA: Opcion<ClaveSimilitud>[] = [
  { valor: "word2vec", etiqueta: "Word2Vec", detalle: "Promedio de embeddings de palabras" },
  { valor: "sbert", etiqueta: "Sentence-BERT", detalle: "Embedding de oraciones (all-MiniLM-L6-v2)" },
];

const ORDEN = [...CLASICOS, ...IA].map((o) => o.valor);

export function VistaSimilitud() {
  const corpus = usePeticion((senal) => api.articulos(senal), []);
  const [ids, setIds] = useState<number[]>([1, 2, 7, 11, 15]);
  const [algoritmos, setAlgoritmos] = useState<ClaveSimilitud[]>(["levenshtein", "coseno_tfidf", "jaccard", "sbert"]);
  const { datos: resultado, cargando, error, ejecutar, enCurso } = useEjecucion<RespuestaSimilitud>();
  const [activo, setActivo] = useState<ClaveSimilitud | null>(null);
  const [par, setPar] = useState<[number, number] | null>(null);

  // Con los 20 artículos el backend tarda ~2 s: mientras tanto el botón queda deshabilitado
  // y se ignoran clics repetidos, para no lanzar el mismo cálculo dos veces.
  const calcular = () => {
    if (enCurso()) return;
    void ejecutar(
      // Orden canónico (clásicos y luego IA) sin importar el orden en que se marcaron los chips.
      (senal) => api.similitud(ids, ORDEN.filter((c) => algoritmos.includes(c)), senal),
      (r) => {
        // Se conserva el algoritmo activo si sigue en la respuesta.
        setActivo((previo) => (r.resultados.some((x) => x.clave === previo) ? previo : r.resultados[0]?.clave ?? null));
        setPar(r.articulos.length >= 2 ? [0, 1] : null);
      },
    );
  };

  // Primer cálculo automático con la selección por defecto.
  useEffect(() => {
    void calcular();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const alternarId = (id: number) => setIds((v) => (v.includes(id) ? v.filter((x) => x !== id) : [...v, id].sort((a, b) => a - b)));
  const actual = resultado?.resultados.find((r) => r.clave === activo) ?? null;
  const valido = ids.length >= 2 && algoritmos.length >= 1;

  return (
    <div className="vista">
      <EncabezadoVista antetitulo="Requerimiento 1" titulo="Similitud textual">
        <p>
          Cuatro algoritmos clásicos (edición, alineamiento, vectorial y de conjuntos) frente a dos modelos de IA basados en
          embeddings. Elija los artículos y los algoritmos; pulse una celda del mapa para ver el cálculo paso a paso.
        </p>
      </EncabezadoVista>

      <div className="rejilla-controles">
        <Tarjeta titulo="Artículos" descripcion={`${ids.length} seleccionados · mínimo 2`} acciones={
          <>
            <Boton tamano="pequeno" variante="fantasma" onClick={() => setIds([])}>
              Limpiar
            </Boton>
          </>
        }>
          {corpus.error && <MensajeError mensaje={corpus.error} reintentar={corpus.recargar} />}
          {corpus.cargando && <Cargando lineas={6} />}
          <ul className="lista-seleccion">
            {corpus.datos?.map((a) => (
              <li key={a.id}>
                <label className={ids.includes(a.id) ? "es-activo" : ""}>
                  <input type="checkbox" checked={ids.includes(a.id)} onChange={() => alternarId(a.id)} />
                  <span className="mono tenue">#{a.id}</span>
                  <span className="recortar">{a.titulo}</span>
                </label>
              </li>
            ))}
          </ul>
        </Tarjeta>

        <Tarjeta titulo="Algoritmos">
          <h4 className="rotulo">Clásicos</h4>
          <Chips etiqueta="Algoritmos clásicos" opciones={CLASICOS} valores={algoritmos} onCambio={setAlgoritmos} />
          <h4 className="rotulo">Inteligencia artificial</h4>
          <Chips etiqueta="Algoritmos de IA" opciones={IA} valores={algoritmos} onCambio={setAlgoritmos} />
          <div className="acciones-formulario">
            <Boton variante="primario" onClick={calcular} disabled={!valido || cargando}>
              {cargando ? "Calculando…" : "Calcular similitud"}
            </Boton>
            {!valido && <span className="tenue texto-pequeno">Seleccione al menos 2 artículos y 1 algoritmo.</span>}
          </div>
        </Tarjeta>
      </div>

      {error && <MensajeError mensaje={error} reintentar={valido ? calcular : undefined} />}
      {resultado?.avisos?.map((a) => (
        <div className="aviso" key={a}>
          <Info size={18} aria-hidden />
          <p>{a}</p>
        </div>
      ))}
      {cargando && (
        <p className="estado-carga" role="status">
          <span className="estado-carga__punto" aria-hidden />
          Calculando {algoritmos.length} {algoritmos.length === 1 ? "algoritmo" : "algoritmos"} sobre {ids.length} artículos
          {ids.length > 10 ? " (puede tardar unos segundos)" : ""}…
        </p>
      )}
      {cargando && !resultado && <Cargando alto={320} />}

      {resultado && actual && (
        <Aparecer className={cargando ? "es-recargando" : ""}>
          <Tarjeta
            titulo="Matrices de similitud"
            descripcion="Cada celda es la similitud en [0, 1] entre dos artículos. Pulse una celda para ver la traza."
            acciones={<LeyendaCalor />}
          >
            <Pestanas
              etiqueta="Algoritmo"
              activa={actual.clave}
              onCambio={setActivo}
              pestanas={resultado.resultados.map((r) => ({
                clave: r.clave,
                etiqueta: (
                  <>
                    {r.nombre}
                    {r.tipo === "ia" && <span className="insignia">IA</span>}
                  </>
                ),
              }))}
            />
            <div className="mapa-y-datos">
              <MapaCalor
                titulo={`Matriz de similitud ${actual.nombre}`}
                articulos={resultado.articulos}
                matriz={actual.matriz}
                seleccion={par}
                onSeleccionar={(i, j) => setPar([i, j])}
              />
              <div className="columna-datos">
                <Dato rotulo="Tiempo de cálculo" valor={formatoMs(actual.tiempo_ms)} />
                <Dato rotulo="Similitud media" valor={formato(promedioFuera(actual.matriz))} />
                <ParExtremo articulos={resultado.articulos} matriz={actual.matriz} />
              </div>
            </div>
          </Tarjeta>

          {par && (
            <PasoSimilitud
              key={`${actual.clave}-${resultado.articulos[par[0]].id}-${resultado.articulos[par[1]].id}`}
              algoritmo={actual.clave}
              a={resultado.articulos[par[0]]}
              b={resultado.articulos[par[1]]}
            />
          )}

          <Comparacion resultado={resultado} />
        </Aparecer>
      )}
    </div>
  );
}

function promedioFuera(m: number[][]): number {
  let s = 0;
  let n = 0;
  m.forEach((f, i) => f.forEach((v, j) => i < j && ((s += v), n++)));
  return n ? s / n : 0;
}

function ParExtremo({ articulos, matriz }: { articulos: ArticuloRef[]; matriz: number[][] }) {
  let mejor = { i: 0, j: 1, v: -1 };
  matriz.forEach((f, i) => f.forEach((v, j) => i < j && v > mejor.v && (mejor = { i, j, v })));
  if (mejor.v < 0) return null;
  return <Dato rotulo="Par más similar" valor={`#${articulos[mejor.i].id} · #${articulos[mejor.j].id}`} nota={formato(mejor.v)} />;
}

/** Tabla por pares con todos los algoritmos, promedios por familia y tiempos. */
function Comparacion({ resultado }: { resultado: RespuestaSimilitud }) {
  const { articulos, resultados } = resultado;
  const pares = useMemo(() => {
    const l: { i: number; j: number }[] = [];
    for (let i = 0; i < articulos.length; i++) for (let j = i + 1; j < articulos.length; j++) l.push({ i, j });
    return l;
  }, [articulos]);

  const media = (tipo: "clasico" | "ia", i: number, j: number) => {
    const rs = resultados.filter((r) => r.tipo === tipo);
    return rs.length ? rs.reduce((s, r) => s + r.matriz[i][j], 0) / rs.length : null;
  };
  const hayIa = resultados.some((r) => r.tipo === "ia");
  const hayClasico = resultados.some((r) => r.tipo === "clasico");

  const columnas: Columna<{ i: number; j: number }>[] = [
    { clave: "par", titulo: "Par", celda: (p) => <span className="mono">#{articulos[p.i].id} – #{articulos[p.j].id}</span> },
    ...resultados.map((r) => ({
      clave: r.clave,
      titulo: r.nombre,
      numerica: true,
      celda: (p: { i: number; j: number }) => <CeldaValor v={r.matriz[p.i][p.j]} />,
    })),
    ...(hayClasico && hayIa
      ? [
          { clave: "mc", titulo: "Media clásicos", numerica: true, celda: (p: { i: number; j: number }) => formato(media("clasico", p.i, p.j)!) },
          { clave: "mi", titulo: "Media IA", numerica: true, celda: (p: { i: number; j: number }) => formato(media("ia", p.i, p.j)!) },
          {
            clave: "dif",
            titulo: "IA − clásicos",
            numerica: true,
            celda: (p: { i: number; j: number }) => {
              const d = media("ia", p.i, p.j)! - media("clasico", p.i, p.j)!;
              return <span className={d > 0 ? "texto-acento" : ""}>{(d > 0 ? "+" : "") + d.toFixed(3)}</span>;
            },
          },
        ]
      : []),
  ];

  return (
    <div className="rejilla-dos">
      <Tarjeta
        titulo="Clásicos frente a IA"
        descripcion={
          hayClasico && hayIa
            ? "Los modelos de embeddings tienden a puntuar más alto: capturan cercanía semántica aunque las palabras no coincidan."
            : "Seleccione algoritmos de ambas familias para compararlas."
        }
      >
        <Tabla titulo="Similitud por par y algoritmo" columnas={columnas} filas={pares} claveFila={(p) => `${p.i}-${p.j}`} densa />
      </Tarjeta>
      <Tarjeta titulo="Tiempo de ejecución" descripcion="Cálculo de la matriz completa, en milisegundos.">
        <BarrasHorizontales
          titulo="Tiempo por algoritmo"
          formato={formatoMs}
          barras={resultados.map((r) => ({ clave: r.clave, etiqueta: r.nombre, valor: r.tiempo_ms, destacada: r.tipo === "ia" }))}
        />
        <p className="nota-grafico">
          <span className="muestra muestra--acento" /> IA <span className="muestra" /> Clásico
        </p>
      </Tarjeta>
    </div>
  );
}

function CeldaValor({ v }: { v: number }) {
  return (
    <span className="celda-valor">
      <span className="celda-valor__barra" style={{ transform: `scaleX(${Math.max(0, Math.min(1, v))})` }} aria-hidden />
      {v.toFixed(3)}
    </span>
  );
}

