// Cifra destacada con su rótulo (para métricas y resúmenes) y utilidades de formato.
import type { ReactNode } from "react";

export function Dato({ rotulo, valor, nota, destacado }: { rotulo: string; valor: ReactNode; nota?: ReactNode; destacado?: boolean }) {
  return (
    <div className={`dato ${destacado ? "dato--destacado" : ""}`}>
      <span className="dato__rotulo">{rotulo}</span>
      <span className="dato__valor">{valor}</span>
      {nota && <span className="dato__nota">{nota}</span>}
    </div>
  );
}

export const formatoMs = (ms: number) => (ms < 1 ? `${ms.toFixed(3)} ms` : ms < 100 ? `${ms.toFixed(2)} ms` : `${ms.toFixed(0)} ms`);
export const formato = (x: number, d = 3) => x.toFixed(d);
export const entero = (x: number) => x.toLocaleString("es-CO");
