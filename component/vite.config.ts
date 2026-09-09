import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// ============================================================================
// Production BROWSER build for the Streamlit Components v2 component.
//
// CRITICAL (known prior failure "BidiComponent Error: process is not defined"):
// the bundle runs in the browser DOM, never in Node. We statically resolve
// NODE_ENV at build time via the bundler's `define` mechanism and verify
// post-build that the final bundle contains zero executable `process`
// references (see scripts/scan_process.py).
// ============================================================================

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    // Statically replace every `process.env.NODE_ENV` reference.
    "process.env.NODE_ENV": JSON.stringify("production"),
    // Any remaining bare `process` identifier (react-dom's unguarded-safe
    // error-report fallback `typeof process`) resolves to `void 0` at build
    // time. The reference is typeof-guarded in the source, so `typeof (void 0)`
    // keeps the branch inert — and the final bundle contains zero `process`
    // identifiers. No runtime polyfill is injected.
    process: "void 0",
  },
  build: {
    lib: {
      entry: "src/component-entry.tsx",
      formats: ["es"],
      fileName: () => "logi-shell.js",
    },
    rollupOptions: {
      output: {
        assetFileNames: (asset) =>
          asset.name?.endsWith(".css") ? "logi-shell.css" : asset.name,
      },
    },
    target: "es2020",
    minify: true,
    cssMinify: true,
    sourcemap: false,
  },
  css: {
    devSourcemap: false,
  },
});
