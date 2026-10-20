// Diagrama de dos conjuntos (Venn) para Jaccard: tamaños y términos de cada región.
import type { DetalleJaccard } from "../../api";

export function DiagramaConjuntos({ detalle, etiquetaA, etiquetaB }: { detalle: DetalleJaccard; etiquetaA: string; etiquetaB: string }) {
  const { solo_a, solo_b, interseccion, tam_union } = detalle;
  return (
    <div className="conjuntos">
      <svg viewBox="0 0 320 170" className="conjuntos__svg" role="img" aria-label={`Diagrama de conjuntos: ${interseccion.length} términos comunes de ${tam_union}`}>
        <circle cx="120" cy="85" r="72" className="conjuntos__a" />
        <circle cx="200" cy="85" r="72" className="conjuntos__b" />
        <text x="82" y="90" textAnchor="middle" className="conjuntos__cifra">{solo_a.length}</text>
        <text x="160" y="90" textAnchor="middle" className="conjuntos__cifra conjuntos__cifra--acento">{interseccion.length}</text>
        <text x="238" y="90" textAnchor="middle" className="conjuntos__cifra">{solo_b.length}</text>
        <text x="82" y="160" textAnchor="middle" className="eje-texto">{etiquetaA}</text>
        <text x="238" y="160" textAnchor="middle" className="eje-texto">{etiquetaB}</text>
      </svg>
      <div className="conjuntos__listas">
        <ListaTerminos titulo={`Solo ${etiquetaA}`} terminos={solo_a} />
        <ListaTerminos titulo="A ∩ B" terminos={interseccion} acento />
        <ListaTerminos titulo={`Solo ${etiquetaB}`} terminos={solo_b} />
      </div>
    </div>
  );
}

function ListaTerminos({ titulo, terminos, acento }: { titulo: string; terminos: string[]; acento?: boolean }) {
  return (
    <div className="conjuntos__lista">
      <h4 className={acento ? "texto-acento" : ""}>
        {titulo} <span className="tenue">({terminos.length})</span>
      </h4>
      <p>
        {terminos.slice(0, 40).map((t) => (
          <span key={t} className={`termino ${acento ? "termino--acento" : ""}`}>
            {t}
          </span>
        ))}
        {terminos.length > 40 && <span className="tenue"> +{terminos.length - 40} más</span>}
      </p>
    </div>
  );
}
