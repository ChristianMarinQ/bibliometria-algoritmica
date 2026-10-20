// Control de una traza paso a paso: índice actual, anterior/siguiente y reproducción automática.
// El componente que lo usa debe montarse con una `key` por traza para empezar siempre en el paso 0.
import { useCallback, useEffect, useState } from "react";

export function useReproductor(total: number, intervaloMs = 650) {
  const [paso, setPaso] = useState(0);
  const [reproduciendo, setReproduciendo] = useState(false);
  const ultimo = Math.max(0, total - 1);

  // Un único intervalo mientras se reproduce; se limpia al pausar, al cambiar la traza o al desmontar.
  useEffect(() => {
    if (!reproduciendo) return;
    const id = window.setInterval(() => setPaso((p) => Math.min(ultimo, p + 1)), intervaloMs);
    return () => window.clearInterval(id);
  }, [reproduciendo, ultimo, intervaloMs]);

  // Al llegar al último paso la reproducción se detiene sola.
  useEffect(() => {
    if (reproduciendo && paso >= ultimo) setReproduciendo(false);
  }, [reproduciendo, paso, ultimo]);

  const siguiente = useCallback(() => setPaso((p) => Math.min(ultimo, p + 1)), [ultimo]);
  const anterior = useCallback(() => setPaso((p) => Math.max(0, p - 1)), []);
  const alternar = useCallback(() => {
    if (reproduciendo) {
      setReproduciendo(false);
      return;
    }
    // Si ya está al final, reproducir vuelve a empezar.
    setPaso((p) => (p >= ultimo ? 0 : p));
    setReproduciendo(ultimo > 0);
  }, [reproduciendo, ultimo]);
  const ir = useCallback((p: number) => setPaso(Math.max(0, Math.min(ultimo, p))), [ultimo]);

  return { paso: Math.min(paso, ultimo), reproduciendo, siguiente, anterior, alternar, ir };
}
