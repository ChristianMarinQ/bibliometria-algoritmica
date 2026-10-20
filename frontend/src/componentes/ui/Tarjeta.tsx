// Panel con encabezado opcional (título, descripción y acciones a la derecha).
import type { ReactNode } from "react";

interface Props {
  titulo?: ReactNode;
  descripcion?: ReactNode;
  acciones?: ReactNode;
  children: ReactNode;
  className?: string;
  plana?: boolean; // sin borde ni fondo, solo separación
}

export function Tarjeta({ titulo, descripcion, acciones, children, className = "", plana }: Props) {
  return (
    <section className={`tarjeta ${plana ? "tarjeta--plana" : ""} ${className}`}>
      {(titulo || acciones) && (
        <header className="tarjeta__cabecera">
          <div>
            {titulo && <h3 className="tarjeta__titulo">{titulo}</h3>}
            {descripcion && <p className="tarjeta__descripcion">{descripcion}</p>}
          </div>
          {acciones && <div className="tarjeta__acciones">{acciones}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
