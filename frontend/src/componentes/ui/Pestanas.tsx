// Pestañas con subrayado que se desplaza entre opciones (layoutId).
import { motion } from "motion/react";
import { useId, type ReactNode } from "react";

export interface Pestana<T extends string> {
  clave: T;
  etiqueta: ReactNode;
}

interface Props<T extends string> {
  pestanas: Pestana<T>[];
  activa: T;
  onCambio: (c: T) => void;
  etiqueta: string;
}

export function Pestanas<T extends string>({ pestanas, activa, onCambio, etiqueta }: Props<T>) {
  const id = useId();
  return (
    <div className="pestanas" role="tablist" aria-label={etiqueta}>
      {pestanas.map((p) => {
        const es = p.clave === activa;
        return (
          <button
            key={p.clave}
            type="button"
            role="tab"
            aria-selected={es}
            className={`pestana ${es ? "es-activa" : ""}`}
            onClick={() => onCambio(p.clave)}
          >
            {p.etiqueta}
            {es && (
              <motion.span
                layoutId={`pestana-${id}`}
                className="pestana__subrayado"
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
