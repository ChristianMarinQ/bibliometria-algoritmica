// Gráfico de líneas con D3 (escalas y generador de líneas) para el escalamiento del benchmark.
import * as d3 from "d3";
import { useState } from "react";
import { useMedida } from "../../hooks/useMedida";

export interface Serie {
  clave: string;
  nombre: string;
  puntos: { x: number; y: number }[];
}

interface Props {
  series: Serie[];
  etiquetaX: string;
  etiquetaY: string;
  titulo: string;
}

const M = { arriba: 16, der: 16, abajo: 40, izq: 52 };
// Se distinguen las series por tono y por patrón de trazo (accesible sin color).
const ESTILOS = [
  { color: "var(--acento)", trazo: "" },
  { color: "var(--tinta)", trazo: "5 4" },
  { color: "var(--tinta-3)", trazo: "1.5 3.5" },
];

export function GraficoLineas({ series, etiquetaX, etiquetaY, titulo }: Props) {
  const [ref, ancho] = useMedida<HTMLDivElement>();
  const [activa, setActiva] = useState<string | null>(null);
  const w = Math.max(280, ancho || 320);
  const h = 260;
  const todos = series.flatMap((s) => s.puntos);
  const x = d3.scaleLinear().domain([0, d3.max(todos, (p) => p.x) ?? 1]).nice().range([M.izq, w - M.der]);
  const y = d3.scaleLinear().domain([0, d3.max(todos, (p) => p.y) ?? 1]).nice().range([h - M.abajo, M.arriba]);
  const linea = d3.line<{ x: number; y: number }>().x((p) => x(p.x)).y((p) => y(p.y));

  return (
    <div ref={ref} className="grafico">
      <svg width={w} height={h} role="img" aria-label={titulo}>
        {y.ticks(5).map((t) => (
          <g key={`y${t}`}>
            <line x1={M.izq} x2={w - M.der} y1={y(t)} y2={y(t)} className="rejilla" />
            <text x={M.izq - 8} y={y(t)} dy="0.35em" textAnchor="end" className="eje-texto">
              {t.toFixed(2)}
            </text>
          </g>
        ))}
        {x.ticks(Math.max(2, Math.floor(w / 110))).map((t) => (
          <text key={`x${t}`} x={x(t)} y={h - M.abajo + 18} textAnchor="middle" className="eje-texto">
            {d3.format("~s")(t)}
          </text>
        ))}
        <text x={w - M.der} y={h - 4} textAnchor="end" className="eje-texto eje-texto--titulo">
          {etiquetaX}
        </text>
        <text x={M.izq} y={10} className="eje-texto eje-texto--titulo">
          {etiquetaY}
        </text>
        {series.map((s, i) => {
          const e = ESTILOS[i % ESTILOS.length];
          const atenuada = activa !== null && activa !== s.clave;
          return (
            <g key={s.clave} opacity={atenuada ? 0.25 : 1} style={{ transition: "opacity 150ms var(--curva-salida)" }}>
              <path d={linea(s.puntos) ?? ""} fill="none" stroke={e.color} strokeWidth={2} strokeDasharray={e.trazo} />
              {s.puntos.map((p) => (
                <circle key={p.x} cx={x(p.x)} cy={y(p.y)} r={3.5} fill="var(--superficie)" stroke={e.color} strokeWidth={1.75}>
                  <title>{`${s.nombre}: n = ${p.x}, ${p.y.toFixed(3)} ms`}</title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
      <div className="leyenda">
        {series.map((s, i) => (
          <button
            type="button"
            key={s.clave}
            className="leyenda__item"
            onMouseEnter={() => setActiva(s.clave)}
            onMouseLeave={() => setActiva(null)}
            onFocus={() => setActiva(s.clave)}
            onBlur={() => setActiva(null)}
          >
            <svg width="22" height="8" aria-hidden>
              <line x1="0" x2="22" y1="4" y2="4" stroke={ESTILOS[i % 3].color} strokeWidth="2" strokeDasharray={ESTILOS[i % 3].trazo} />
            </svg>
            {s.nombre}
          </button>
        ))}
      </div>
    </div>
  );
}
