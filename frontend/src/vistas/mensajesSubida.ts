// Mensajes de error amables para la subida de artículos (códigos de docs/CONTRATO_API.md).
import { ErrorApi } from "../api";
import { mensajeError } from "../hooks/usePeticion";

/** Traduce los códigos del contrato a mensajes amables; conserva el detalle del backend. */
export function mensajeSubida(e: unknown): string {
  if (!(e instanceof ErrorApi)) return mensajeError(e);
  const detalle = e.message && !/^Error \d+$/.test(e.message) ? ` (${e.message})` : "";
  switch (e.estado) {
    case 400:
      return `No se pudo leer el archivo: debe ser un PDF con texto seleccionable${detalle}.`;
    case 403:
      return "La clave de subida no es válida o la subida está deshabilitada en este servidor.";
    case 404:
      return "El artículo ya no existe; recarga la lista.";
    case 409:
      return "Ya existe un artículo con ese título en el corpus. Cambia el título o cancela.";
    case 413:
      return "El archivo supera el tamaño máximo permitido.";
    case 422:
      return `Revisa los datos: el título no puede quedar vacío y el abstract debe tener entre 30 y 1000 palabras${detalle}.`;
    default:
      return e.message;
  }
}
