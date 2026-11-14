import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

// Verification run driven by scripts/verify/verify.mjs (skill: .claude/skills/verify-la-lanh).
// Same server as tests/screens: Vite build + preview, every /v1 call mocked with fake data.
// Not part of `pnpm check` and not wired into CI.
const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const port = Number(process.env.VERIFY_PORT ?? 4184);
const widths = (process.env.VERIFY_WIDTHS ?? "360,390")
  .split(",")
  .map((value) => Number(value.trim()))
  .filter((value) => Number.isInteger(value) && value > 0);
const reuseServer = process.env.VERIFY_REUSE_SERVER === "1";

export default defineConfig({
  testDir: ".",
  testMatch: process.env.VERIFY_SPEC ?? "verify.spec.ts",
  outputDir: resolve(webRoot, "test-results/verify-run"),
  reporter: [["list"]],
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    serviceWorkers: "block",
    trace: "off",
  },
  webServer: {
    command: reuseServer
      ? `${process.execPath} node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port ${port} --strictPort`
      : `${process.execPath} node_modules/typescript/bin/tsc -b && ${process.execPath} node_modules/vite/bin/vite.js build && ${process.execPath} node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port ${port} --strictPort`,
    cwd: webRoot,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 240_000,
  },
  projects: widths.map((width) => ({
    name: `w${width}`,
    use: {
      ...devices["iPhone 13"],
      browserName: "chromium" as const,
      viewport: { width, height: 844 },
      locale: "vi-VN",
      timezoneId: "Asia/Ho_Chi_Minh",
      contextOptions: { reducedMotion: "reduce" as const },
      serviceWorkers: "block" as const,
    },
  })),
});
