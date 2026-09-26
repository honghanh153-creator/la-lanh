import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: "./test-results",
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    serviceWorkers: "block",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${process.execPath} node_modules/typescript/bin/tsc -b && ${process.execPath} node_modules/vite/bin/vite.js build && ${process.execPath} node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 4173`,
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    {
      name: "mobile-chromium",
      use: { ...devices["iPhone 13"], serviceWorkers: "block" },
    },
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"], serviceWorkers: "block" },
    },
  ],
});
