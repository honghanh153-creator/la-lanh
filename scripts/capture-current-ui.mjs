import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { chromium } from "/Users/phamhanh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const baseUrl = process.env.LA_LANH_CAPTURE_URL ?? "http://127.0.0.1:5202";
const outputDir = new URL("../docs/reviews/ui-audit-2026-09-28/final/", import.meta.url);

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 1,
  isMobile: true,
});
const page = await context.newPage();

async function capture(name, path) {
  await page.goto(`${baseUrl}${path}`, { waitUntil: "networkidle" });
  await page.screenshot({ path: fileURLToPath(new URL(`${name}.png`, outputDir)), fullPage: true });
}

await capture("02-welcome", "/welcome");
await capture("03-consent-alias", "/consent");

await page.goto(`${baseUrl}/tarot`, { waitUntil: "networkidle" });
await page.getByPlaceholder("Ví dụ: Mình nên nói rõ hay chờ thêm?").fill("Mình nên nói rõ hay chờ thêm?");
await page.screenshot({ path: fileURLToPath(new URL("01-tarot-question-first.png", outputDir)), fullPage: true });

await page.goto(`${baseUrl}/welcome`, { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Đồng ý & bắt đầu" }).click();
await page.waitForURL("**/birth");
await page.getByPlaceholder("DD").fill("15");
await page.getByPlaceholder("MM").fill("03");
await page.getByPlaceholder("YYYY").fill("1990");
await page.screenshot({ path: fileURLToPath(new URL("04-birth.png", outputDir)), fullPage: true });
await page.getByRole("button", { name: "Khớp tín hiệu" }).click();
await page.waitForURL("**/reveal", { timeout: 30_000 });
await page.screenshot({ path: fileURLToPath(new URL("05-reveal.png", outputDir)), fullPage: true });
await page.getByRole("button", { name: "Mở Note hôm nay" }).click();
await page.waitForURL("**/home", { timeout: 30_000 });
await page.screenshot({ path: fileURLToPath(new URL("06-home.png", outputDir)), fullPage: true });

await browser.close();
console.log(`Captured current UI to ${outputDir.pathname}`);
