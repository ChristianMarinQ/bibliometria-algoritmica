// Mapa de calor de una matriz de similitud simétrica. Al pulsar una celda se elige el par.
import { useState, type KeyboardEvent } from "react";
import type { ArticuloRef } from "../../api";
import { useMedida } from "../../hooks/useMedida";
import { Tooltip, type PosTooltip } from "../ui/Tooltip";

interface Props {
  articulos: ArticuloRef[];
  matriz: number[][];
  seleccion?: [number, number] | null;
  onSeleccionar?: (i: number, j: number) => void;
  titulo: string;
}

const MARGEN = 40; // espacio para las etiquetas de filas y columnas

export function MapaCalor({ articulos, matriz, seleccion, onSeleccionar, titulo }: Props) {
  const [ref, ancho] = useMedida<HTMLDivElement>();
  const [tip, setTip] = useState<PosTooltip | null>(null);
  const n = articulos.length;
  // Celdas entre 26 y 64 px; si no caben, el contenedor tiene scroll propio.
  const celda = Math.max(26, Math.min(64, Math.floor(((ancho || 320) - MARGEN) / n)));
  const lado = MARGEN + celda * n;
  const mostrarValor = celda >= 36;

  return (
    <div ref={ref} className="grafico mapa-calor">
      <svg width={lado} height={lado} role={onSeleccionar ? "group" : "img"} aria-label={titulo}>
        {articulos.map((a, k) => (
          <g key={a.id}>
            <text x={MARGEN + k * celda + celda / 2} y={MARGEN - 10} textAnchor="middle" className="eje-texto">
              #{a.id}
            </text>
            <text x={MARGEN - 8} y={MARGEN + k * celda + celda / 2} dy="0.35em" textAnchor="end" className="eje-texto">
              #{a.id}
            </text>
          </g>
        ))}
        {matriz.map((fila, i) =>
          fila.map((v, j) => {
            const elegida = seleccion && ((seleccion[0] === i && seleccion[1] === j) || (seleccion[0] === j && seleccion[1] === i));
            const diagonal = i === j;
            // Solo el triángulo superior entra en el orden de tabulación (la matriz es simétrica).
            const enfocable = Boolean(onSeleccionar) && i < j;
            const mostrarTip = () =>
                  setTip({
                    x: MARGEN + j * celda + celda / 2,
                    y: MARGEN + i * celda,
                    contenido: (
                      <>
                        <span className="tooltip__valor">{v.toFixed(4)}</span>
                        <span>#{articulos[i].id} {articulos[i].titulo}</span>
                        <span>#{articulos[j].id} {articulos[j].titulo}</span>
                      </>
                    ),
                  });
            return (
              <g
                key={`${i}-${j}`}
                className={`mapa-calor__celda ${diagonal ? "" : "es-pulsable"}`}
                onClick={() => !diagonal && onSeleccionar?.(i, j)}
                onMouseEnter={mostrarTip}
                onMouseLeave={() => setTip(null)}
                {...(enfocable && {
                  tabIndex: 0,
                  role: "button",
                  "aria-label": `Ver traza de #${articulos[i].id} y #${articulos[j].id}: similitud ${v.toFixed(3)}`,
                  "aria-pressed": Boolean(elegida),
                  onFocus: mostrarTip,
                  onBlur: () => setTip(null),
                  onKeyDown: (e: KeyboardEvent<SVGGElement>) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSeleccionar?.(i, j);
                    }
                  },
                })}
              >
                <rect
                  x={MARGEN + j * celda + 1}
                  y={MARGEN + i * celda + 1}
                  width={celda - 2}
                  height={celda - 2}
                  rx={2}
                  style={{
                    fill: diagonal
                      ? "var(--superficie-2)"
                      : `color-mix(in oklab, var(--acento) ${Math.round(Math.max(0, Math.min(1, v)) * 100)}%, var(--superficie))`,
                  }}
                  className={elegida ? "es-elegida" : ""}
                />
                {mostrarValor && (
                  <text
                    x={MARGEN + j * celda + celda / 2}
                    y={MARGEN + i * celda + celda / 2}
                    dy="0.35em"
                    textAnchor="middle"
                    className={`mapa-calor__valor ${diagonal ? "" : nivelTexto(v)}`}
                  >
                    {diagonal ? "—" : v.toFixed(2)}
                  </text>
                )}
              </g>
            );
          }),
        )}
      </svg>
      <Tooltip pos={tip} />
    </div>
  );
}

// Clase del texto según la intensidad: los colores por tema están en tokens.css (--calor-texto-*).
function nivelTexto(v: number): string {
  if (v > 0.85) return "es-alto";
  if (v > 0.75) return "es-medio";
  return "";
}

/** Leyenda de la escala de color (0 → 1). */
export function LeyendaCalor() {
  return (
    <div className="leyenda-calor" aria-hidden>
      <span>0</span>
      <span className="leyenda-calor__barra" />
      <span>1</span>
    </div>
  );
}
