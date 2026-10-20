// Aviso global "corpus cambiado": al agregar o eliminar un artículo, las vistas que
// cargan la lista de artículos incluyen esta versión en sus dependencias y se recargan.
import { useEffect, useState } from "react";

const EVENTO = "corpus-cambiado";

export function avisarCorpusCambiado(): void {
  window.dispatchEvent(new Event(EVENTO));
}

/** Número que aumenta cada vez que cambia el corpus (útil como dependencia de usePeticion). */
export function useVersionCorpus(): number {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const alCambiar = () => setVersion((v) => v + 1);
    window.addEventListener(EVENTO, alCambiar);
    return () => window.removeEventListener(EVENTO, alCambiar);
  }, []);
  return version;
}
