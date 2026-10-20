// Punto de entrada: estilos globales, enrutador y montaje de la aplicación.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { MotionConfig } from "motion/react";
import { App } from "./App";
import "./estilos/tokens.css";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/vistas.css";

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    {/* reducedMotion="user": Motion desactiva transformaciones si el sistema lo pide */}
    <MotionConfig reducedMotion="user">
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <App />
      </BrowserRouter>
    </MotionConfig>
  </StrictMode>,
);
