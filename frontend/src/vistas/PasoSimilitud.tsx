// Panel "paso a paso" de similitud para un par de artículos: fórmula, pasos y detalle visual
// según el algoritmo (matriz DP, tabla TF-IDF, conjuntos o componentes del embedding).
import { api, type ArticuloRef, type ClaveSimilitud, type DetalleCoseno, type DetalleEdicion, type DetalleEmbedding } from "../api";
import { DiagramaConjuntos } from "../componentes/graficos/DiagramaConjuntos";
import { MatrizDP } from "../componentes/graficos/MatrizDP";
import { Dato, formato } from "../componentes/ui/Dato";
import { Aparecer, Cargando, MensajeError } from "../componentes/ui/Estado";
import { Tabla } from "../componentes/ui/Tabla";
import { Tarjeta } from "../componentes/ui/Tarjeta";
import { usePeticion } from "../hooks/usePeticion";

interface Props {
  algoritmo: ClaveSimilitud;
  a: ArticuloRef;
  b: ArticuloRef;
}

export function PasoSimilitud({ algoritmo, a, b }: Props) {
  const { datos: t, cargando, error, recargar } = usePeticion(
    (senal) => api.trazaSimilitud(a.id, b.id, algoritmo, senal),
    [a.id, b.id, algoritmo],
  );

  return (
    <Tarjeta
      className="paso-similitud"
      titulo={
        <>
          Paso a paso{t ? ` · ${t.nombre}` : ""}
        </>
      }
      descripcion={
        <>
          <span className="mono">#{a.id}</span> {a.titulo}
          <br />
          <span className="mono">#{b.id}</span> {b.titulo}
        </>
      }
    >
      {error && <MensajeError mensaje={error} reintentar={recargar} />}
      {cargando && <Cargando lineas={5} />}
      {t && !cargando && (
        <Aparecer>
          <div className="paso-similitud__resumen">
            <Dato rotulo="Similitud" valor={formato(t.similitud, 4)} destacado />
            <div className="formula">
              <span className="rotulo">Fórmula</span>
              <code>{t.formula}</code>
            </div>
          </div>
          <ol className="pasos">
            {t.pasos.map((p, k) => (
              <li key={k}>{p}</li>
            ))}
          </ol>
          {(t.clave === "levenshtein" || t.clave === "needleman_wunsch") && <DetalleEdicionVista d={t.detalle} nw={t.clave === "needleman_wunsch"} />}
          {t.clave === "coseno_tfidf" && <DetalleCosenoVista d={t.detalle} />}
          {t.clave === "jaccard" && <DiagramaConjuntos detalle={t.detalle} etiquetaA={`#${a.id}`} etiquetaB={`#${b.id}`} />}
          {(t.clave === "word2vec" || t.clave === "sbert") && <DetalleEmbeddingVista d={t.detalle} a={a.id} b={b.id} />}
        </Aparecer>
      )}
    </Tarjeta>
  );
}

function DetalleEdicionVista({ d, nw }: { d: DetalleEdicion; nw: boolean }) {
  return (
    <div className="detalle-traza">
      <div className="fila-datos fila-datos--compacta">
        {d.distancia !== undefined && <Dato rotulo="Distancia (texto completo)" valor={d.distancia} />}
        {d.puntaje !== undefined && <Dato rotulo="Puntaje (texto completo)" valor={d.puntaje} />}
        {d.parametros && <Dato rotulo="Parámetros" valor={<span className="mono texto-pequeno">match {d.parametros.match} · mismatch {d.parametros.mismatch} · gap {d.parametros.gap}</span>} />}
        <Dato rotulo="Palabras" valor={`${d.secuencia_a.length} × ${d.secuencia_b.length}`} />
      </div>
      <h4 className="subtitulo">
        Matriz de programación dinámica {d.truncado && <span className="tenue">(primeras 12 × 12 palabras)</span>}
      </h4>
      <MatrizDP secuenciaA={d.secuencia_a} secuenciaB={d.secuencia_b} matriz={d.matriz} camino={d.camino} />
      <p className="nota-grafico">
        <span className="muestra muestra--acento" /> camino óptimo <span className="muestra muestra--exito" /> palabras iguales
      </p>
      {nw && d.alineamiento && (
        <>
          <h4 className="subtitulo">Alineamiento global</h4>
          <div className="alineamiento" role="table" aria-label="Alineamiento de las dos secuencias">
            {d.alineamiento.a.slice(0, 60).map((p, k) => {
              const q = d.alineamiento!.b[k];
              const tipo = p === "-" || q === "-" ? "hueco" : p === q ? "igual" : "distinto";
              return (
                <span key={k} className={`alineamiento__col es-${tipo}`} role="row">
                  <span role="cell">{p}</span>
                  <span role="cell">{q}</span>
                </span>
              );
            })}
            {d.alineamiento.a.length > 60 && <span className="tenue alineamiento__mas">+{d.alineamiento.a.length - 60} columnas</span>}
          </div>
        </>
      )}
    </div>
  );
}

