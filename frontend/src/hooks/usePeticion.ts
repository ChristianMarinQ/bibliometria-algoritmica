// Hooks de peticiones: `usePeticion` se ejecuta al cambiar sus dependencias y `useEjecucion`
// se lanza a mano (botón «Calcular», «Buscar»). Ambos cancelan con AbortController la petición
// anterior, así una respuesta vieja nunca pisa a una más nueva.
import { useCallback, useEffect, useRef, useState, type DependencyList } from "react";

export interface EstadoPeticion<T> {
  datos: T | null;
  cargando: boolean;
  error: string | null;
  recargar: () => void;
}

export function usePeticion<T>(fn: ((senal: AbortSignal) => Promise<T>) | null, deps: DependencyList): EstadoPeticion<T> {
  const [datos, setDatos] = useState<T | null>(null);
  const [cargando, setCargando] = useState(Boolean(fn));
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!fn) {
      setCargando(false);
      return;
    }
    const control = new AbortController();
    setCargando(true);
    setError(null);
    fn(control.signal)
      .then((r) => {
        if (!control.signal.aborted) setDatos(r);
      })
      .catch((e: unknown) => {
        if (!control.signal.aborted) setError(mensajeError(e));
      })
      .finally(() => {
        if (!control.signal.aborted) setCargando(false);
      });
    // Al cambiar las dependencias o desmontar se cancela la petición en curso.
    return () => control.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, version]);

  const recargar = useCallback(() => setVersion((v) => v + 1), []);
  return { datos, cargando, error, recargar };
}

export interface EstadoEjecucion<T> {
  datos: T | null;
  cargando: boolean;
  error: string | null;
  /** Lanza `fn` cancelando la anterior; `alExito` corre en el mismo lote que guarda los datos. */
  ejecutar: (fn: (senal: AbortSignal) => Promise<T>, alExito?: (r: T) => void) => Promise<void>;
  /** true si hay una petición sin terminar (lectura síncrona, sirve para evitar duplicados). */
  enCurso: () => boolean;
}

export function useEjecucion<T>(): EstadoEjecucion<T> {
  const [datos, setDatos] = useState<T | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const actual = useRef<AbortController | null>(null);

  // Cancelar la petición pendiente al desmontar la vista.
  useEffect(
    () => () => {
      actual.current?.abort();
      actual.current = null;
    },
    [],
  );
  const enCurso = useCallback(() => actual.current !== null, []);

  const ejecutar = useCallback(async (fn: (senal: AbortSignal) => Promise<T>, alExito?: (r: T) => void) => {
    actual.current?.abort();
    const control = new AbortController();
    actual.current = control;
    setCargando(true);
    setError(null);
    try {
      const r = await fn(control.signal);
      if (control.signal.aborted) return;
      alExito?.(r);
      setDatos(r);
    } catch (e) {
      if (!control.signal.aborted) setError(mensajeError(e));
    } finally {
      if (actual.current === control) {
        actual.current = null;
        setCargando(false);
      }
    }
  }, []);

  return { datos, cargando, error, ejecutar, enCurso };
}

export function mensajeError(e: unknown): string {
  // fetch lanza TypeError cuando no hay conexión (backend apagado, CORS, red).
  if (e instanceof TypeError) return "No se pudo conectar con la API. ¿Está corriendo el backend?";
  return e instanceof Error ? e.message : String(e);
}
