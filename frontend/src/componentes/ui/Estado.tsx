// Estados de carga, error y vacío reutilizables, y la entrada animada estándar.
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { Boton } from "./Boton";
import { CircleAlert, RotateCcw } from "./Icono";

export function Cargando({ lineas = 4, alto }: { lineas?: number; alto?: number }) {
  if (alto) return <div className="esqueleto" style={{ height: alto }} aria-busy="true" aria-label="Cargando" />;
  return (
    <div className="esqueleto-lineas" aria-busy="true" aria-label="Cargando">
      {Array.from({ length: lineas }, (_, i) => (
        <div key={i} className="esqueleto" style={{ width: `${92 - ((i * 17) % 40)}%` }} />
      ))}
    </div>
  );
}

export function MensajeError({ mensaje, reintentar }: { mensaje: string; reintentar?: () => void }) {
  return (
    <div className="aviso aviso--error" role="alert">
      <CircleAlert size={18} aria-hidden />
      <div>
        <strong>No se pudo completar la operación.</strong>
        <p>{mensaje}</p>
      </div>
      {reintentar && (
        <Boton tamano="pequeno" variante="fantasma" icono={<RotateCcw size={14} />} onClick={reintentar}>
          Reintentar
        </Boton>
      )}
    </div>
  );
}

export function Vacio({ children }: { children: ReactNode }) {
  return <div className="vacio">{children}</div>;
}

/** Entrada sutil: desplazamiento de 8 px + desvanecido. */
export function Aparecer({ children, retraso = 0, className }: { children: ReactNode; retraso?: number; className?: string }) {
  return (
    <motion.div
      className={`pila ${className ?? ""}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1], delay: retraso }}
    >
      {children}
    </motion.div>
  );
}
