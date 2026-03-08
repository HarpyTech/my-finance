import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: "app",
  plugins: [react()],
  resolve: {
    // Keep extensionless imports working for JS/JSX modules.
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json"]
  },
  build: {
    outDir: "static",
    emptyOutDir: true
  },
  server: {
    port: 3000
  }
});
