// Selectores: Segmentado (una opción, con indicador que se desliza), Chips (varias) y Lista (desplegable).
import { motion } from "motion/react";
import { useId } from "react";

export interface Opcion<T extends string | number> {
  valor: T;
  etiqueta: string;
  detalle?: string;
}

interface PropsSegmentado<T extends string | number> {
  opciones: Opcion<T>[];
  valor: T;
  onCambio: (v: T) => void;
  etiqueta: string; // nombre accesible del grupo
}

export function Segmentado<T extends string | number>({ opciones, valor, onCambio, etiqueta }: PropsSegmentado<T>) {
  const id = useId();
  return (
    <div className="segmentado" role="radiogroup" aria-label={etiqueta}>
      {opciones.map((o) => {
        const activo = o.valor === valor;
        return (
          <button
            key={String(o.valor)}
            type="button"
            role="radio"
            aria-checked={activo}
            className={`segmentado__opcion ${activo ? "es-activo" : ""}`}
            onClick={() => onCambio(o.valor)}
          >
            {activo && (
              <motion.span
                layoutId={`segmentado-${id}`}
                className="segmentado__indicador"
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
            <span className="segmentado__texto">{o.etiqueta}</span>
          </button>
        );
      })}
    </div>
  );
}

interface PropsChips<T extends string | number> {
  opciones: Opcion<T>[];
  valores: T[];
  /** Recibe una función de actualización (compatible con el `set` de useState) para no
   *  depender de `valores` capturado en el render: dos clics seguidos se registran ambos. */
  onCambio: (actualizar: (previos: T[]) => T[]) => void;
  etiqueta: string;
}

export function Chips<T extends string | number>({ opciones, valores, onCambio, etiqueta }: PropsChips<T>) {
  const alternar = (v: T) => onCambio((previos) => (previos.includes(v) ? previos.filter((x) => x !== v) : [...previos, v]));
  return (
    <div className="chips" role="group" aria-label={etiqueta}>
      {opciones.map((o) => {
        const activo = valores.includes(o.valor);
        return (
          <motion.button
            key={String(o.valor)}
            type="button"
            aria-pressed={activo}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 600, damping: 35 }}
            className={`chip ${activo ? "es-activo" : ""}`}
            onClick={() => alternar(o.valor)}
            title={o.detalle}
          >
            <span className="chip__marca" aria-hidden />
            {o.etiqueta}
          </motion.button>
        );
      })}
    </div>
  );
}

interface PropsLista<T extends string | number> {
  opciones: Opcion<T>[];
  valor: T;
  onCambio: (v: T) => void;
  etiqueta: string;
}

/** Selector desplegable nativo con estilo propio (para listas largas). */
export function Lista<T extends string | number>({ opciones, valor, onCambio, etiqueta }: PropsLista<T>) {
  return (
    <label className="lista">
      <span className="lista__etiqueta">{etiqueta}</span>
      <select
        value={String(valor)}
        onChange={(e) => {
          const o = opciones.find((x) => String(x.valor) === e.target.value);
          if (o) onCambio(o.valor);
        }}
      >
        {opciones.map((o) => (
          <option key={String(o.valor)} value={String(o.valor)}>
            {o.etiqueta}
          </option>
        ))}
      </select>
    </label>
  );
}
