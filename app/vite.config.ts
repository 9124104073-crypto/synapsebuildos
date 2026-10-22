import { readFile, readdir } from "node:fs/promises";
import { extname, relative, resolve, sep } from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const legacyRoot = resolve(import.meta.dirname, "../web");
const contentTypes: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".pdf": "application/pdf",
  ".wasm": "application/wasm",
  ".gz": "application/gzip",
};

async function legacyFiles(dir = legacyRoot): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = await Promise.all(entries.map(entry => {
    const path = resolve(dir, entry.name);
    return entry.isDirectory() ? legacyFiles(path) : [path];
  }));
  return files.flat();
}

function legacyPages(): Plugin {
  return {
    name: "legacy-pages",
    configureServer(server) {
      server.middlewares.use("/legacy", async (req, res, next) => {
        try {
          const pathname = decodeURIComponent((req.url || "/").split("?", 1)[0]);
          const requested = pathname === "/" ? "/index.html" : pathname;
          const file = resolve(legacyRoot, `.${requested}`);
          if (!file.startsWith(`${legacyRoot}${sep}`)) return next();
          const source = await readFile(file);
          res.statusCode = 200;
          res.setHeader("Content-Type", contentTypes[extname(file)] || "application/octet-stream");
          res.end(source);
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code === "ENOENT") return next();
          next(error as Error);
        }
      });
    },
    async buildStart() {
      for (const file of await legacyFiles()) {
        this.emitFile({
          type: "asset",
          fileName: `legacy/${relative(legacyRoot, file).replaceAll("\\", "/")}`,
          source: await readFile(file),
        });
      }
    },
  };
}

const modules = resolve(import.meta.dirname, "node_modules");
const coreRoot = resolve(modules, "tesseract.js-core");
let ocrManifest: Promise<{ name: string; file: string }[]> | null = null;

function ocrFiles() {
  return ocrManifest ||= readdir(coreRoot).then(coreFiles => [
    { name: "pdf.min.mjs", file: resolve(modules, "pdfjs-dist/build/pdf.min.mjs") },
    { name: "pdf.worker.min.mjs", file: resolve(modules, "pdfjs-dist/build/pdf.worker.min.mjs") },
    { name: "jszip.min.js", file: resolve(modules, "jszip/dist/jszip.min.js") },
    { name: "tesseract.min.js", file: resolve(modules, "tesseract.js/dist/tesseract.min.js") },
    { name: "worker.min.js", file: resolve(modules, "tesseract.js/dist/worker.min.js") },
    { name: "lang/eng.traineddata.gz", file: resolve(modules, "@tesseract.js-data/eng/4.0.0/eng.traineddata.gz") },
    ...coreFiles
      .filter(name => name.startsWith("tesseract-core") && (name.endsWith(".js") || name.endsWith(".wasm")))
      .map(name => ({ name: `core/${name}`, file: resolve(coreRoot, name) })),
  ]);
}

function ocrAssets(): Plugin {
  return {
    name: "ocr-assets",
    configureServer(server) {
      server.middlewares.use("/ocr-assets", async (req, res, next) => {
        try {
          const requested = decodeURIComponent((req.url || "/").split("?", 1)[0]).replace(/^\/+/, "");
          const file = (await ocrFiles()).find(asset => asset.name === requested)?.file;
          if (!file) return next();
          res.statusCode = 200;
          res.setHeader("Content-Type", contentTypes[extname(file)] || "application/octet-stream");
          res.end(await readFile(file));
        } catch (error) {
          next(error as Error);
        }
      });
    },
    async buildStart() {
      for (const asset of await ocrFiles()) {
        this.emitFile({ type: "asset", fileName: `ocr-assets/${asset.name}`, source: await readFile(asset.file) });
      }
    },
  };
}

/* The engine is not copied into this app. It stays at web/engine.js and is
   imported from there, so the browser app, the old pages and the Python
   engines all still describe one set of rules. Two copies would drift, and a
   cost that disagrees with itself is worse than no cost at all. */
export default defineConfig({
  plugins: [legacyPages(), ocrAssets(), react()],
  resolve: {
    alias: {
      "@engine": resolve(import.meta.dirname, "../web/engine.js"),
      "@scene3d": resolve(import.meta.dirname, "../web/scene3d.js"),
      "@exports": resolve(import.meta.dirname, "../web/exports.js"),
    },
  },
  // The dev server proxies the API so the browser sees one origin, the same
  // way the deployment does. Port 8001 because another project on this
  // machine holds 8000.
  server: {
    port: 5174,
    fs: { allow: [import.meta.dirname, legacyRoot] },
    proxy: { "/auth": "http://127.0.0.1:8001", "/projects": "http://127.0.0.1:8001",
             "/health": "http://127.0.0.1:8001", "/cortex": "http://127.0.0.1:8001",
             "/plans": "http://127.0.0.1:8001" },
  },
  build: { outDir: "dist", sourcemap: true },
});
