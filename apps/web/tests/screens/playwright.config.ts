import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

// Key-screen screenshots for PR review (ui-screens.yml). Separate from tests/e2e so `pnpm check`
// does not run it. Vite preview only, every /v1 call mocked with fake data.
const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const port = 4183;

export default defineConfig({
  testDir: ".",
  outputDir: resolve(webRoot, "test-results/ui-screens-run"),
  reporter: [["list"]],
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    serviceWorkers: "block",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${process.execPath} node_modules/typescript/bin/tsc -b && ${process.execPath} node_modules/vite/bin/vite.js build && ${process.execPath} node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port ${port} --strictPort`,
    cwd: webRoot,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 180_000,
  },
  projects: [
    {
      name: "phone-390",
      use: {
        ...devices["iPhone 13"],
        browserName: "chromium",
        viewport: { width: 390, height: 844 },
        locale: "vi-VN",
        timezoneId: "Asia/Ho_Chi_Minh",
        contextOptions: { reducedMotion: "reduce" },
        serviceWorkers: "block",
      },
    },
  ],
});
