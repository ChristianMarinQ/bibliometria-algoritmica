// Información flotante posicionada dentro de un contenedor relativo.
import { AnimatePresence, motion } from "motion/react";
import type { ReactNode } from "react";

export interface PosTooltip {
  x: number;
  y: number;
  contenido: ReactNode;
}

export function Tooltip({ pos }: { pos: PosTooltip | null }) {
  return (
    <AnimatePresence>
      {pos && (
        <motion.div
          className="tooltip"
          role="tooltip"
          style={{ left: pos.x, top: pos.y }}
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.1 } }}
          transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
        >
          {pos.contenido}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
