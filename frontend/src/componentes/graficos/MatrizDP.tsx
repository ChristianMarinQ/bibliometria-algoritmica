// Matriz de programación dinámica (Levenshtein / Needleman-Wunsch) con el camino óptimo resaltado.
// La matriz llega recortada (13×13 = cadena vacía + 12 palabras); el camino llega completo y se filtra.
import { useState } from "react";

interface Props {
  secuenciaA: string[];
  secuenciaB: string[];
  matriz: number[][];
  camino: [number, number][];
}

export function MatrizDP({ secuenciaA, secuenciaB, matriz, camino }: Props) {
  const [foco, setFoco] = useState<[number, number] | null>(null);
  const filas = matriz.length;
  const cols = matriz[0]?.length ?? 0;
  const enCamino = new Map<string, number>();
  camino.filter(([i, j]) => i < filas && j < cols).forEach(([i, j], k) => enCamino.set(`${i},${j}`, k));
  const encA = ["∅", ...secuenciaA.slice(0, filas - 1)];
  const encB = ["∅", ...secuenciaB.slice(0, cols - 1)];

  return (
    <div className="matriz-dp" onMouseLeave={() => setFoco(null)}>
      <table>
        <thead>
          <tr>
            <th className="matriz-dp__esquina" scope="col">
              <span className="solo-lector">A \ B</span>
            </th>
            {encB.map((p, j) => (
              <th key={j} scope="col" className={foco?.[1] === j ? "es-foco" : ""}>
                <span className="matriz-dp__palabra">{p}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matriz.map((fila, i) => (
            <tr key={i}>
              <th scope="row" className={foco?.[0] === i ? "es-foco" : ""}>
                <span className="matriz-dp__palabra">{encA[i]}</span>
              </th>
              {fila.map((v, j) => {
                const orden = enCamino.get(`${i},${j}`);
                const coincide = i > 0 && j > 0 && encA[i] === encB[j];
                return (
                  <td
                    key={j}
                    className={`${orden !== undefined ? "es-camino" : ""} ${coincide ? "es-igual" : ""}`}
                    style={orden !== undefined ? { transitionDelay: `${orden * 25}ms` } : undefined}
                    onMouseEnter={() => setFoco([i, j])}
                  >
                    {v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
