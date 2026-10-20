// Botón base: escala 0.97 al presionar (spring corto), variantes y tamaño.
import { motion, type HTMLMotionProps } from "motion/react";
import type { ReactNode } from "react";

interface Props extends HTMLMotionProps<"button"> {
  variante?: "primario" | "secundario" | "fantasma";
  tamano?: "normal" | "pequeno";
  icono?: ReactNode;
  children?: ReactNode;
}

export function Boton({ variante = "secundario", tamano = "normal", icono, children, className = "", ...resto }: Props) {
  return (
    <motion.button
      type="button"
      whileTap={resto.disabled ? undefined : { scale: 0.97 }}
      transition={{ type: "spring", stiffness: 600, damping: 35 }}
      className={`boton boton--${variante} ${tamano === "pequeno" ? "boton--pequeno" : ""} ${!children ? "boton--icono" : ""} ${className}`}
      {...resto}
    >
      {icono}
      {children && <span>{children}</span>}
    </motion.button>
  );
}
