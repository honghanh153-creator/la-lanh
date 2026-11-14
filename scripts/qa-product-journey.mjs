#!/usr/bin/env node
// Post-release product journey: walks the public app like a new user on a phone, with synthetic
// birth data only, records what each screen shows and how fast, then deletes the synthetic guest.
//
// Usage: LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only node scripts/qa-product-journey.mjs <origin> <out-dir>
//
// Output (for the Claude and Codex product reviews; never contains cookies, tokens or IDs):
//   <out-dir>/journey.json   per step: route (IDs redacted), ok, load time, blank time, layout checks, errors
//   <out-dir>/shots/*.png    one screenshot per step (390 px wide, 2x)
//   <out-dir>/text/*.txt     the visible text of each step, for copy review
// Exit code: 0 when every required step passed and the guest was deleted, 1 otherwise.
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { LOADING, PERSONA, redactRoute } from "./qa-journey-lib.mjs";

const here = fileURLToPath(new URL(".", import.meta.url));
const requireFromWeb = createRequire(resolve(here, "../apps/web/package.json"));
const { chromium } = requireFromWeb("@playwright/test");

const origin = new URL(process.argv[2] ?? "").origin;
const outDir = resolve(process.argv[3] ?? "");
if (process.env.LA_LANH_SMOKE_WRITE_CONSENT !== "synthetic-only") {
  console.error("Set LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only to create and delete QA-only data.");
  process.exit(2);
}
if (!origin.startsWith("https://") && !origin.startsWith("http://127.0.0.1:")) {
  console.error("Origin must be https:// or a local 127.0.0.1 server.");
  process.exit(2);
}
if (!process.argv[3]) {
  console.error("Usage: qa-product-journey.mjs <origin> <out-dir>");
  process.exit(2);
}
mkdirSync(join(outDir, "shots"), { recursive: true });
mkdirSync(join(outDir, "text"), { recursive: true });

const steps = [];
const consoleErrors = [];
const serverErrors = [];
let index = 0;

async function measure(page, minText = 80, before = null) {
  // Ready time: until the main area shows real content rather than a loading line.
  const started = Date.now();
  let readyMs = null;
  let sawLoading = false;
  while (Date.now() - started < 20_000) {
    const text = await page
      .evaluate(() => (document.querySelector("main")?.innerText ?? "").replace(/\s+/g, " ").trim())
      .catch(() => "");
    const loading = LOADING.test(text.slice(0, 200));
    sawLoading ||= loading;
    const moved = !before || page.url() === before.url || text !== before.text;
    if (text.length > minText && !loading && moved) {
      readyMs = Date.now() - started;
      break;
    }
    await page.waitForTimeout(150);
  }
  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
  if (readyMs === null) throw new Error("still loading or empty after 20 s");
  return { readyMs, sawLoading };
}

async function layout(page) {
  return page.evaluate(() => {
    const width = window.innerWidth;
    const overflowX = document.documentElement.scrollWidth > width + 1;
    const small = [];
    for (const el of document.querySelectorAll("a[href], button, input, select, [role=button]")) {
      const style = getComputedStyle(el);
      if (style.visibility === "hidden" || style.display === "none" || el.offsetParent === null) continue;
      if (el.matches("input[type=checkbox], input[type=radio]")) continue;
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      if (rect.height < 44 || rect.width < 44) {
        small.push(`${el.tagName.toLowerCase()} "${(el.getAttribute("aria-label") || el.textContent || "").trim().slice(0, 40)}" ${Math.round(rect.width)}x${Math.round(rect.height)}`);
      }
    }
    const h1 = document.querySelectorAll("h1").length;
    return { overflowX, smallTargets: small.slice(0, 12), smallTargetCount: small.length, h1 };
  });
}

async function step(page, name, action, { required = true, minText = 80 } = {}) {
  index += 1;
  const id = `${String(index).padStart(2, "0")}-${name}`;
  const record = { id, name, required, ok: false };
  const startedAt = Date.now();
  const mainText = () => page.evaluate(() => (document.querySelector("main")?.innerText ?? "").replace(/\s+/g, " ").trim()).catch(() => "");
  const before = { url: page.url(), text: await mainText() };
  try {
    await action();
    Object.assign(record, await measure(page, minText, before));
    record.actionMs = Date.now() - startedAt;
    record.ok = true;
  } catch (error) {
    record.error = String(error?.message ?? error).split("\n")[0].slice(0, 200);
    record.buttons = await page
      .$$eval("button, a[href]", (els) => els.filter((e) => e.offsetParent !== null).map((e) => e.textContent.trim().slice(0, 30)).slice(0, 25))
      .catch(() => []);
  }
  record.route = redactRoute(page.url());
  try {
    Object.assign(record, await layout(page));
    await page.screenshot({ path: join(outDir, "shots", `${id}.png`) });
    const text = await page.locator("body").innerText({ timeout: 5_000 });
    writeFileSync(join(outDir, "text", `${id}.txt`), text);
  } catch (error) {
    record.captureError = String(error?.message ?? error).split("\n")[0].slice(0, 200);
  }
  steps.push(record);
  console.log(`${record.ok ? "ok  " : "FAIL"} ${id} ${record.route} ${record.readyMs ?? "-"}ms${record.error ? ` ${record.error}` : ""}`);
  return record.ok;
}

