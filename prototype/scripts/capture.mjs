import { chromium } from "/Users/phamhanh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});

const page = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
});

const screens = [
  "welcome",
  "consent",
  "auth",
  "otp",
  "birth",
  "loading",
  "profile",
  "card",
  "home",
  "share",
  "birthTime",
  "moonLoading",
  "moonReveal",
  "saved",
  "profileSettings",
];

for (const screen of screens) {
  await page.goto(`http://127.0.0.1:5173/?screen=${screen}`, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${screen}-screenshot.png`, fullPage: true });
}

await browser.close();
console.log(`Captured ${screens.length} screens`);
