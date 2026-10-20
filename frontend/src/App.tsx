// Estructura general: barra lateral de navegación (menú desplegable en móvil) y rutas de las vistas.
import { AnimatePresence, motion } from "motion/react";
import { Menu, Moon, Sun, X as Cerrar } from "lucide";
import { useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { USAR_MOCKS, URL_API } from "./api";
import { IconoMorph } from "./componentes/ui/Icono";
import { LimiteError } from "./componentes/ui/LimiteError";
import { useTema } from "./hooks/useTema";
import { VistaBusqueda } from "./vistas/Busqueda";
import { VistaClustering } from "./vistas/Clustering";
import { VistaCorpus } from "./vistas/Corpus";
import { VistaRanking } from "./vistas/Ranking";
import { VistaSimilitud } from "./vistas/Similitud";

const SECCIONES = [
  { ruta: "/corpus", marca: "00", nombre: "Corpus", detalle: "20 artículos" },
  { ruta: "/similitud", marca: "R1", nombre: "Similitud textual", detalle: "Clásicos e IA" },
  { ruta: "/clustering", marca: "R2", nombre: "Clustering jerárquico", detalle: "Dendrogramas" },
  { ruta: "/busqueda", marca: "R3", nombre: "Búsqueda de patrones", detalle: "KMP · BM · RK" },
  { ruta: "/ranking", marca: "S", nombre: "Ranking de términos", detalle: "Ordenamiento lineal" },
];

export function App() {
  const ubicacion = useLocation();
  const { tema, alternar } = useTema();
  const [menuAbierto, setMenuAbierto] = useState(false);

  // Cerrar el menú móvil al navegar.
  useEffect(() => setMenuAbierto(false), [ubicacion.pathname]);

  // Cerrar el menú móvil con Escape.
  useEffect(() => {
    if (!menuAbierto) return;
    const alTeclear = (e: KeyboardEvent) => e.key === "Escape" && setMenuAbierto(false);
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [menuAbierto]);

  // `grupo` separa el layoutId del indicador entre la barra lateral y el menú móvil.
  const navegacion = (grupo: string) => (
    <nav aria-label="Secciones" className="nav">
      {SECCIONES.map((s) => (
        <NavLink key={s.ruta} to={s.ruta} className={({ isActive }) => `nav__enlace ${isActive ? "es-activo" : ""}`}>
          {({ isActive }) => (
            <>
              {isActive && (
                <motion.span layoutId={`nav-indicador-${grupo}`} className="nav__indicador" transition={{ type: "spring", stiffness: 500, damping: 40 }} />
              )}
              <span className="nav__marca">{s.marca}</span>
              <span className="nav__textos">
                <span className="nav__nombre">{s.nombre}</span>
                <span className="nav__detalle">{s.detalle}</span>
              </span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );

  const interruptorTema = (
    <button
      type="button"
      className="boton boton--fantasma boton--icono"
      onClick={alternar}
      aria-label={tema === "claro" ? "Activar modo oscuro" : "Activar modo claro"}
      title={tema === "claro" ? "Modo oscuro" : "Modo claro"}
    >
      <IconoMorph icono={tema === "claro" ? Moon : Sun} />
    </button>
  );

  return (
    <div className="aplicacion">
      <aside className="lateral">
        <div className="lateral__marca">
          <p className="lateral__titulo">
            Bibliometría <em>algorítmica</em>
          </p>
          <p className="lateral__sub">Análisis de Algoritmos · Universidad del Quindío</p>
        </div>
        {navegacion("lateral")}
        <div className="lateral__pie">
          <span className={`etiqueta-fuente ${USAR_MOCKS ? "es-mock" : ""}`} title={USAR_MOCKS ? "VITE_USAR_MOCKS=true: corpus real, cálculos simulados en el navegador" : URL_API}>
            <span className="punto" aria-hidden />
            {USAR_MOCKS ? "Cálculos simulados" : "API en vivo"}
          </span>
          {interruptorTema}
        </div>
      </aside>

      <header className="barra-movil">
        <p className="lateral__titulo">
          Bibliometría <em>algorítmica</em>
        </p>
        <div className="barra-movil__acciones">
          {interruptorTema}
          <button
            type="button"
            className="boton boton--fantasma boton--icono"
            aria-expanded={menuAbierto}
            aria-controls="menu-movil"
            aria-label={menuAbierto ? "Cerrar menú" : "Abrir menú"}
            onClick={() => setMenuAbierto((v) => !v)}
          >
            <IconoMorph icono={menuAbierto ? Cerrar : Menu} />
          </button>
        </div>
        <AnimatePresence>
          {menuAbierto && (
            <motion.div
              id="menu-movil"
              className="menu-movil"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6, transition: { duration: 0.15 } }}
              transition={{ duration: 0.22, ease: [0.23, 1, 0.32, 1] }}
            >
              {navegacion("movil")}
              {USAR_MOCKS && <p className="tenue menu-movil__nota">Modo sin backend: corpus real, cálculos simulados</p>}
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="principal" id="contenido">
        {/* Solo animación de entrada (sin esperar la salida): el cambio de vista es inmediato. */}
        <motion.div
          key={ubicacion.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
        >
          {/* El contenedor tiene key por ruta, así que el límite de errores se reinicia al navegar. */}
          <LimiteError>
            <Routes location={ubicacion}>
              <Route path="/" element={<Navigate to="/corpus" replace />} />
              <Route path="/corpus" element={<VistaCorpus />} />
              <Route path="/similitud" element={<VistaSimilitud />} />
              <Route path="/clustering" element={<VistaClustering />} />
              <Route path="/busqueda" element={<VistaBusqueda />} />
              <Route path="/ranking" element={<VistaRanking />} />
              <Route path="*" element={<Navigate to="/corpus" replace />} />
            </Routes>
          </LimiteError>
        </motion.div>
      </main>
    </div>
  );
}
