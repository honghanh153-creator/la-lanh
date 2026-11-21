import { defineConfig, devices } from "@playwright/test";

// One heavy-job slot per port (owner 16.11.2026, 5-fix package item 3b; scripts/collab-heavy-slots.mjs).
// LA_LANH_E2E_PORT moves this run off 4173; inside a slot the run never reuses a server it did not
// start, since that server may belong to the other slot's job.
const requested = Number(process.env.LA_LANH_E2E_PORT);
const port = Number.isInteger(requested) && requested >= 1024 && requested <= 65535 ? requested : 4173;
const origin = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: "./test-results",
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: origin,
    serviceWorkers: "block",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${process.execPath} node_modules/typescript/bin/tsc -b && ${process.execPath} node_modules/vite/bin/vite.js build && ${process.execPath} node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port ${port}`,
    url: origin,
    reuseExistingServer: !process.env.CI && !process.env.LA_LANH_HEAVY_SLOT,
  },
  projects: [
    {
      // Despite the name, the iPhone 13 preset runs WebKit (Safari's engine) at 3x density. On the
      // Linux CI runner WebKit renders in software and is several times slower than on a Mac (#763).
      name: "mobile-chromium",
      use: { ...devices["iPhone 13"], serviceWorkers: "block" },
    },
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"], serviceWorkers: "block" },
    },
  ],
});