function DetalleCosenoVista({ d }: { d: DetalleCoseno }) {
  const rad = (d.angulo_grados * Math.PI) / 180;
  return (
    <div className="detalle-traza">
      <div className="coseno-resumen">
        <svg viewBox="0 0 120 90" className="angulo" role="img" aria-label={`Ángulo de ${d.angulo_grados.toFixed(1)} grados entre los vectores`}>
          <line x1="10" y1="80" x2="110" y2="80" className="angulo__vector" />
          <line x1="10" y1="80" x2={10 + 100 * Math.cos(rad)} y2={80 - 100 * Math.sin(rad)} className="angulo__vector angulo__vector--acento" />
          <path d={`M40,80 A30,30 0 0,0 ${10 + 30 * Math.cos(rad)},${80 - 30 * Math.sin(rad)}`} className="angulo__arco" />
          <text x="48" y="72" className="eje-texto">θ</text>
        </svg>
        <div className="fila-datos fila-datos--compacta">
          <Dato rotulo="A · B" valor={formato(d.producto_punto, 4)} />
          <Dato rotulo="‖A‖" valor={formato(d.norma_a, 4)} />
          <Dato rotulo="‖B‖" valor={formato(d.norma_b, 4)} />
          <Dato rotulo="Ángulo θ" valor={`${d.angulo_grados.toFixed(1)}°`} />
        </div>
      </div>
      <h4 className="subtitulo">Términos con mayor aporte al producto punto</h4>
      <Tabla
        titulo="Pesos TF-IDF por término"
        densa
        filas={d.terminos}
        claveFila={(f) => f.termino}
        resaltar={(f) => f.peso_a > 0 && f.peso_b > 0}
        columnas={[
          { clave: "t", titulo: "Término", celda: (f) => <span className="mono">{f.termino}</span> },
          { clave: "tfa", titulo: "tf A", numerica: true, celda: (f) => f.tf_a.toFixed(4) },
          { clave: "tfb", titulo: "tf B", numerica: true, celda: (f) => f.tf_b.toFixed(4) },
          { clave: "idf", titulo: "idf", numerica: true, celda: (f) => f.idf.toFixed(3) },
          { clave: "pa", titulo: "peso A", numerica: true, celda: (f) => f.peso_a.toFixed(4) },
          { clave: "pb", titulo: "peso B", numerica: true, celda: (f) => f.peso_b.toFixed(4) },
          { clave: "pp", titulo: "A·B", numerica: true, celda: (f) => (f.peso_a * f.peso_b).toFixed(5) },
        ]}
      />
    </div>
  );
}

function DetalleEmbeddingVista({ d, a, b }: { d: DetalleEmbedding; a: number; b: number }) {
  const max = Math.max(...d.vector_a.map(Math.abs), ...d.vector_b.map(Math.abs), 1e-6);
  const alto = 120;
  const medio = alto / 2;
  const paso = 22;
  return (
    <div className="detalle-traza">
      <div className="fila-datos fila-datos--compacta">
        <Dato rotulo="Modelo" valor={<span className="texto-pequeno">{d.modelo}</span>} nota={`${d.dimensiones} dimensiones`} />
        <Dato rotulo="Coseno" valor={formato(d.coseno, 4)} />
        <Dato rotulo="Producto punto" valor={formato(d.producto_punto, 4)} />
        <Dato rotulo="Distancia euclidiana" valor={formato(d.distancia_euclidiana, 4)} />
        <Dato rotulo="Normas" valor={`${formato(d.norma_a, 2)} · ${formato(d.norma_b, 2)}`} />
        {d.cobertura_a !== undefined && (
          <Dato rotulo="Cobertura del vocabulario" valor={`${Math.round(d.cobertura_a * 100)}% · ${Math.round((d.cobertura_b ?? 0) * 100)}%`} />
        )}
      </div>
      <h4 className="subtitulo">Primeras {d.vector_a.length} componentes</h4>
      <div className="grafico">
        <svg width={d.vector_a.length * paso + 8} height={alto + 20} role="img" aria-label="Componentes de los vectores A y B">
          <line x1="0" x2={d.vector_a.length * paso + 8} y1={medio} y2={medio} className="rejilla" />
          {d.vector_a.map((va, k) => {
            const vb = d.vector_b[k] ?? 0;
            const ha = (Math.abs(va) / max) * (medio - 4);
            const hb = (Math.abs(vb) / max) * (medio - 4);
            return (
              <g key={k}>
                <rect x={4 + k * paso} y={va >= 0 ? medio - ha : medio} width={8} height={ha} fill="var(--acento)">
                  <title>{`#${a}[${k}] = ${va}`}</title>
                </rect>
                <rect x={4 + k * paso + 9} y={vb >= 0 ? medio - hb : medio} width={8} height={hb} fill="var(--tinta-3)">
                  <title>{`#${b}[${k}] = ${vb}`}</title>
                </rect>
                <text x={4 + k * paso + 8} y={alto + 14} textAnchor="middle" className="eje-texto">
                  {k}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <p className="nota-grafico">
        <span className="muestra muestra--acento" /> #{a} <span className="muestra" /> #{b}
      </p>
    </div>
  );
}
