// Visualizador de la traza de búsqueda: el texto como fila de celdas, el patrón deslizándose
// por cada alineación, comparaciones coloreadas, desplazamiento y motivo, y tablas auxiliares.
import { Pause, Play } from "lucide";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useMemo, useRef, type KeyboardEvent } from "react";
import type { TrazaBusqueda } from "../api";
import { Boton } from "../componentes/ui/Boton";
import { Dato, entero } from "../componentes/ui/Dato";
import { ChevronLeft, ChevronRight, IconoMorph, SkipBack } from "../componentes/ui/Icono";
import { useReproductor } from "../hooks/useReproductor";

const CELDA = 22; // ancho de cada carácter en píxeles

export function VisualizadorTraza({ traza }: { traza: TrazaBusqueda }) {
  const { pasos, texto, patron } = traza;
  const r = useReproductor(pasos.length);
  const reducido = useReducedMotion();
  const desdeTeclado = useRef(false);
  const pista = useRef<HTMLDivElement>(null);
  const actual = pasos[r.paso];

  // Comparaciones del paso actual indexadas por posición del texto y del patrón.
  const { porTexto, porPatron } = useMemo(() => {
    const t = new Map<number, boolean>();
    const p = new Map<number, boolean>();
    actual?.comparaciones.forEach((c) => {
      t.set(c.i, c.igual);
      p.set(c.j, c.igual);
    });
    return { porTexto: t, porPatron: p };
  }, [actual]);

  // Coincidencias halladas hasta el paso actual (se subrayan en el texto).
  const halladas = useMemo(() => {
    const s = new Set<number>();
    pasos.slice(0, r.paso + 1).forEach((p) => {
      if (p.coincidencia) for (let k = 0; k < patron.length; k++) s.add(p.alineacion + k);
    });
    return s;
  }, [pasos, r.paso, patron.length]);

  const comparacionesAcumuladas = useMemo(
    () => pasos.slice(0, r.paso + 1).reduce((s, p) => s + p.comparaciones.length, 0),
    [pasos, r.paso],
  );

  // Mantener la ventana visible: desplazamiento del contenedor con scroll propio.
  useEffect(() => {
    const el = pista.current;
    if (!el || !actual) return;
    const objetivo = actual.alineacion * CELDA - el.clientWidth / 3;
    el.scrollTo({ left: Math.max(0, objetivo), behavior: reducido || desdeTeclado.current ? "auto" : "smooth" });
  }, [actual, reducido]);

  const alTeclear = (e: KeyboardEvent) => {
    // Los controles internos conservan su comportamiento nativo: el deslizador usa sus flechas
    // y los botones se activan con espacio (si no, un mismo espacio actuaría dos veces).
    const objetivo = e.target as HTMLElement;
    if (objetivo !== e.currentTarget) {
      if (objetivo.closest("input, select")) return;
      if (e.key === " " && objetivo.closest("button, summary, a")) return;
    }
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      desdeTeclado.current = true; // sin animación en acciones repetitivas de teclado
      if (e.key === "ArrowRight") r.siguiente();
      else r.anterior();
    } else if (e.key === " ") {
      e.preventDefault();
      desdeTeclado.current = false;
      r.alternar();
    }
  };
  const conRaton = (fn: () => void) => () => {
    desdeTeclado.current = false;
    fn();
  };

  if (!actual) return <p className="tenue">La traza no tiene pasos (¿el patrón es más largo que el texto?).</p>;
  const animar = !reducido && !desdeTeclado.current;

  return (
    <div className="visualizador" tabIndex={0} onKeyDown={alTeclear} aria-label="Visualizador de la traza; use flechas para avanzar">
      <div className="visualizador__pista" ref={pista}>
        <div className="visualizador__lienzo" style={{ width: texto.length * CELDA + CELDA * 2 }}>
          <div className="visualizador__indices" aria-hidden>
            {Array.from(texto, (_, i) =>
              i % 10 === 0 ? (
                <span key={i} style={{ left: i * CELDA }}>
                  {i}
                </span>
              ) : null,
            )}
          </div>
          <div className="visualizador__texto">
            {Array.from(texto, (c, i) => {
              const comp = porTexto.get(i);
              const enVentana = i >= actual.alineacion && i < actual.alineacion + patron.length;
              return (
                <span
                  key={i}
                  className={`celda ${enVentana ? "es-ventana" : ""} ${comp === true ? "es-igual" : comp === false ? "es-distinta" : ""} ${halladas.has(i) ? "es-hallada" : ""}`}
                >
                  {c === " " ? "·" : c}
                </span>
              );
            })}
          </div>
          <motion.div
            className="visualizador__patron"
            animate={{ x: actual.alineacion * CELDA }}
            transition={animar ? { type: "spring", stiffness: 380, damping: 34 } : { duration: 0 }}
          >
            {Array.from(patron, (c, j) => {
              const comp = porPatron.get(j);
              return (
                <span key={j} className={`celda celda--patron ${comp === true ? "es-igual" : comp === false ? "es-distinta" : ""}`}>
                  {c === " " ? "·" : c}
                </span>
              );
            })}
          </motion.div>
        </div>
      </div>

      <div className="visualizador__controles">
        <Boton variante="fantasma" icono={<SkipBack size={16} />} aria-label="Ir al inicio" onClick={conRaton(() => r.ir(0))} />
        <Boton variante="fantasma" icono={<ChevronLeft size={18} />} aria-label="Paso anterior" onClick={conRaton(r.anterior)} disabled={r.paso === 0} />
        <Boton
          variante="primario"
          icono={<IconoMorph icono={r.reproduciendo ? Pause : Play} tamano={16} />}
          aria-label={r.reproduciendo ? "Pausar" : "Reproducir"}
          onClick={conRaton(r.alternar)}
        />
        <Boton variante="fantasma" icono={<ChevronRight size={18} />} aria-label="Paso siguiente" onClick={conRaton(r.siguiente)} disabled={r.paso >= pasos.length - 1} />
        <input
          className="deslizador"
          type="range"
          min={0}
          max={pasos.length - 1}
          value={r.paso}
          onChange={(e) => {
            desdeTeclado.current = true;
            r.ir(Number(e.target.value));
          }}
          aria-label="Paso de la traza"
        />
        <span className="mono texto-pequeno visualizador__contador">
          {r.paso + 1} / {pasos.length}
        </span>
      </div>

      <div className="visualizador__estado">
        <div className="fila-datos fila-datos--compacta">
          <Dato rotulo="Alineación" valor={actual.alineacion} />
          <Dato rotulo="Comparaciones (paso)" valor={actual.comparaciones.length} nota={`acumuladas ${entero(comparacionesAcumuladas)} de ${entero(traza.total_comparaciones)}`} />
          <Dato rotulo="Desplazamiento" valor={`+${actual.desplazamiento}`} />
          {actual.hash_ventana !== null && <Dato rotulo="Hash ventana" valor={actual.hash_ventana} />}
          <Dato rotulo="Resultado" valor={actual.coincidencia ? "Coincidencia" : actual.colision ? "Colisión" : "Sin coincidencia"} destacado={actual.coincidencia || actual.colision} />
        </div>
        <p className="motivo">
          <span className="rotulo">Motivo</span>
          {actual.motivo}
        </p>
        {actual.calculo_hash && (
          <p className="motivo">
            <span className="rotulo">Hash rodante</span>
            <code>{actual.calculo_hash}</code>
          </p>
        )}
      </div>

      <div className="leyenda-celdas texto-pequeno">
        <span><span className="celda celda--mini es-igual" /> igual</span>
        <span><span className="celda celda--mini es-distinta" /> distinta</span>
        <span><span className="celda celda--mini es-ventana" /> ventana</span>
        <span><span className="celda celda--mini es-hallada" /> coincidencia hallada</span>
        <span className="tenue">
          Posiciones en el fragmento: {traza.posiciones.length ? traza.posiciones.join(", ") : "ninguna"}
          {traza.inicio_texto ? ` · el fragmento empieza en el carácter ${traza.inicio_texto} del abstract` : ""}
        </span>
      </div>

      <TablasAuxiliares traza={traza} irA={(p) => { desdeTeclado.current = false; r.ir(p); }} />
    </div>
  );
}

