// Fix-forward #969: the browser tests run once per Playwright project (two today). A screenshot
// saved under a fixed file name is written by both, so the second run replaces the first and one
// engine's evidence is lost. Every saved screenshot must carry the project in its path.
/// <reference types="node" />
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const E2E_DIR = join(process.cwd(), "tests/e2e");
const PER_PROJECT = /testInfo\.project\.name|testInfo\.outputPath\(/;

describe("browser test screenshots", () => {
  it("every saved screenshot has the browser project in its path", () => {
    const specs = readdirSync(E2E_DIR).filter((file) => file.endsWith(".spec.ts"));
    expect(specs.length).toBeGreaterThan(0);

    const saved: string[] = [];
    const shared: string[] = [];
    for (const file of specs) {
      const lines = readFileSync(join(E2E_DIR, file), "utf8").split("\n");
      lines.forEach((line, index) => {
        if (!/\.screenshot\(\{[^}]*\bpath:/.test(line)) return;
        saved.push(`${file}:${index + 1}`);
        if (!PER_PROJECT.test(line)) shared.push(`${file}:${index + 1}`);
      });
    }

    // The scan must really see the calls; a rewrite that hides them from it should fail here.
    expect(saved.length).toBeGreaterThan(0);
    expect(shared, "screenshots that two browser projects would overwrite").toEqual([]);
  });
});
