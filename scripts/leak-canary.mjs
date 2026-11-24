#!/usr/bin/env node
// Leak canary (#690): runs the built web app against the real API (local, throwaway SQLite) with a
// synthetic profile whose values are easy to find, then searches the places that must never carry
// them: server log, request URLs, Referer headers, requests leaving the app, error reports, API
// error answers, browser history, the current URL and web storage. #691: it also downloads and
// shares the note card and the birth card and downloads the data file, then searches the file
// names, the SVG each picture is drawn from and the metadata inside each PNG.
//
// Usage:  node scripts/leak-canary.mjs [--plant <surface>]
//   --plant <surface>  put a mark into that surface on purpose; the run must then end red (exit 1).
// Needs the web build (pnpm qa:build). Exit code: 0 clean, 1 a mark was found or the journey did not
// send every mark, 2 the run itself broke.
// How to read the result: docs/operations/leak-canary-runbook.md
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  CANARY, SAFETY_TEXT, SURFACES, TAROT_QUESTION,
  buildMarks, canaryServerEnv, dumpWebStorage, isLocalUrl, missingFiles, missingSends, pngMetadata, reportLines,
  scanSurfaces, sendsIn, svgTextOf,
} from "./leak-canary-lib.mjs";
import { drainOnStop } from "./qa-server.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const requireFromWeb = createRequire(resolve(root, "apps/web/package.json"));
const { chromium } = requireFromWeb("@playwright/test");

const plantAt = process.argv.indexOf("--plant");
const planted = plantAt === -1 ? null : process.argv[plantAt + 1];
if (planted !== null && !SURFACES.includes(planted)) {
  console.error(`--plant cần một trong: ${SURFACES.join(", ")}`);
  process.exit(2);
}

const scratch = await mkdtemp(join(tmpdir(), "la-lanh-leak-canary-"));
const apiPort = 18_900 + Math.floor(Math.random() * 400);
const webPort = apiPort + 500;
const origin = `http://127.0.0.1:${webPort}`;

const surfaces = Object.fromEntries(SURFACES.map((name) => [name, []]));
const sent = new Set();
const collected = new Set();
const secrets = new Set();
let placeId = null;
let serverLog = "";

const server = spawn(process.execPath, ["scripts/qa-server.mjs"], {
  cwd: root,
  env: canaryServerEnv({ base: process.env, databaseFile: join(scratch, "qa.db"), apiPort, webPort }),
  stdio: ["ignore", "pipe", "pipe"],
});
const stopServer = drainOnStop(server);
server.stdout.on("data", (chunk) => { serverLog += chunk; });
server.stderr.on("data", (chunk) => { serverLog += chunk; });

async function waitReady() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline && server.exitCode === null) {
    try {
      const response = await fetch(`${origin}/__qa/ready`, { signal: AbortSignal.timeout(1_000) });
      if (response.ok) return;
    } catch {
      // The API creates its schema and loads the ephemeris first.
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
  }
  throw new Error("máy chủ QA không sẵn sàng sau 60 giây (đã chạy `pnpm qa:build` chưa?)");
}

function watch(context) {
  context.on("request", (request) => {
    const url = request.url();
    if (!isLocalUrl(url, origin)) {
      surfaces["external-request"].push(url);
      return;
    }
    surfaces["request-url"].push(url);
    const path = new URL(url).pathname;
    for (const kind of sendsIn(request.method(), path, request.postData() ?? "")) sent.add(kind);
    if (path.endsWith("/birth-profile/supplement") && request.method() === "POST") {
      try {
        placeId = JSON.parse(request.postData() ?? "{}").place_id ?? placeId;
      } catch {
        // Not JSON: nothing to learn from this body.
      }
    }
    void request.allHeaders().then((headers) => {
      if (headers.referer) surfaces["request-referer"].push(headers.referer);
      if (headers["x-csrf-token"]) secrets.add(headers["x-csrf-token"]);
    }).catch(() => {});
  });
  context.on("response", (response) => {
    // The file name a server answer proposes for a download.
    const disposition = response.headers()["content-disposition"];
    if (disposition) surfaces["file-name"].push(disposition);
    if (response.status() < 400 || !isLocalUrl(response.url(), origin)) return;
    void response.text().then((text) => surfaces["error-response"].push(text)).catch(() => {});
  });
}

function watchPage(page) {
  page.on("console", (message) => surfaces["error-report"].push(message.text()));
  page.on("pageerror", (error) => surfaces["error-report"].push(`${error?.message ?? error}\n${error?.stack ?? ""}`));
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) surfaces["browser-history"].push(frame.url());
  });
}