/** Tablas de preprocesamiento según el algoritmo. */
function TablasAuxiliares({ traza, irA }: { traza: TrazaBusqueda; irA: (paso: number) => void }) {
  const p = traza.patron;
  if (traza.clave === "kmp") {
    const pre = traza.preprocesamiento;
    return (
      <div className="auxiliares">
        <h4 className="subtitulo">Tabla LPS (prefijo más largo que también es sufijo)</h4>
        <TablaFilas filas={[["j", Array.from(p, (_, j) => j)], ["P[j]", Array.from(p)], ["LPS[j]", pre.lps]]} />
        <ListaPasos pasos={pre.pasos_lps} />
      </div>
    );
  }
  if (traza.clave === "boyer_moore") {
    const pre = traza.preprocesamiento;
    const entradas = Object.entries(pre.caracter_malo);
    return (
      <div className="auxiliares">
        <h4 className="subtitulo">Carácter malo (última aparición en el patrón)</h4>
        <TablaFilas filas={[["carácter", entradas.map(([c]) => (c === " " ? "·" : c))], ["posición", entradas.map(([, v]) => v)]]} />
        <h4 className="subtitulo">Sufijo bueno (desplazamiento por posición)</h4>
        <TablaFilas
          filas={[
            ["j", pre.sufijo_bueno.map((_, j) => j)],
            ["desplaz.", pre.sufijo_bueno],
            ...(pre.bordes ? ([["borde", pre.bordes]] as [string, (string | number)[]][]) : []),
          ]}
        />
        <ListaPasos pasos={pre.pasos} />
      </div>
    );
  }
  const pre = traza.preprocesamiento;
  const colisiones = traza.pasos.map((x, k) => ({ x, k })).filter(({ x }) => x.colision);
  return (
    <div className="auxiliares">
      <div className="fila-datos fila-datos--compacta">
        <Dato rotulo="Base" valor={pre.base} />
        <Dato rotulo="Módulo q" valor={pre.modulo} />
        <Dato rotulo="h = base^(m−1) mod q" valor={pre.h} />
        <Dato rotulo="Hash del patrón" valor={pre.hash_patron} destacado />
        <Dato rotulo="Colisiones" valor={traza.total_colisiones ?? colisiones.length} />
      </div>
      <ListaPasos pasos={pre.pasos} abierto />
      <h4 className="subtitulo">Hashes por ventana</h4>
      <div className="hashes">
        {traza.pasos.map((x, k) => (
          <button
            type="button"
            key={k}
            className={`hash ${x.hash_ventana === pre.hash_patron ? (x.colision ? "es-colision" : "es-igual") : ""}`}
            onClick={() => irA(k)}
            title={`Ventana ${x.alineacion}: hash ${x.hash_ventana}`}
          >
            <span className="hash__pos">{x.alineacion}</span>
            {x.hash_ventana}
          </button>
        ))}
      </div>
      {colisiones.length > 0 && (
        <p className="texto-pequeno">
          Colisiones (hash igual, texto distinto) en las alineaciones{" "}
          {colisiones.map(({ x, k }, n) => (
            <span key={k}>
              {n > 0 && ", "}
              <button type="button" className="enlace" onClick={() => irA(k)}>
                {x.alineacion}
              </button>
            </span>
          ))}
          .
        </p>
      )}
    </div>
  );
}

function TablaFilas({ filas }: { filas: [string, (string | number)[]][] }) {
  return (
    <div className="tabla-contenedor">
      <table className="tabla tabla--densa tabla--filas">
        <tbody>
          {filas.map(([titulo, valores]) => (
            <tr key={titulo}>
              <th scope="row">{titulo}</th>
              {valores.map((v, k) => (
                <td key={k} className="num mono">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ListaPasos({ pasos, abierto }: { pasos: string[]; abierto?: boolean }) {
  if (!pasos.length) return null;
  return (
    <details className="desplegable" open={abierto}>
      <summary>Pasos del preprocesamiento ({pasos.length})</summary>
      <ol className="pasos pasos--compactos">
        {pasos.map((p, k) => (
          <li key={k}>{p}</li>
        ))}
      </ol>
    </details>
  );
}
