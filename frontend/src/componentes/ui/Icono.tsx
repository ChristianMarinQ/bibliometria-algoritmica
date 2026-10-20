// Iconos: estáticos de lucide-react y morfológicos (morphicons) para cambios de estado.
import { MorphIcon } from "morphicons/react";
import type { IconNode } from "lucide";

export {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Info,
  RotateCcw,
  Search,
  SkipBack,
  SkipForward,
  X,
} from "lucide-react";

interface PropsMorph {
  icono: IconNode;
  tamano?: number;
  etiqueta?: string;
  grosor?: number;
}

/** Icono que se transforma (morph) al cambiar `icono`; respeta prefers-reduced-motion. */
export function IconoMorph({ icono, tamano = 18, etiqueta, grosor = 1.75 }: PropsMorph) {
  return <MorphIcon icon={icono} size={tamano} strokeWidth={grosor} label={etiqueta} reducedMotion="user" spring="snappy" />;
}
