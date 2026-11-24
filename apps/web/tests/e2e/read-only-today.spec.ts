import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

// #700: "Hôm nay chỉ muốn đọc" folds the small-action box on Home and the note page to one line.
// At 360 and 390px the button fits, is a 44px target, works from the keyboard, sends nothing and
// writes nothing to the device. The worst case for room is a "Đuối" day with a kept-able action:
// the lighter switch, the keep button and this button share the box. Synthetic data only.
const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/read-only-today");
mkdirSync(OUT_DIR, { recursive: true });

const NOTE_ID = "note-test";
const OWN = "Nhắn một người để hẹn lại lịch làm việc chung của tuần này.";
const LIGHT = "Rót một ly nước, ngồi xuống ghế gần nhất, uống chậm từng ngụm và nhìn ra cửa sổ cho tới khi thấy vai mình thả lỏng hơn.";
const HOOK = "Đừng biến mình thành deadline.";
const FOLD = "Hôm nay chỉ muốn đọc";
const OPEN = "Hiện lại việc nhỏ";
const cues = { observation: "Bạn thấy người dịu hơn chưa?", permission: "Không hợp thì bỏ qua." };

const active = { state: "active", onboarding_status: "completed", expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };
const dailyNote = {
  id: NOTE_ID, note_date: "2026-09-02", title: HOOK,
  body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.", full_body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
  context_label: "Bản cũ", content_version: "daily-note-v1", persona_mode: "aura", persona_label: "Mềm",
  persona_version: "persona-v1", source_level: "full_chart", astrology_source_version: "2.10.03",
  fallback_used: false, fallback_reason: null, awakening: null, sky_chapter: null,
  created_at: "2026-09-02T00:00:00Z",
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
    active: {
      revision_id: "00000000-0000-4000-8000-000000000010", source: "deterministic",
      mode: "full_synthesis", purpose: "daily_note", tradition: "western", precision: "exact",
      sections: {
        hook: HOOK, thesis: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
        manifestation: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
        transit: null, micro_action: OWN,
      },
      experiment: { action_key: "d".repeat(64), action: OWN, ...cues },
      lighter_action: { action: LIGHT, weight: "light", experiment: { action_key: "e".repeat(64), action: LIGHT, ...cues } },
      evidence: { title: "Căn cứ trong lá số", claims: ["Ngày sinh đã cung cấp"], framework_disclosure: "Chiêm tinh là một khung diễn giải." },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-02T00:00:00Z",
    },
  },
};

function answer(key: string): { status: number; json: unknown } | null {
  switch (key) {
    case "GET /v1/session":
    case "POST /v1/session/renew":
      return { status: 200, json: active };
    case "GET /v1/daily-note":
      return { status: 200, json: dailyNote };
    case `GET /v1/daily-note/${NOTE_ID}/mood`:
      return { status: 200, json: { id: "mood-test", daily_note_id: NOTE_ID, mood: "Đuối", checked_in_at: "2026-09-02T01:00:00Z" } };
    case "GET /v1/daily-note/resonance":
      return { status: 200, json: { consented: false, feedback_count: 0, last_choice: null } };
    case "GET /v1/daily-note/experiment":
      return { status: 200, json: null };
    case "GET /v1/saved-notes":
      return { status: 200, json: [] };
    case "GET /v1/birth-profile/supplement":
      return { status: 200, json: { profile_id: "profile-test", profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null } };
    default:
      return null;
  }
}

let unmocked: string[] = [];
let writes: string[] = [];
test.beforeEach(async ({ page }) => {
  unmocked = [];
  writes = [];
  await page.route("**/v1/**", async (route) => {
    const method = route.request().method();
    const key = `${method} ${new URL(route.request().url()).pathname}`;
    if (method !== "GET" && key !== "POST /v1/session/renew") writes.push(key);
    const reply = answer(key);
    if (!reply) {
      unmocked.push(key);
      await route.fulfill({ status: 503, json: { code: "E2E_UNMOCKED", path: key } });
      return;
    }
    await route.fulfill(reply);
  });
});
test.afterEach(() => {
  expect(unmocked, "API calls without a mock").toEqual([]);
  expect(writes, "the button never writes to the server").toEqual([]);
});

