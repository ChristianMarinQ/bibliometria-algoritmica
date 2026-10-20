// Vista Req. 3 — Búsqueda de patrones: resultados con coincidencias en contexto, tabla
// comparativa de KMP / Boyer-Moore / Rabin-Karp y visualizador paso a paso de la traza.
import { useEffect, useState, type FormEvent } from "react";
import { api, type ClaveBusqueda, type RespuestaBusqueda } from "../api";
import { BarrasHorizontales } from "../componentes/graficos/BarrasHorizontales";
import { Boton } from "../componentes/ui/Boton";
import { entero, formatoMs } from "../componentes/ui/Dato";
import { EncabezadoVista } from "../componentes/ui/EncabezadoVista";
import { Aparecer, Cargando, MensajeError, Vacio } from "../componentes/ui/Estado";
import { Search } from "../componentes/ui/Icono";
import { Lista, Segmentado } from "../componentes/ui/Selector";
import { Tabla } from "../componentes/ui/Tabla";
import { Tarjeta } from "../componentes/ui/Tarjeta";
import { useEjecucion, usePeticion } from "../hooks/usePeticion";
import { useVersionCorpus } from "../hooks/useCorpus";
import { VisualizadorTraza } from "./VisualizadorTraza";

export function VistaBusqueda() {
  const [patron, setPatron] = useState("learning");
  const [mayusculas, setMayusculas] = useState(false);
  const { datos: resultado, cargando, error, ejecutar } = useEjecucion<RespuestaBusqueda>();
  // Opción de mayúsculas con la que se hizo la última búsqueda (la traza debe usar la misma).
  const [mayusculasBuscadas, setMayusculasBuscadas] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const buscar = (e?: FormEvent) => {
    e?.preventDefault();
    if (!patron.trim()) {
      setAviso("Escriba un patrón para buscar (al menos un carácter distinto de espacio).");
      return;
    }
    setAviso(null);
    const distinguir = mayusculas;
    void ejecutar(
      (senal) => api.busqueda({ patron, ids: null, distinguir_mayusculas: distinguir }, senal),
      () => setMayusculasBuscadas(distinguir),
    );
  };

  useEffect(() => {
    void buscar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalCoincidencias = resultado?.resultados.reduce((s, r) => s + r.posiciones.length, 0) ?? 0;

  return (
    <div className="vista">
      <EncabezadoVista antetitulo="Requerimiento 3" titulo="Búsqueda de patrones">
        <p>
          Tres algoritmos de coincidencia exacta recorren los 20 abstracts. KMP evita re-comparar gracias a la tabla de bordes,
          Boyer-Moore compara de derecha a izquierda y salta con dos heurísticas, y Rabin-Karp filtra ventanas por hash.
        </p>
      </EncabezadoVista>

      <form className="buscador" onSubmit={buscar}>
        <label className="campo campo--busqueda campo--grande">
          <Search size={18} aria-hidden />
          <span className="solo-lector">Patrón a buscar</span>
          <input
            value={patron}
            onChange={(e) => {
              setPatron(e.target.value);
              setAviso(null);
            }}
            placeholder="Patrón, p. ej. learning"
            maxLength={80}
            aria-invalid={aviso ? true : undefined}
            aria-describedby={aviso ? "aviso-patron" : undefined}
          />
        </label>
        <label className="casilla">
          <input type="checkbox" checked={mayusculas} onChange={(e) => setMayusculas(e.target.checked)} />
          Distinguir mayúsculas
        </label>
        <Boton variante="primario" type="submit" disabled={cargando}>
          {cargando ? "Buscando…" : "Buscar"}
        </Boton>
      </form>
      {aviso && (
        <p id="aviso-patron" className="aviso" role="alert">
          {aviso}
        </p>
      )}

      {error && <MensajeError mensaje={error} reintentar={() => buscar()} />}
      {cargando && !resultado && <Cargando alto={220} />}

      {resultado && (
        <Aparecer className={cargando ? "es-recargando" : ""}>
          <div className="rejilla-dos rejilla-dos--ancha">
            <Tarjeta
              titulo="Comparación de algoritmos"
              descripcion={
                <>
                  Patrón <code>“{resultado.patron}”</code> ·{" "}
                  {resultado.coinciden ? (
                    <span className="texto-exito">los tres algoritmos hallaron las mismas posiciones</span>
                  ) : (
                    <span className="texto-acento">los algoritmos difieren en las posiciones encontradas</span>
                  )}
                </>
              }
            >
              <Tabla
                titulo="Métricas por algoritmo de búsqueda"
                filas={resultado.algoritmos}
                claveFila={(a) => a.clave}
                columnas={[
                  { clave: "n", titulo: "Algoritmo", celda: (a) => a.nombre },
                  { clave: "p", titulo: "Preproceso", numerica: true, celda: (a) => formatoMs(a.tiempo_preprocesamiento_ms) },
                  { clave: "b", titulo: "Búsqueda", numerica: true, celda: (a) => formatoMs(a.tiempo_busqueda_ms) },
                  { clave: "c", titulo: "Comparaciones", numerica: true, celda: (a) => entero(a.comparaciones) },
                  { clave: "m", titulo: "Coincidencias", numerica: true, celda: (a) => a.total_coincidencias },
                ]}
              />
            </Tarjeta>
            <Tarjeta titulo="Comparaciones de caracteres" descripcion="Menos es mejor; mide el trabajo real del algoritmo.">
              <BarrasHorizontales
                titulo="Comparaciones por algoritmo"
                formato={entero}
                barras={resultado.algoritmos.map((a) => ({
                  clave: a.clave,
                  etiqueta: a.nombre,
                  valor: a.comparaciones,
                  destacada: a.comparaciones === Math.min(...resultado.algoritmos.map((x) => x.comparaciones)),
                }))}
              />
            </Tarjeta>
          </div>

          <Tarjeta
            titulo="Coincidencias en contexto"
            descripcion={`${totalCoincidencias} apariciones en ${resultado.resultados.length} artículos del corpus.`}
          >
            {resultado.resultados.length === 0 && <Vacio>El patrón no aparece en ningún abstract.</Vacio>}
            <ul className="resultados">
              {resultado.resultados.map((r) => (
                <li key={r.articulo_id} className="resultado">
                  <div className="resultado__cabecera">
                    <span className="mono tenue">#{r.articulo_id}</span>
                    <span className="resultado__titulo">{r.titulo}</span>
                    <span className="insignia">{r.posiciones.length}</span>
                  </div>
                  <ul className="fragmentos">
                    {r.fragmentos.slice(0, 4).map((f) => (
                      <li key={f.posicion}>
                        <span className="mono tenue fragmentos__pos">{f.posicion}</span>
                        <span className="fragmentos__texto">
                          {f.antes}
                          <mark>{f.coincidencia}</mark>
                          {f.despues}
                        </span>
                      </li>
                    ))}
                    {r.fragmentos.length > 4 && <li className="tenue texto-pequeno">+{r.fragmentos.length - 4} más</li>}
                  </ul>
                </li>
              ))}
            </ul>
          </Tarjeta>

          {/* La key reinicia el artículo elegido al cambiar de búsqueda. */}
          <PanelTraza
            key={`${resultado.patron}-${mayusculasBuscadas}`}
            patron={resultado.patron}
            distinguirMayusculas={mayusculasBuscadas}
            idsConCoincidencia={resultado.resultados.map((r) => r.articulo_id)}
          />
        </Aparecer>
      )}
    </div>
  );
}

/** Selección de algoritmo y artículo para la traza paso a paso. */
interface PropsPanelTraza {
  patron: string;
  distinguirMayusculas: boolean;
  idsConCoincidencia: number[];
}

function PanelTraza({ patron, distinguirMayusculas, idsConCoincidencia }: PropsPanelTraza) {
  const versionCorpus = useVersionCorpus();
  const corpus = usePeticion((senal) => api.articulos(senal), [versionCorpus]);
  const [algoritmo, setAlgoritmo] = useState<ClaveBusqueda>("boyer_moore");
  // Por defecto, el primer artículo que contiene el patrón (o el 3, buen ejemplo para "learning").
  const [articulo, setArticulo] = useState<number>(idsConCoincidencia.includes(3) ? 3 : idsConCoincidencia[0] ?? 1);
  const traza = usePeticion(
    (senal) =>
      api.trazaBusqueda(
        { patron, algoritmo, articulo_id: articulo, max_caracteres: 300, distinguir_mayusculas: distinguirMayusculas },
        senal,
      ),
    [patron, algoritmo, articulo, distinguirMayusculas],
  );

  return (
    <Tarjeta
      titulo="Traza paso a paso"
      descripcion="Fragmento de 300 caracteres del abstract elegido (centrado en la primera aparición si no está al inicio). Pulse sobre el visualizador y use ← y → para avanzar o la barra espaciadora para reproducir."
      acciones={
        <div className="controles-traza">
          <Segmentado
            etiqueta="Algoritmo de la traza"
            valor={algoritmo}
            onCambio={setAlgoritmo}
            opciones={[
              { valor: "kmp", etiqueta: "KMP" },
              { valor: "boyer_moore", etiqueta: "Boyer-Moore" },
              { valor: "rabin_karp", etiqueta: "Rabin-Karp" },
            ]}
          />
          <Lista
            etiqueta="Artículo"
            valor={articulo}
            onCambio={setArticulo}
            opciones={(corpus.datos ?? [{ id: articulo, titulo: "" }]).map((a) => ({
              valor: a.id,
              etiqueta: `#${a.id}${idsConCoincidencia.includes(a.id) ? " ●" : ""} ${a.titulo.slice(0, 38)}${a.titulo.length > 38 ? "…" : ""}`,
            }))}
          />
        </div>
      }
    >
      {traza.error && <MensajeError mensaje={traza.error} reintentar={traza.recargar} />}
      {traza.cargando && !traza.datos && <Cargando alto={180} />}
      {traza.datos && (
        <VisualizadorTraza
          key={`${traza.datos.clave}-${traza.datos.articulo_id ?? articulo}-${traza.datos.patron}`}
          traza={traza.datos}
        />
      )}
    </Tarjeta>
  );
}
