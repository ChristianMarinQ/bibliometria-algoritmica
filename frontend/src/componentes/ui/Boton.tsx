// Botón base: escala 0.97 al presionar (spring corto), variantes y tamaño.
import { motion, type HTMLMotionProps } from "motion/react";
import { forwardRef, type ReactNode } from "react";

interface Props extends HTMLMotionProps<"button"> {
  variante?: "primario" | "secundario" | "fantasma";
  tamano?: "normal" | "pequeno";
  icono?: ReactNode;
  children?: ReactNode;
}

// forwardRef: permite devolver el foco al botón (p. ej. al cerrar un diálogo).
export const Boton = forwardRef<HTMLButtonElement, Props>(function Boton(
  { variante = "secundario", tamano = "normal", icono, children, className = "", ...resto },
  ref,
) {
  return (
    <motion.button
      ref={ref}
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
});
