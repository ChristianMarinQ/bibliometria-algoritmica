// Dendrograma horizontal con D3: raíz a la izquierda, hojas a la derecha.
// El eje x es la distancia de fusión: entre más a la derecha se unen dos ramas, más parecidas son.
import * as d3 from "d3";
import { motion } from "motion/react";
import { useMemo, useState } from "react";
import type { NodoArbol } from "../../api";
import { useMedida } from "../../hooks/useMedida";
import { Tooltip, type PosTooltip } from "../ui/Tooltip";

interface Props {
  arbol: NodoArbol;
  titulo: string;
}

const ALTO_HOJA = 20;
const MARGEN = { arriba: 12, abajo: 28, izq: 8, der: 44 };

export function Dendrograma({ arbol, titulo }: Props) {
  const [ref, ancho] = useMedida<HTMLDivElement>();
  const [tip, setTip] = useState<PosTooltip | null>(null);
  const [hojaActiva, setHojaActiva] = useState<number | null>(null);

  const raiz = useMemo(() => d3.hierarchy<NodoArbol>(arbol, (d) => d.hijos), [arbol]);
  const hojas = raiz.leaves();
  const alto = hojas.length * ALTO_HOJA + MARGEN.arriba + MARGEN.abajo;
  const anchoUtil = Math.max(160, (ancho || 320) - MARGEN.izq - MARGEN.der);

  const x = d3.scaleLinear().domain([raiz.data.distancia || 1, 0]).range([MARGEN.izq, MARGEN.izq + anchoUtil]);

  // Posición vertical: hojas en orden de recorrido, nodos internos en el punto medio.
  const posY = new Map<d3.HierarchyNode<NodoArbol>, number>();
  hojas.forEach((h, i) => posY.set(h, MARGEN.arriba + i * ALTO_HOJA + ALTO_HOJA / 2));
  raiz.eachAfter((n) => {
    if (n.children) posY.set(n, d3.mean(n.children, (c) => posY.get(c)!)!);
  });

  // Ancestros de la hoja activa para resaltar su recorrido.
  const activos = new Set<d3.HierarchyNode<NodoArbol>>();
  if (hojaActiva !== null) hojas.find((h) => h.data.id === hojaActiva)?.ancestors().forEach((a) => activos.add(a));

  const ticks = x.ticks(5);

  return (
    <div ref={ref} className="grafico dendrograma">
      <svg width={MARGEN.izq + anchoUtil + MARGEN.der} height={alto} role="img" aria-label={titulo}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={MARGEN.arriba} y2={alto - MARGEN.abajo} className="rejilla" />
            <text x={x(t)} y={alto - 10} textAnchor="middle" className="eje-texto">
              {t.toFixed(2)}
            </text>
          </g>
        ))}
        <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} key={arbol.id}>
          {raiz.descendants().flatMap((n) =>
            (n.children ?? []).map((c) => (
              <path
                key={`${n.data.id}-${c.data.id}`}
                d={`M${x(n.data.distancia)},${posY.get(n)} V${posY.get(c)} H${x(c.data.distancia)}`}
                fill="none"
                stroke={activos.has(c) ? "var(--acento)" : "var(--tinta-2)"}
                strokeWidth={activos.has(c) ? 2.25 : 1.25}
                opacity={hojaActiva !== null && !activos.has(c) ? 0.35 : 1}
              />
            )),
          )}
        </motion.g>
        {hojas.map((h) => (
          <g
            key={h.data.id}
            className="dendrograma__hoja"
            onMouseEnter={() => {
              setHojaActiva(h.data.id);
              setTip({
                x: x(0) - 90,
                y: posY.get(h)! - 6,
                contenido: (
                  <>
                    <span className="tooltip__valor">Artículo #{h.data.articulo_id}</span>
                    <span>{h.data.titulo}</span>
                  </>
                ),
              });
            }}
            onMouseLeave={() => {
              setHojaActiva(null);
              setTip(null);
            }}
          >
            <rect x={x(0)} y={posY.get(h)! - ALTO_HOJA / 2} width={MARGEN.der} height={ALTO_HOJA} fill="transparent" />
            <circle cx={x(0)} cy={posY.get(h)} r={2.5} fill="var(--acento)" />
            <text x={x(0) + 8} y={posY.get(h)} dy="0.35em" className={`eje-texto ${hojaActiva === h.data.id ? "eje-texto--acento" : ""}`}>
              #{h.data.articulo_id}
            </text>
          </g>
        ))}
      </svg>
      <Tooltip pos={tip} />
    </div>
  );
}