const button = (page, name) => page.getByRole("button", { name }).first();
const link = (page, name) => page.getByRole("link", { name }).first();
const go = (page, path) => page.goto(`${origin}${path}`, { waitUntil: "domcontentloaded" });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
  locale: "vi-VN",
  timezoneId: "Asia/Ho_Chi_Minh",
  serviceWorkers: "block",
});
const page = await context.newPage();
page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text().replace(/[A-Za-z0-9_-]{24,}/g, ":redacted").slice(0, 160));
});
page.on("response", (response) => {
  if (response.status() >= 500) serverErrors.push(`${response.status()} ${redactRoute(response.url())}`);
});

let deleted = false;
try {
  await step(page, "welcome", () => go(page, "/"));
  await step(page, "birth-date", async () => {
    await button(page, "Đồng ý & bắt đầu").click();
    await page.getByPlaceholder("DD").waitFor();
  });
  await step(page, "birth-time-place", async () => {
    await page.getByPlaceholder("DD").fill(PERSONA.day);
    await page.getByPlaceholder("MM").fill(PERSONA.month);
    await page.getByPlaceholder("YYYY").fill(PERSONA.year);
    await button(page, /Thêm giờ & nơi sinh/).click();
    await button(page, "Biết giờ").click();
    const selects = page.locator("select");
    await selects.nth(0).selectOption(PERSONA.hour);
    await selects.nth(1).selectOption(PERSONA.minute);
    await page.getByPlaceholder("Tìm thành phố / tỉnh").fill(PERSONA.place);
    await button(page, new RegExp(`^${PERSONA.place}, Việt Nam`)).click();
    await page.locator("input[type=checkbox]").first().check();
  });
  await step(page, "reveal", async () => {
    await page.getByRole("button", { name: /Khớp tín hiệu|Tiếp tục|Xem/ }).last().click();
    await page.waitForURL((url) => !url.pathname.startsWith("/birth"), { timeout: 30_000 });
  });
  await step(page, "home", async () => {
    await go(page, "/home");
    await page.getByText("HÔM NAY CỦA BẠN", { exact: false }).first().waitFor({ timeout: 20_000 });
  });
  await step(page, "note-full", async () => {
    await page.getByText("Đọc đầy đủ").first().click();
    await page.waitForURL(/\/note\/today/);
  });
  await step(page, "note-direct", () => go(page, "/note/today"), { required: false });
  await step(page, "share-link", async () => {
    await page.getByRole("link", { name: "Chia sẻ" }).first().click();
    await page.waitForURL(/\/card/);
    await button(page, /Tạo safe link/).click();
    await button(page, /Thu hồi link/).waitFor({ timeout: 20_000 });
  }, { minText: 10 });
  await step(page, "share-revoke", async () => {
    await button(page, /Thu hồi link/).click();
    await button(page, /Thu hồi link/).waitFor({ state: "detached", timeout: 20_000 });
  }, { minText: 10 });
  await step(page, "mood", async () => {
    await go(page, "/home");
    await button(page, /Chọn mood/).click();
    await button(page, /Chill/).click();
    await page.waitForTimeout(1500);
  }, { required: false });
  await step(page, "insights-overview", () => go(page, "/insights"));
  await step(page, "insights-jyotish", () => go(page, "/insights/overview?tradition=jyotish"));
  await step(page, "current-sky", () => go(page, "/insights/current-sky"));
  await step(page, "aura", () => go(page, "/reveal/aura"));
  await step(page, "birth-card", () => go(page, "/birth-card"), { required: false });
  await step(page, "tarot", () => go(page, "/tarot"));
  await step(page, "tarot-1", async () => {
    await page.locator("textarea").fill("Tuần này mình nên tập trung vào việc gì?");
    await button(page, /^1 lá/).click();
    await button(page, /^Xòe 1 lá/).click();
    await page.locator("[data-fan-index]").first().waitFor({ timeout: 20_000 });
  });
  await step(page, "tarot-result", async () => {
    const card = page.locator("[data-fan-index]").nth(7);
    await card.scrollIntoViewIfNeeded();
    await card.evaluate((el) => el.click());
    await page.getByText("Chưa chọn").waitFor({ state: "detached", timeout: 20_000 });
    await page.waitForTimeout(4000);
  });
  await step(page, "radar", () => go(page, "/radar"));
  await step(page, "saved", () => go(page, "/saved"), { required: false });
  await step(page, "profile", () => go(page, "/profile"));
  await step(page, "delete", async () => {
    await page.getByText("Dữ liệu & quyền riêng tư").first().click();
    await button(page, /Xóa Lá và dữ liệu/).click();
    await page.waitForTimeout(800);
    // Confirm in whatever dialog the app shows.
    const confirm = page.getByRole("button", { name: /^(Xóa|Xoá)/ }).last();
    await confirm.click();
    await page.waitForURL((url) => /\/(welcome|)$/.test(url.pathname), { timeout: 20_000 });
    deleted = true;
  });
} finally {
  await browser.close();
}

const summary = {
  origin,
  at: new Date().toISOString(),
  viewport: "390x844@2x",
  persona: "synthetic",
  guestDeleted: deleted,
  requiredFailed: steps.filter((s) => s.required && !s.ok).map((s) => s.id),
  consoleErrors: [...new Set(consoleErrors)].slice(0, 20),
  serverErrors: [...new Set(serverErrors)].slice(0, 20),
  steps,
};
writeFileSync(join(outDir, "journey.json"), `${JSON.stringify(summary, null, 2)}\n`);
console.log(`required failed: ${summary.requiredFailed.length}; guest deleted: ${deleted}`);
process.exit(summary.requiredFailed.length === 0 && deleted ? 0 : 1);
