import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

/* The engine is not copied into this app. It stays at web/engine.js and is
   imported from there, so the browser app, the old pages and the Python
   engines all still describe one set of rules. Two copies would drift, and a
   cost that disagrees with itself is worse than no cost at all. */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@engine": resolve(__dirname, "../web/engine.js"),
      "@scene3d": resolve(__dirname, "../web/scene3d.js"),
      "@exports": resolve(__dirname, "../web/exports.js"),
    },
  },
  server: {
    fs: { allow: [resolve(__dirname), resolve(__dirname, "../web")] },
    proxy: { "/auth": "http://127.0.0.1:8000", "/projects": "http://127.0.0.1:8000",
             "/health": "http://127.0.0.1:8000", "/cortex": "http://127.0.0.1:8000",
             "/plans": "http://127.0.0.1:8000" },
  },
  build: { outDir: "dist", sourcemap: true },
});
