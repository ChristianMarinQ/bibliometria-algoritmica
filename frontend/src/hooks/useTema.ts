// Tema claro/oscuro: claro por defecto y oscuro opcional con un interruptor.
import { useEffect, useState } from "react";

export type Tema = "claro" | "oscuro";

// El tema por defecto es claro (fondo blanco); el oscuro solo se activa con el interruptor.
function temaSistema(): Tema {
  return "claro";
}

export function useTema() {
  const [tema, setTema] = useState<Tema>(() => {
    const forzado = document.documentElement.dataset.tema;
    return forzado === "claro" || forzado === "oscuro" ? forzado : temaSistema();
  });

  useEffect(() => {
    document.documentElement.dataset.tema = tema;
  }, [tema]);

  const alternar = () =>
    setTema((t) => {
      const nuevo = t === "claro" ? "oscuro" : "claro";
      try {
        localStorage.setItem("tema", nuevo);
      } catch {
        /* almacenamiento no disponible: el tema solo dura la sesión */
      }
      return nuevo;
    });

  return { tema, alternar };
}
