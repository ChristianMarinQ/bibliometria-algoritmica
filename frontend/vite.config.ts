import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configuración de Vite: React + puerto fijo para el desarrollo.
export default defineConfig({
  plugins: [react()],
  // Puertos fijos: el backend solo permite CORS desde localhost:5173 (dev) y :4173 (preview).
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
});
