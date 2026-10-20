// Tabla de datos genérica: columnas declarativas, números tabulares alineados a la derecha.
import type { ReactNode } from "react";

export interface Columna<F> {
  clave: string;
  titulo: ReactNode;
  celda: (fila: F, indice: number) => ReactNode;
  numerica?: boolean;
  ancho?: string;
}

interface Props<F> {
  columnas: Columna<F>[];
  filas: F[];
  claveFila: (f: F, i: number) => string | number;
  resaltar?: (f: F) => boolean;
  densa?: boolean;
  alPulsar?: (f: F) => void;
  titulo?: string; // caption accesible
}

export function Tabla<F>({ columnas, filas, claveFila, resaltar, densa, alPulsar, titulo }: Props<F>) {
  return (
    <div className="tabla-contenedor">
      <table className={`tabla ${densa ? "tabla--densa" : ""}`}>
        {titulo && <caption className="solo-lector">{titulo}</caption>}
        <thead>
          <tr>
            {columnas.map((c) => (
              <th key={c.clave} className={c.numerica ? "num" : ""} style={{ width: c.ancho }} scope="col">
                {c.titulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((f, i) => (
            <tr
              key={claveFila(f, i)}
              className={`${resaltar?.(f) ? "es-resaltada" : ""} ${alPulsar ? "es-pulsable" : ""}`}
              onClick={alPulsar ? () => alPulsar(f) : undefined}
            >
              {columnas.map((c) => (
                <td key={c.clave} className={c.numerica ? "num" : ""}>
                  {c.celda(f, i)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
