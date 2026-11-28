import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test } from "@playwright/test";

// Fix-forward #898 (item 2) and #909: the Lá pixel trial on /companion-lab had unit tests only.
// Here a real browser picks every move, sees it play once and come back to rest, checks the page
// does not scroll sideways at 360 and 390px, and checks "Xem tĩnh" keeps Lá still. The lab page
// calls no API and stores nothing, so any /v1 call fails the test.
const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/companion-lab");
mkdirSync(OUT_DIR, { recursive: true });

// Order of PIXEL_MOVES (src/shared/ui/companion/pixel/moves/index.ts).
const MOVE_IDS = ["chao", "ngoi-cung", "kinh-roi", "uong-tra"] as const;
// The move budget is 5 seconds; a little room for a slow CI runner.
const PLAY_TIMEOUT_MS = 8000;

let apiCalls: string[] = [];
test.beforeEach(async ({ page }) => {
  apiCalls = [];
  await page.route("**/v1/**", async (route) => {
    apiCalls.push(`${route.request().method()} ${new URL(route.request().url()).pathname}`);
    await route.fulfill({ status: 503, json: { code: "E2E_UNMOCKED" } });
  });
});
test.afterEach(() => {
  expect(apiCalls, "the lab page calls no API").toEqual([]);
});

for (const width of [360, 390]) {
  test(`companion lab: every Lá pixel move plays once and the page fits at ${width}px (#898, #909)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/companion-lab");

    const section = page.getByRole("region", { name: "Lá pixel, bản thử" });
    const la = section.locator("button.pixel-la");
    const moves = section.getByRole("group", { name: "Động tác" }).getByRole("button");
    await expect(moves).toHaveCount(MOVE_IDS.length);
    await expect(la).toHaveAttribute("data-motion", "ready");
    await expect(la).toHaveAttribute("data-frame", "rest");

    for (let index = 0; index < MOVE_IDS.length; index += 1) {
      const id = MOVE_IDS[index];
      const button = moves.nth(index);
      const name = (await button.textContent())?.trim() ?? "";
      expect(name, `move ${id} has a name`).not.toBe("");
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
      await expect(section.getByRole("group", { name: "Động tác" }).locator('button[aria-pressed="true"]')).toHaveCount(1);
      await expect(la).toHaveAttribute("data-move", id);
      await expect(la).toHaveAttribute("aria-label", `Lá pixel, bấm để chạy động tác ${name}`);
      await expect(la, `${id} starts playing`).toHaveAttribute("data-motion", "playing");
      await expect(la, `${id} ends by itself`).toHaveAttribute("data-motion", "ready", { timeout: PLAY_TIMEOUT_MS });
      await expect(la).toHaveAttribute("data-frame", "rest");
    }

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);
    const box = await la.boundingBox();
    expect(box, "Lá is on the page").not.toBeNull();
    expect(box!.x, `Lá left edge at ${width}px`).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width, `Lá right edge at ${width}px`).toBeLessThanOrEqual(width);

    await section.scrollIntoViewIfNeeded();
    await page.screenshot({ path: resolve(OUT_DIR, `pixel-${width}.png`), fullPage: true, animations: "disabled", scale: "css" });
  });
}

test("companion lab: with 'Xem tĩnh' on, pressing Lá or a move changes nothing on screen (#898)", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/companion-lab");

  const section = page.getByRole("region", { name: "Lá pixel, bản thử" });
  const la = section.locator("button.pixel-la");
  const moves = section.getByRole("group", { name: "Động tác" }).getByRole("button");

  await page.getByRole("checkbox", { name: "Xem tĩnh (giảm chuyển động)" }).check();
  await expect(la).toHaveAttribute("data-motion", "still");

  await moves.nth(2).click();
  await expect(la).toHaveAttribute("data-move", MOVE_IDS[2]);
  await expect(la).toHaveAttribute("data-motion", "still");
  await expect(la).toHaveAttribute("data-frame", "rest");

  // Keyboard: Lá itself is a button; Enter must not start the move either.
  await la.focus();
  await page.keyboard.press("Enter");
  await expect(la).toHaveAttribute("data-motion", "still");
  await expect(la).toHaveAttribute("data-frame", "rest");
  await page.screenshot({ path: resolve(OUT_DIR, "pixel-390-still.png"), fullPage: true, animations: "disabled", scale: "css" });
});
