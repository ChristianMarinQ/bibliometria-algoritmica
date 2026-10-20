// Encabezado editorial de cada vista: antetítulo, título serif y entradilla.
import type { ReactNode } from "react";

export function EncabezadoVista({ antetitulo, titulo, children }: { antetitulo: string; titulo: string; children?: ReactNode }) {
  return (
    <header className="encabezado-vista">
      <p className="antetitulo">{antetitulo}</p>
      <h1 className="titulo-vista">{titulo}</h1>
      {children && <div className="entradilla">{children}</div>}
    </header>
  );
}
