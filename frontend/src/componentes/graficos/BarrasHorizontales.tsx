// Barras horizontales en HTML: la longitud se anima con transform: scaleX (solo transform).
import * as d3 from "d3";
import { motion, useReducedMotion } from "motion/react";

export interface Barra {
  clave: string;
  etiqueta: string;
  valor: number;
  destacada?: boolean;
  nota?: string;
}

interface Props {
  barras: Barra[];
  formato?: (v: number) => string;
  maximo?: number;
  titulo: string;
}

export function BarrasHorizontales({ barras, formato = (v) => String(v), maximo, titulo }: Props) {
  const reducido = useReducedMotion();
  const max = maximo ?? d3.max(barras, (b) => b.valor) ?? 1;
  return (
    <div className="barras" role="list" aria-label={titulo}>
      {barras.map((b, i) => (
        <div className="barras__fila" role="listitem" key={b.clave}>
          <span className="barras__etiqueta" title={b.etiqueta}>
            {b.etiqueta}
          </span>
          <span className="barras__pista">
            <motion.span
              className={`barras__relleno ${b.destacada ? "es-destacada" : ""}`}
              style={{ originX: 0 }}
              initial={reducido ? false : { scaleX: 0 }}
              animate={{ scaleX: max > 0 ? b.valor / max : 0 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1], delay: Math.min(i * 0.02, 0.2) }}
            />
          </span>
          <span className="barras__valor">{formato(b.valor)}</span>
        </div>
      ))}
    </div>
  );
}
