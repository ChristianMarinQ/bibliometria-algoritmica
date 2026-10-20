// Observa el ancho de un contenedor para que los gráficos D3 sean responsivos.
import { useEffect, useRef, useState } from "react";

export function useMedida<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [ancho, setAncho] = useState(0);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new ResizeObserver(([e]) => setAncho(Math.floor(e.contentRect.width)));
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return [ref, ancho] as const;
}