async function readStorage(page) {
  surfaces["web-storage"].push(...await page.evaluate(dumpWebStorage));
}

// --plant for a surface the run collects itself: the mark goes into the real place, so the run is
// red only if the collector reads it. Web storage: the body of an answer kept in Cache Storage.
async function plantInPage(page) {
  if (planted !== "web-storage") return;
  await page.evaluate(async (text) => {
    const cache = await caches.open("leak-canary-plant");
    await cache.put("/__leak-canary-plant", new Response(text, { headers: { "content-type": "text/plain" } }));
  }, `planted ${CANARY.tarotMark}`);
  await readStorage(page);
}

const button = (page, name) => page.getByRole("button", { name }).first();

// One share card (#691): the SVG the picture is drawn from, the downloaded PNG (name and metadata)
// and what the app hands to the share sheet. The browser here has no share sheet, so a stand-in
// records the call; without it the app falls back to a download and the share path is not run.
async function collectCard(page, { kind, downloadName, shareName }) {
  const image = page.locator("img.share-art__image.is-loaded");
  await image.waitFor({ timeout: 30_000 });
  const svg = svgTextOf(await image.getAttribute("src"));
  if (!/<svg[\s>]/.test(svg) || !/<text[\s>]/.test(svg)) throw new Error("ảnh xem trước không phải bản SVG có chữ");
  surfaces["share-image"].push(
    svg,
    `alt ${await image.getAttribute("alt")}`,
    `heading ${await page.locator(".share-art h1").first().textContent().catch(() => "")}`,
  );

  const downloading = page.waitForEvent("download", { timeout: 20_000 });
  await page.getByRole("button", { name: downloadName, exact: true }).click();
  const file = await downloading;
  surfaces["file-name"].push(file.suggestedFilename());
  const { chunks, texts } = pngMetadata(await readFile(await file.path()));
  surfaces["image-metadata"].push(`chunks ${chunks.join(" ")}`, ...texts);
  collected.add(`${kind}-png`);

  await page.evaluate(() => {
    const calls = [];
    Object.defineProperty(window, "__leakCanaryShared", { value: calls, configurable: true });
    Object.defineProperty(navigator, "canShare", { value: () => true, configurable: true });
    Object.defineProperty(navigator, "share", {
      configurable: true,
      value: async (data) => {
        calls.push({ title: data?.title ?? "", text: data?.text ?? "", url: data?.url ?? "", files: [...(data?.files ?? [])].map((entry) => entry.name) });
      },
    });
  });
  await page.getByRole("button", { name: shareName, exact: true }).click();
  await page.waitForFunction(() => window.__leakCanaryShared.length > 0, null, { timeout: 20_000 });
  for (const call of await page.evaluate(() => window.__leakCanaryShared)) {
    if (call.files.length === 0) throw new Error("bảng chia sẻ không nhận file nào");
    surfaces["file-name"].push(...call.files);
    surfaces["share-image"].push(`share title ${call.title}\ntext ${call.text}\nurl ${call.url}`);
  }
  collected.add(`${kind}-share`);
}

