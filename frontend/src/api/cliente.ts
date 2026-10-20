// Cliente HTTP mínimo: arma la URL, envía JSON y traduce los errores de FastAPI.

export const URL_API: string = (import.meta.env.VITE_API_URL ?? "http://localhost:8000/api").replace(/\/$/, "");
export const USAR_MOCKS: boolean = import.meta.env.VITE_USAR_MOCKS === "true";

/** Error con el mensaje `detail` que devuelve FastAPI y el código HTTP. */
export class ErrorApi extends Error {
  constructor(mensaje: string, public estado: number) {
    super(mensaje);
    this.name = "ErrorApi";
  }
}

type Parametros = Record<string, string | number | undefined>;

function construirUrl(ruta: string, parametros?: Parametros): string {
  // La base permite URL relativas ("/api") cuando el frontend y la API comparten dominio.
  const url = new URL(URL_API + ruta, window.location.origin);
  if (parametros) {
    for (const [clave, valor] of Object.entries(parametros)) {
      if (valor !== undefined) url.searchParams.set(clave, String(valor));
    }
  }
  return url.toString();
}

async function procesar<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    let mensaje = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      // FastAPI usa {"detail": "…"}; en 422 `detail` es una lista de errores.
      if (typeof cuerpo.detail === "string") mensaje = cuerpo.detail;
      else if (Array.isArray(cuerpo.detail)) mensaje = cuerpo.detail.map((d: { msg?: string }) => d.msg).join("; ");
    } catch {
      /* cuerpo no JSON: se conserva el mensaje genérico */
    }
    throw new ErrorApi(mensaje, respuesta.status);
  }
  return respuesta.json() as Promise<T>;
}

export async function obtener<T>(ruta: string, parametros?: Parametros, senal?: AbortSignal): Promise<T> {
  const respuesta = await fetch(construirUrl(ruta, parametros), { signal: senal });
  return procesar<T>(respuesta);
}

export async function enviar<T>(ruta: string, cuerpo: unknown, senal?: AbortSignal): Promise<T> {
  const respuesta = await fetch(construirUrl(ruta), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
    signal: senal,
  });
  return procesar<T>(respuesta);
}
