import { mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Locator, type Page, type Route } from "@playwright/test";


// G2 width checks for the consent screens (fix-forward #681 from #652). Level M asks for results at
// 360 and 390 px. /consent is the welcome screen with the "Đồng ý & bắt đầu" button; /privacy is the
// detail page that carries the owner-approved mood sentence. Each route at each width must:
// - have no horizontal page overflow;
// - keep the key text and actions inside the viewport, with a target of at least 24 px (WCAG 2.2
//   2.5.8);
// - show the mood sentence on /privacy, word for word.
// Vite preview with every /v1 call answered by fake data; no real data. Screenshots go next to the
// key screens, so ui-screens.yml uploads them for review.

const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/ui-screens");
mkdirSync(OUT_DIR, { recursive: true });

const WIDTHS = [360, 390] as const;

// The approved sentence, read from the app's own constant (this test project cannot import src).
const noteSource = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "../../src/shared/config/moodLighterTaskNote.ts"), "utf8");
const MOOD_LIGHTER_TASK_NOTE = /export const MOOD_LIGHTER_TASK_NOTE = "([^"]+)";/.exec(noteSource)?.[1] ?? "";
if (!MOOD_LIGHTER_TASK_NOTE) throw new Error("MOOD_LIGHTER_TASK_NOTE not found in moodLighterTaskNote.ts");

async function guestApi(page: Page) {
  const unmocked: string[] = [];
  await page.route("**/v1/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === "GET" && (path === "/v1/session" || path === "/v1/session/onboarding-status")) {
      await route.fulfill({ status: 401, json: { code: "GUEST_SESSION_MISSING" } });
      return;
    }
    unmocked.push(`${request.method()} ${path}`);
    await route.fulfill({ status: 503, json: { code: "SCREENS_UNMOCKED", path } });
  });
  return unmocked;
}

// Elements whose box leaves the viewport sideways. Decorative layers (aria-hidden) are skipped: they
// are clipped by design and carry no text a person needs.
async function sidewaysOverflow(page: Page) {
  return page.evaluate(() => {
    const width = window.innerWidth;
    const out: string[] = [];
    for (const el of Array.from(document.querySelectorAll("main *"))) {
      if (el.closest("[aria-hidden='true']")) continue;
      const box = el.getBoundingClientRect();
      if (box.width === 0 || box.height === 0) continue;
      if (box.left < -0.5 || box.right > width + 0.5) out.push(`${el.tagName.toLowerCase()}.${(el.getAttribute("class") ?? "").split(" ")[0]} [${Math.round(box.left)}, ${Math.round(box.right)}]`);
    }
    return { scrollWidth: document.documentElement.scrollWidth, innerWidth: width, out };
  });
}

async function inside(page: Page, target: Locator, what: string) {
  await target.scrollIntoViewIfNeeded();
  await expect(target, what).toBeVisible();
  const box = await target.boundingBox();
  const width = page.viewportSize()?.width ?? 0;
  expect(box, what).not.toBeNull();
  expect(box!.x, `${what}: left edge`).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width, `${what}: right edge`).toBeLessThanOrEqual(width + 0.5);
  return box!;
}

const routes = [
  {
    route: "/consent",
    ready: (page: Page) => page.getByRole("button", { name: "Đồng ý & bắt đầu" }),
    targets: (page: Page) => [
      { what: "nút Đồng ý & bắt đầu", locator: page.getByRole("button", { name: "Đồng ý & bắt đầu" }), action: true },
      { what: "link Xem chi tiết", locator: page.getByRole("link", { name: "Xem chi tiết" }), action: true },
    ],
  },
  {
    route: "/privacy",
    ready: (page: Page) => page.getByRole("heading", { name: "Lá Lành dùng dữ liệu thế nào?" }),
    targets: (page: Page) => [
      { what: "câu mood đã duyệt", locator: page.getByText(MOOD_LIGHTER_TASK_NOTE, { exact: true }), action: false },
      { what: "nút Mình hiểu rồi", locator: page.getByRole("button", { name: "Mình hiểu rồi" }), action: true },
    ],
  },
];

for (const { route, ready, targets } of routes) {
  for (const width of WIDTHS) {
    test(`G2 ${route} at ${width}px: no sideways overflow, key text and actions fit`, async ({ page }) => {
      await page.setViewportSize({ width, height: 800 });
      const unmocked = await guestApi(page);
      await page.goto(route);
      await expect(ready(page)).toBeVisible();
      await page.evaluate(() => document.fonts.ready);

      const overflow = await sidewaysOverflow(page);
      expect(overflow.scrollWidth, `${route} @ ${width}: page wider than the screen`).toBeLessThanOrEqual(overflow.innerWidth);
      expect(overflow.out, `${route} @ ${width}: elements outside the screen`).toEqual([]);

      const receipt: Record<string, unknown> = { route, width, scrollWidth: overflow.scrollWidth };
      for (const { what, locator, action } of targets(page)) {
        const box = await inside(page, locator, `${route} @ ${width}: ${what}`);
        if (action) expect(box.height, `${route} @ ${width}: ${what} target height`).toBeGreaterThanOrEqual(24);
        receipt[what] = { x: Math.round(box.x), right: Math.round(box.x + box.width), h: Math.round(box.height) };
      }
      if (route === "/privacy") {
        const sentence = page.getByText(MOOD_LIGHTER_TASK_NOTE, { exact: true });
        const style = await sentence.evaluate((el) => {
          const s = getComputedStyle(el);
          return { fontSize: parseFloat(s.fontSize), lineHeight: s.lineHeight, lines: Math.round(el.getBoundingClientRect().height / (parseFloat(s.lineHeight) || parseFloat(s.fontSize) * 1.4)) };
        });
        expect(style.fontSize, `${route} @ ${width}: mood sentence font size`).toBeGreaterThanOrEqual(12);
        receipt.moodSentence = style;
      }
      console.log(`G2 ${JSON.stringify(receipt)}`);
      await page.screenshot({ path: resolve(OUT_DIR, `g2-${route.slice(1)}-${width}.png`), fullPage: true, animations: "disabled" });
      if (unmocked.length) test.info().annotations.push({ type: "unmocked", description: Array.from(new Set(unmocked)).join(", ") });
    });
  }
}