/** The button stays inside the viewport, unclipped, with a 44px target, and the page does not scroll sideways. */
async function expectFits(page: Page, width: number, label: string) {
  const button = page.getByRole("button", { name: label, exact: true });
  await expect(button).toBeVisible();
  const layout = await page.evaluate((name) => {
    const control = Array.from(document.querySelectorAll("button")).find((el) => el.textContent?.trim() === name)!;
    const r = control.getBoundingClientRect();
    return {
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      vw: window.innerWidth, left: r.left, right: r.right, height: r.height,
      clipped: control.scrollWidth > control.clientWidth || control.scrollHeight > control.clientHeight,
    };
  }, label);
  expect(layout.overflow, `no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);
  expect(layout.left, `${label} left edge at ${width}px`).toBeGreaterThanOrEqual(0);
  expect(layout.right, `${label} right edge at ${width}px`).toBeLessThanOrEqual(layout.vw);
  expect(layout.clipped, `${label} is not clipped at ${width}px`).toBe(false);
  expect(layout.height, `${label} is a 44px target at ${width}px`).toBeGreaterThanOrEqual(44);
}

const stored = (page: Page) => page.evaluate(() => JSON.stringify([Object.entries(localStorage).sort(), Object.entries(sessionStorage).sort()]));

for (const [name, path] of [["home", "/home"], ["note", "/note/today"]] as const) {
  test(`${name}: "Hôm nay chỉ muốn đọc" folds the action box at 360 and 390px, from the keyboard, with nothing sent or stored (#700)`, async ({ page }) => {
    for (const width of [360, 390]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(path);
      await expect(page.getByText(LIGHT, { exact: true })).toBeVisible();
      await expectFits(page, width, FOLD);
      await page.screenshot({ path: resolve(OUT_DIR, `${name}-${width}-open.png`), fullPage: true, animations: "disabled", scale: "css" });

      const url = page.url();
      const storedBefore = await stored(page);
      let requests = 0;
      const count = () => { requests += 1; };
      page.on("request", count);

      // Keyboard: Enter folds the box to one line and the focus stays on the button.
      await page.getByRole("button", { name: FOLD, exact: true }).focus();
      await page.keyboard.press("Enter");
      await expectFits(page, width, OPEN);
      await expect(page.getByRole("button", { name: OPEN, exact: true })).toBeFocused();
      await expect(page.getByText(LIGHT, { exact: true })).toHaveCount(0);
      await expect(page.getByText(OWN, { exact: true })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Giữ để thử hôm nay" })).toHaveCount(0);
      await expect(page.getByRole("heading", { name: HOOK })).toBeVisible();
      await page.screenshot({ path: resolve(OUT_DIR, `${name}-${width}-folded.png`), fullPage: true, animations: "disabled", scale: "css" });

      // Enter again opens it as it was.
      await page.keyboard.press("Enter");
      await expect(page.getByRole("button", { name: FOLD, exact: true })).toBeFocused();
      await expect(page.getByText(LIGHT, { exact: true })).toBeVisible();

      page.off("request", count);
      expect(requests, "no request while folding and opening").toBe(0);
      expect(page.url(), "stays on the same screen").toBe(url);
      expect(await stored(page), "nothing written to device storage").toBe(storedBefore);
    }
  });
}

test("the fold is shared by Home and the note page while the app stays open, and a reload opens the box again (#700)", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/home");
  await page.getByRole("button", { name: FOLD, exact: true }).click();
  await expect(page.getByRole("button", { name: OPEN, exact: true })).toBeVisible();

  // In-app navigation keeps the page's memory.
  await page.getByRole("link", { name: /Đọc đầy đủ/ }).click();
  await expect(page).toHaveURL(/\/note\/today/);
  await expect(page.getByRole("button", { name: OPEN, exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Thử một việc nhỏ" })).toHaveCount(0);

  // Memory only: a reload starts open.
  await page.reload();
  await expect(page.getByRole("button", { name: FOLD, exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Thử một việc nhỏ" })).toBeVisible();
});
