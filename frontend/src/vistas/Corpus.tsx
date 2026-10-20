// Vista Corpus: índice de los 20 artículos; al abrir uno se muestra su abstract en una hoja lateral.
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { api, type Articulo } from "../api";
import { Boton } from "../componentes/ui/Boton";
import { Dato, entero } from "../componentes/ui/Dato";
import { EncabezadoVista } from "../componentes/ui/EncabezadoVista";
import { Cargando, MensajeError, Vacio } from "../componentes/ui/Estado";
import { Search, X } from "../componentes/ui/Icono";
import { Segmentado } from "../componentes/ui/Selector";
import { usePeticion } from "../hooks/usePeticion";

type Orden = "id" | "anio";

export function VistaCorpus() {
  const { datos, cargando, error, recargar } = usePeticion((senal) => api.articulos(senal), []);
  const [filtro, setFiltro] = useState("");
  const [orden, setOrden] = useState<Orden>("id");
  const [abierto, setAbierto] = useState<Articulo | null>(null);
  // Al cerrar, el foco vuelve a la fila que abrió la hoja (accesibilidad con teclado).
  const origen = useRef<HTMLElement | null>(null);
  const cerrar = useCallback(() => {
    setAbierto(null);
    origen.current?.focus();
  }, []);

  const lista = useMemo(() => {
    const f = filtro.trim().toLowerCase();
    const filtrados = (datos ?? []).filter(
      (a) => !f || a.titulo.toLowerCase().includes(f) || a.autores.join(" ").toLowerCase().includes(f) || a.revista.toLowerCase().includes(f),
    );
    return [...filtrados].sort((a, b) => (orden === "id" ? a.id - b.id : b.anio - a.anio || a.id - b.id));
  }, [datos, filtro, orden]);

  const anios = datos?.map((a) => a.anio) ?? [];
  const palabras = datos?.reduce((s, a) => s + a.palabras_abstract, 0) ?? 0;

  return (
    <div className="vista">
      <EncabezadoVista antetitulo="Corpus" titulo="Veinte artículos sobre IA en educación">
        <p>
          Los abstracts de estos artículos son la materia prima de todos los requerimientos: se comparan por similitud, se agrupan
          jerárquicamente, se recorren buscando patrones y se usan para el ranking de términos.
        </p>
      </EncabezadoVista>

      {datos && (
        <div className="fila-datos">
          <Dato rotulo="Artículos" valor={datos.length} />
          <Dato rotulo="Periodo" valor={`${Math.min(...anios)}–${Math.max(...anios)}`} />
          <Dato rotulo="Palabras en abstracts" valor={entero(palabras)} />
          <Dato rotulo="Revistas" valor={new Set(datos.map((a) => a.revista)).size} />
        </div>
      )}

      <div className="barra-herramientas">
        <label className="campo campo--busqueda">
          <Search size={16} aria-hidden />
          <span className="solo-lector">Filtrar artículos</span>
          <input value={filtro} onChange={(e) => setFiltro(e.target.value)} placeholder="Filtrar por título, autor o revista" />
        </label>
        <Segmentado
          etiqueta="Ordenar por"
          valor={orden}
          onCambio={setOrden}
          opciones={[
            { valor: "id", etiqueta: "Número" },
            { valor: "anio", etiqueta: "Año" },
          ]}
        />
      </div>

      {error && <MensajeError mensaje={error} reintentar={recargar} />}
      {cargando && !datos && <Cargando lineas={8} />}
      {datos && lista.length === 0 && <Vacio>Ningún artículo coincide con “{filtro}”.</Vacio>}

      <ol className="indice">
        {lista.map((a, k) => (
          <motion.li
            key={a.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1], delay: Math.min(k * 0.02, 0.24) }}
          >
            <button type="button" className="indice__fila" onClick={(e) => {
                origen.current = e.currentTarget;
                setAbierto(a);
              }}>
              <span className="indice__numero">{String(a.id).padStart(2, "0")}</span>
              <span className="indice__cuerpo">
                <span className="indice__titulo">{a.titulo}</span>
                <span className="indice__meta">
                  {a.autores.join(", ")} · <em>{a.revista}</em>
                </span>
              </span>
              <span className="indice__anio">{a.anio}</span>
            </button>
          </motion.li>
        ))}
      </ol>

      <HojaArticulo articulo={abierto} onCerrar={cerrar} />
    </div>
  );
}

/** Panel lateral con el detalle (carga el abstract bajo demanda). */
function HojaArticulo({ articulo, onCerrar }: { articulo: Articulo | null; onCerrar: () => void }) {
  const detalle = usePeticion(articulo ? (senal) => api.articulo(articulo.id, senal) : null, [articulo?.id]);

  const abierta = articulo !== null;
  useEffect(() => {
    if (!abierta) return;
    const alTeclear = (e: KeyboardEvent) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [abierta, onCerrar]);

  // Portal al <body>: la transición de ruta aplica transform al contenedor y rompería position: fixed.
  return createPortal(
    <AnimatePresence>
      {articulo && (
        <>
          <motion.div
            className="velo"
            onClick={onCerrar}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
          <motion.aside
            className="hoja"
            role="dialog"
            aria-modal="true"
            aria-labelledby="hoja-titulo"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%", transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } }}
            transition={{ type: "spring", stiffness: 420, damping: 42 }}
          >
            <div className="hoja__cabecera">
              <span className="antetitulo">Artículo {String(articulo.id).padStart(2, "0")}</span>
              <Boton variante="fantasma" icono={<X size={18} />} aria-label="Cerrar" onClick={onCerrar} autoFocus />
            </div>
            <h2 id="hoja-titulo" className="hoja__titulo">
              {articulo.titulo}
            </h2>
            <dl className="hoja__meta">
              <div>
                <dt>Autores</dt>
                <dd>{articulo.autores.join(", ")}</dd>
              </div>
              <div>
                <dt>Revista</dt>
                <dd>
                  <em>{articulo.revista}</em>, {articulo.anio}
                </dd>
              </div>
              <div>
                <dt>Archivo</dt>
                <dd className="mono">{articulo.archivo}</dd>
              </div>
            </dl>
            <h3 className="subtitulo">Abstract · {articulo.palabras_abstract} palabras</h3>
            {detalle.error && <MensajeError mensaje={detalle.error} reintentar={detalle.recargar} />}
            {detalle.cargando && <Cargando lineas={7} />}
            {detalle.datos && !detalle.cargando && <p className="hoja__abstract">{detalle.datos.abstract}</p>}
          </motion.aside>
        </>
      )}
    </AnimatePresence>,
    document.body,
  );
}
