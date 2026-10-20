// Límite de errores: si una vista falla al renderizar se muestra un aviso en lugar de una pantalla en blanco.
import { Component, type ReactNode } from "react";
import { MensajeError } from "./Estado";

interface Props {
  children: ReactNode;
}

export class LimiteError extends Component<Props, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <MensajeError
          mensaje={`La vista encontró un error inesperado: ${this.state.error.message}`}
          reintentar={() => this.setState({ error: null })}
        />
      );
    }
    return this.props.children;
  }
}
