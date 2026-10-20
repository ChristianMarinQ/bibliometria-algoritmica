// Diálogo "Agregar artículo": 1) elegir el PDF, 2) revisar lo extraído, 3) guardar.
// El backend extrae sin guardar; el usuario corrige y confirma (ver docs/CONTRATO_API.md).
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState, type DragEvent, type FormEvent, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { api, guardarClave, leerClave, type ArticuloExtraido, type ArticuloGuardado, type InfoSistema } from "../api";
import { Boton } from "../componentes/ui/Boton";
import { MensajeError } from "../componentes/ui/Estado";
import { CircleAlert, FileUp, Info, Plus, X } from "../componentes/ui/Icono";
import { mensajeSubida } from "./mensajesSubida";

type Paso = "archivo" | "revision" | "guardando";

interface Props {
  abierto: boolean;
  sistema: InfoSistema;
  onCerrar: () => void;
  onGuardado: (articulo: ArticuloGuardado) => void;
}

const contarPalabras = (texto: string) => texto.split(/\s+/).filter(Boolean).length;

export function DialogoSubida({ abierto, sistema, onCerrar, onGuardado }: Props) {
  const [paso, setPaso] = useState<Paso>("archivo");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [clave, setClave] = useState(leerClave);
  const [extraido, setExtraido] = useState<ArticuloExtraido | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const panel = useRef<HTMLDivElement>(null);
  const control = useRef<AbortController | null>(null);

  // Formulario editable de la revisión.
  const [titulo, setTitulo] = useState("");
  const [autores, setAutores] = useState<string[]>([]);
  const [anio, setAnio] = useState("");
  const [revista, setRevista] = useState("");
  const [abstract, setAbstract] = useState("");

  // Reiniciar al abrir y cancelar lo pendiente al cerrar.
  useEffect(() => {
    if (abierto) {
      setPaso("archivo");
      setArchivo(null);
      setExtraido(null);
      setError(null);
      setOcupado(false);
    }
    return () => control.current?.abort();
  }, [abierto]);

  const cerrar = () => {
    if (paso === "guardando") return; // no se interrumpe el guardado a medias
    control.current?.abort();
    onCerrar();
  };

  // Foco atrapado dentro del diálogo y Escape para cerrar.
  const alTeclear = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      cerrar();
      return;
    }
    if (e.key !== "Tab" || !panel.current) return;
    const enfocables = panel.current.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    if (enfocables.length === 0) return;
    const primero = enfocables[0];
    const ultimo = enfocables[enfocables.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  const elegir = (f: File | null | undefined) => {
    setError(null);
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf") && f.type !== "application/pdf") {
      setArchivo(null);
      setError("El archivo debe ser un PDF (.pdf).");
      return;
    }
    if (f.size > sistema.tamano_maximo_mb * 1024 * 1024) {
      setArchivo(null);
      setError(`El archivo pesa ${(f.size / 1024 / 1024).toFixed(1)} MB; el máximo es ${sistema.tamano_maximo_mb} MB.`);
      return;
    }
    setArchivo(f);
  };

  const extraer = async (e: FormEvent) => {
    e.preventDefault();
    if (!archivo || ocupado) return;
    if (sistema.requiere_clave && !clave.trim()) {
      setError("Escribe la clave de subida.");
      return;
    }
    guardarClave(clave.trim());
    control.current?.abort();
    control.current = new AbortController();
    setOcupado(true);
    setError(null);
    try {
      const r = await api.extraerArticulo(archivo, control.current.signal);
      setExtraido(r);
      setTitulo(r.titulo);
      setAutores(r.autores.length ? r.autores : [""]);
      setAnio(r.anio ? String(r.anio) : "");
      setRevista(r.revista);
      setAbstract(r.abstract);
      setPaso("revision");
    } catch (err) {
      if (!control.current?.signal.aborted) setError(mensajeSubida(err));
    } finally {
      setOcupado(false);
    }
  };

  const palabras = contarPalabras(abstract);
  const abstractValido = palabras >= 30 && palabras <= 1000;
  const anioNumero = anio.trim() ? Number(anio) : null;
  const anioValido = anioNumero === null || (Number.isInteger(anioNumero) && anioNumero > 1900 && anioNumero <= 2100);

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    if (!extraido || !titulo.trim() || !abstractValido || !anioValido) return;
    control.current = new AbortController();
    setPaso("guardando");
    setError(null);
    try {
      const r = await api.guardarArticulo(
        {
          titulo: titulo.trim(),
          autores: autores.map((a) => a.trim()).filter(Boolean),
          anio: anioNumero,
          revista: revista.trim(),
          abstract: abstract.trim(),
          archivo: extraido.archivo,
        },
        control.current.signal,
      );
      onGuardado(r);
    } catch (err) {
      setError(mensajeSubida(err));
      setPaso("revision");
    }
  };

  const numeroPaso = paso === "archivo" ? 1 : paso === "revision" ? 2 : 3;

  return createPortal(
    <AnimatePresence>
      {abierto && (
        <>
          <motion.div
            className="velo"
            onClick={cerrar}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
          <motion.div
            ref={panel}
            className="hoja subida"
            role="dialog"
            aria-modal="true"
            aria-labelledby="subida-titulo"
            aria-describedby="subida-paso"
            onKeyDown={alTeclear}
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%", transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } }}
            transition={{ type: "spring", stiffness: 420, damping: 42 }}
          >
            <div className="hoja__cabecera">
              <span className="antetitulo" id="subida-paso">
                Paso {numeroPaso} de 3 · {paso === "archivo" ? "Archivo" : paso === "revision" ? "Revisión" : "Guardado"}
              </span>
              <Boton variante="fantasma" icono={<X size={18} />} aria-label="Cerrar" onClick={cerrar} disabled={paso === "guardando"} autoFocus />
            </div>
            <h2 id="subida-titulo" className="hoja__titulo">
              Agregar artículo
            </h2>
            <ol className="subida__pasos" aria-hidden>
              {[1, 2, 3].map((n) => (
                <li key={n} className={n <= numeroPaso ? "es-activo" : ""} />
              ))}
            </ol>

            {!sistema.ia_en_servidor && (
              <div className="aviso">
                <Info size={18} aria-hidden />
                <div>
                  <p>El servidor no tiene los modelos de IA: el artículo no tendrá vectores Word2Vec ni SBERT y esos algoritmos lo omitirán.</p>
                </div>
              </div>
            )}

            {error && <MensajeError mensaje={error} />}

            {paso === "archivo" && (
              <form className="subida__formulario" onSubmit={extraer}>
                <ZonaArchivo archivo={archivo} maximo={sistema.tamano_maximo_mb} onElegir={elegir} />
                {sistema.requiere_clave && (
                  <label className="subida__campo">
                    <span>Clave de subida</span>
                    <input type="password" className="entrada" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="off" />
                  </label>
                )}
                <div className="subida__acciones">
                  <Boton variante="fantasma" onClick={cerrar}>
                    Cancelar
                  </Boton>
                  <Boton variante="primario" type="submit" disabled={!archivo || ocupado} aria-busy={ocupado}>
                    {ocupado ? "Extrayendo texto…" : "Extraer datos"}
                  </Boton>
                </div>
              </form>
            )}

            {paso === "revision" && extraido && (
              <form className="subida__formulario" onSubmit={guardar}>
                {extraido.advertencias.length > 0 && (
                  <div className="aviso aviso--advertencia" role="status">
                    <CircleAlert size={18} aria-hidden />
                    <div>
                      <strong>Revisa lo extraído del PDF</strong>
                      <ul>
                        {extraido.advertencias.map((a) => (
                          <li key={a}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
                <p className="subida__archivo mono">{extraido.archivo}</p>
                <label className="subida__campo">
                  <span>Título</span>
                  <input className="entrada" value={titulo} onChange={(e) => setTitulo(e.target.value)} required aria-invalid={!titulo.trim()} />
                </label>
                <fieldset className="subida__campo">
                  <legend>Autores</legend>
                  {autores.map((a, k) => (
                    <div key={k} className="subida__autor">
                      <input
                        className="entrada"
                        value={a}
                        aria-label={`Autor ${k + 1}`}
                        onChange={(e) => setAutores(autores.map((x, j) => (j === k ? e.target.value : x)))}
                      />
                      <Boton
                        variante="fantasma"
                        tamano="pequeno"
                        icono={<X size={14} />}
                        aria-label={`Quitar autor ${k + 1}`}
                        onClick={() => setAutores(autores.length > 1 ? autores.filter((_, j) => j !== k) : [""])}
                      />
                    </div>
                  ))}
                  <Boton variante="fantasma" tamano="pequeno" icono={<Plus size={14} />} onClick={() => setAutores([...autores, ""])}>
                    Agregar autor
                  </Boton>
                </fieldset>
                <div className="subida__fila">
                  <label className="subida__campo subida__campo--anio">
                    <span>Año</span>
                    <input className="entrada" inputMode="numeric" value={anio} onChange={(e) => setAnio(e.target.value)} aria-invalid={!anioValido} placeholder="—" />
                  </label>
                  <label className="subida__campo">
                    <span>Revista</span>
                    <input className="entrada" value={revista} onChange={(e) => setRevista(e.target.value)} />
                  </label>
                </div>
                <label className="subida__campo">
                  <span>Abstract</span>
                  <textarea
                    className="entrada subida__abstract"
                    value={abstract}
                    rows={9}
                    onChange={(e) => setAbstract(e.target.value)}
                    aria-invalid={!abstractValido}
                    aria-describedby="subida-palabras"
                  />
                  <span id="subida-palabras" className={`subida__contador ${abstractValido ? "" : "es-invalido"}`} aria-live="polite">
                    {palabras} palabras {abstractValido ? "" : "· debe tener entre 30 y 1000"}
                  </span>
                </label>
                <div className="subida__acciones">
                  <Boton variante="fantasma" onClick={() => setPaso("archivo")}>
                    Atrás
                  </Boton>
                  <Boton variante="primario" type="submit" disabled={!titulo.trim() || !abstractValido || !anioValido}>
                    Guardar en el corpus
                  </Boton>
                </div>
              </form>
            )}

            {paso === "guardando" && (
              <div className="subida__guardando" role="status" aria-live="polite">
                <span className="subida__giro" aria-hidden />
                <div>
                  <strong>Guardando y calculando vectores…</strong>
                  <p>
                    El servidor preprocesa el abstract y calcula sus embeddings. La primera vez puede tardar varios segundos mientras se
                    cargan los modelos de IA.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body,
  );
}

/** Zona para soltar o seleccionar el PDF (el input real es accesible con teclado). */
function ZonaArchivo({ archivo, maximo, onElegir }: { archivo: File | null; maximo: number; onElegir: (f: File | undefined) => void }) {
  const [encima, setEncima] = useState(false);
  const soltar = (e: DragEvent) => {
    e.preventDefault();
    setEncima(false);
    onElegir(e.dataTransfer.files[0]);
  };
  return (
    <label
      className={`subida__zona ${encima ? "es-encima" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setEncima(true);
      }}
      onDragLeave={() => setEncima(false)}
      onDrop={soltar}
    >
      <input
        type="file"
        accept=".pdf,application/pdf"
        className="solo-lector"
        onChange={(e) => {
          onElegir(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <FileUp size={22} aria-hidden />
      {archivo ? (
        <span>
          <strong>{archivo.name}</strong>
          <span className="subida__nota">{(archivo.size / 1024).toFixed(0)} KB · haz clic para cambiarlo</span>
        </span>
      ) : (
        <span>
          <strong>Arrastra un PDF aquí o haz clic para elegirlo</strong>
          <span className="subida__nota">Solo .pdf con texto seleccionable, máximo {maximo} MB</span>
        </span>
      )}
    </label>
  );
}
