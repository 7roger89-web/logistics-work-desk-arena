// ============================================================================
// Tiny TS loader for focused unit tests of PURE component libs.
//
// Uses the project's OWN installed TypeScript compiler (`component/node_modules
// /.bin/tsc`) to emit plain JS into a temp dir, then imports it. No new
// dependency, no second bundler config, no runtime transform framework.
// ============================================================================

import { mkdtempSync, mkdirSync, cpSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const TSC = path.join(ROOT, "component/node_modules/.bin/tsc");

let outDir = null;

/** Compile `component/src/lib/*.ts` once, then import one emitted module. */
export async function importTs(relPath) {
  if (!outDir) {
    outDir = mkdtempSync(path.join(tmpdir(), "logi-lib-"));
    const srcDir = path.join(outDir, "src");
    mkdirSync(srcDir, { recursive: true });
    cpSync(path.join(ROOT, "component/src/lib"), srcDir, { recursive: true });
    execFileSync(
      TSC,
      [
        "--target", "es2022", "--module", "esnext", "--moduleResolution", "bundler",
        "--skipLibCheck", "--noEmitOnError", "false",
        "--outDir", path.join(outDir, "out"),
        path.join(srcDir, "quoteTextParser.ts"),
        path.join(srcDir, "miniCalc.ts"),
        path.join(srcDir, "costHistory.ts"),
      ],
      { stdio: "pipe" }
    );
  }
  const name = path.basename(relPath).replace(/\.ts$/, ".js");
  return import(pathToFileURL(path.join(outDir, "out", name)).href);
}
