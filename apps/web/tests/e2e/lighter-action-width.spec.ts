import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

// #627 PR B, G2 evidence: on a "Đuối" day Home and the note page show the lighter action with a
// switch back to the card's own action. Both controls must fit at 360 and 390px, be at least 44px
// tall, and work from the keyboard. Synthetic data only.
const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/lighter-action");
mkdirSync(OUT_DIR, { recursive: true });

const NOTE_ID = "note-test";
const OWN = "Nhắn một người để hẹn lại lịch làm việc chung của tuần này.";
// The longest sentence the contract allows (120 characters) must still wrap inside the card.
const LIGHT = "Rót một ly nước, ngồi xuống ghế gần nhất, uống chậm từng ngụm và nhìn ra cửa sổ cho tới khi thấy vai mình thả lỏng hơn.";
const cues = { observation: "Bạn thấy người dịu hơn chưa?", permission: "Không hợp thì bỏ qua." };

const active = { state: "active", onboarding_status: "completed", expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };
const dailyNote = {
  id: NOTE_ID, note_date: "2026-09-02", title: "Đừng biến mình thành deadline.",
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
        hook: "Đừng biến mình thành deadline.", thesis: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
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
    case "GET /v1/month/status":
      return { status: 200, json: { available: false, month: "2026-09", presets: [] } };
    case "GET /v1/birth-profile/supplement":
      return { status: 200, json: { profile_id: "profile-test", profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null } };
    default:
      return null;
  }
}

let unmocked: string[] = [];
test.beforeEach(async ({ page }) => {
  unmocked = [];
  await page.route("**/v1/**", async (route) => {
    const key = `${route.request().method()} ${new URL(route.request().url()).pathname}`;
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
});

/** The switch and the action text stay inside the viewport, unclipped, with a 44px target. */
async function expectFits(page: Page, width: number, label: string, text: string) {
  const button = page.getByRole("button", { name: label });
  await expect(button).toBeVisible();
  await expect(page.getByText(text, { exact: true })).toBeVisible();
  const layout = await page.evaluate(({ label: name, text: sentence }) => {
    const control = Array.from(document.querySelectorAll("button")).find((el) => el.textContent?.trim() === name)!;
    const line = Array.from(document.querySelectorAll("p")).find((el) => el.textContent === sentence)!;
    const box = (el: Element) => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, height: r.height }; };
    return {
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      vw: window.innerWidth,
      button: { ...box(control), clipped: control.scrollWidth > control.clientWidth || control.scrollHeight > control.clientHeight },
      text: { ...box(line), clipped: line.scrollWidth > line.clientWidth || line.scrollHeight > line.clientHeight },
    };
  }, { label, text });
  expect(layout.overflow, `no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);
  for (const [name, item] of [["switch", layout.button], ["action", layout.text]] as const) {
    expect(item.left, `${name} left edge at ${width}px`).toBeGreaterThanOrEqual(0);
    expect(item.right, `${name} right edge at ${width}px`).toBeLessThanOrEqual(layout.vw);
    expect(item.clipped, `${name} is not clipped at ${width}px`).toBe(false);
  }
  expect(layout.button.height, `switch is a 44px target at ${width}px`).toBeGreaterThanOrEqual(44);
}

for (const [name, path] of [["home", "/home"], ["note", "/note/today"]] as const) {
  test(`${name}: the lighter action and its switch fit at 360 and 390px and work from the keyboard (#627)`, async ({ page }) => {
    for (const width of [360, 390]) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(path);
      await expectFits(page, width, "Xem việc ban đầu", LIGHT);
      await page.screenshot({ path: resolve(OUT_DIR, `${name}-${width}-lighter.png`), fullPage: true, animations: "disabled", scale: "css" });

      // Keyboard: focus the switch, Enter shows the card's own action, Enter again the lighter one.
      await page.getByRole("button", { name: "Xem việc ban đầu" }).focus();
      await page.keyboard.press("Enter");
      await expectFits(page, width, "Xem việc nhẹ hơn", OWN);
      await expect(page.getByRole("button", { name: "Xem việc nhẹ hơn" })).toBeFocused();
      await expect(page.getByText(LIGHT, { exact: true })).toHaveCount(0);
      await page.screenshot({ path: resolve(OUT_DIR, `${name}-${width}-original.png`), fullPage: true, animations: "disabled", scale: "css" });
      await page.keyboard.press("Enter");
      await expect(page.getByText(LIGHT, { exact: true })).toBeVisible();
    }
  });
}