async function journey(page) {
  const go = (path) => page.goto(`${origin}${path}`, { waitUntil: "domcontentloaded" });
  const mark = async (name, action) => {
    await action();
    await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
    surfaces["current-url"].push(page.url());
    await readStorage(page);
    console.log(`bước xong: ${name}`);
  };

  await mark("mở app, đồng ý", async () => {
    await go("/");
    await button(page, "Đồng ý & bắt đầu").click();
    await page.getByPlaceholder("DD").waitFor();
  });
  await mark("ngày sinh, giờ sinh, nơi sinh", async () => {
    await page.getByPlaceholder("DD").fill(CANARY.day);
    await page.getByPlaceholder("MM").fill(CANARY.month);
    await page.getByPlaceholder("YYYY").fill(CANARY.year);
    await button(page, /Thêm giờ & nơi sinh/).click();
    await button(page, "Biết giờ").click();
    const selects = page.locator("select");
    await selects.nth(0).selectOption(CANARY.hour);
    await selects.nth(1).selectOption(CANARY.minute);
    await page.getByPlaceholder("Tìm thành phố / tỉnh").fill(CANARY.place);
    await button(page, new RegExp(`^${CANARY.place}`)).click();
    await page.locator("input[type=checkbox]").first().check();
    await page.getByRole("button", { name: /Khớp tín hiệu|Tiếp tục|Xem/ }).last().click();
    await page.waitForURL((url) => !url.pathname.startsWith("/birth"), { timeout: 30_000 });
  });
  await mark("Home, chọn mood", async () => {
    await go("/home");
    await page.locator(".mood-quick-trigger").first().click();
    const saved = page.waitForResponse((response) => /\/mood$/.test(new URL(response.url()).pathname) && response.request().method() === "PUT", { timeout: 20_000 });
    await page.locator(".mood-sheet__options button", { hasText: CANARY.mood }).click();
    await saved;
  });
  await mark("note hôm nay", () => go("/note/today"));
  await mark("chữ gõ vào lớp an toàn", async () => {
    await go("/tarot");
    await page.locator("textarea").fill(SAFETY_TEXT);
    await button(page, /^1 lá/).click();
    const answered = page.waitForResponse((response) => new URL(response.url()).pathname === "/v1/tarot/sessions" && response.request().method() === "POST", { timeout: 20_000 });
    await button(page, /^Xòe 1 lá/).click();
    const response = await answered;
    if (response.status() !== 422) throw new Error(`lớp an toàn trả ${response.status()}, chờ 422`);
  });
  await mark("câu hỏi Tarot", async () => {
    await go("/tarot");
    await page.locator("textarea").fill(TAROT_QUESTION);
    await button(page, /^1 lá/).click();
    await button(page, /^Xòe 1 lá/).click();
    await page.locator("[data-fan-index]").first().waitFor({ timeout: 20_000 });
    const card = page.locator("[data-fan-index]").nth(7);
    await card.scrollIntoViewIfNeeded();
    await card.evaluate((element) => element.click());
    await page.getByText("Chưa chọn").waitFor({ state: "detached", timeout: 20_000 });
    await page.waitForTimeout(3_000);
  });
  await mark("các màn đọc lại hồ sơ", async () => {
    for (const path of ["/insights", "/insights/current-sky", "/saved", "/profile"]) {
      await go(path);
      await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
      surfaces["current-url"].push(page.url());
    }
  });
  await mark("ảnh note: tải và chia sẻ", async () => {
    await go("/card");
    await collectCard(page, { kind: "note-card", downloadName: "Tải ảnh PNG", shareName: "Chia sẻ thẻ" });
  });
  await mark("Lá Khai Sinh: tải và chia sẻ", async () => {
    await go("/birth-card");
    await collectCard(page, { kind: "birth-card", downloadName: "Tải PNG", shareName: "Chia sẻ" });
  });
  await mark("tải dữ liệu của tôi", async () => {
    await go("/profile");
    await page.locator("details.profile-more > summary").click();
    await button(page, /Tải dữ liệu của tôi/).click();
    const downloading = page.waitForEvent("download", { timeout: 20_000 });
    await page.getByRole("button", { name: "Tải về", exact: true }).click();
    // Only the name is searched: the file itself holds the owner's data on purpose.
    surfaces["file-name"].push((await downloading).suggestedFilename());
    collected.add("data-export-file");
  });
}

let exitCode = 2;
let browser = null;
try {
  await waitReady();
  browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    locale: "vi-VN",
    timezoneId: "Asia/Ho_Chi_Minh",
    serviceWorkers: "block",
  });
  watch(context);
  const page = await context.newPage();
  watchPage(page);
  await journey(page);
  await plantInPage(page);
  for (const cookie of await context.cookies()) secrets.add(cookie.value);
  await browser.close();
  browser = null;

  // Stop the server and wait until its output is closed before reading the log: the API writes
  // its shutdown lines after the launcher has been told to stop.
  await stopServer();
  surfaces["server-log"] = serverLog.split("\n").filter((line) => line.trim() !== "");

  if (planted && planted !== "web-storage") surfaces[planted].push(`planted ${CANARY.tarotMark}`);
  const marks = buildMarks({ placeId, secrets: [...secrets] });
  const findings = scanSurfaces(surfaces, marks);
  const missing = missingSends(sent);
  const noFiles = missingFiles(collected);
  for (const line of reportLines({ surfaces, findings, missing, missingFiles: noFiles, planted })) console.log(line);
  exitCode = findings.length > 0 || missing.length > 0 || noFiles.length > 0 ? 1 : 0;
} catch (error) {
  // Only the first line, without values: an error text can quote the page.
  console.error(`Lượt chạy hỏng: ${String(error?.message ?? error).split("\n")[0].slice(0, 200)}`);
  exitCode = 2;
} finally {
  if (browser) await browser.close().catch(() => {});
  // After a broken run the server may still be up; a server that will not stop keeps the run broken.
  await stopServer().catch(() => { exitCode = 2; });
  await rm(scratch, { recursive: true, force: true });
}
process.exit(exitCode);
