import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

// #688 (7-week plan, week 1): keeping the day's small action works on a phone for the three kinds
// of profile (date only, approximate time, exact time) at 360 and 390px: keep, stop keeping,
// replace, record an outcome, reload, and lose the network in between. The API is a stateful fake
// that answers the way the server does once every kind of profile is offered the action (#716).
// Synthetic data only.
const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/keep-action");
mkdirSync(OUT_DIR, { recursive: true });

const NOTE_ID = "00000000-0000-4000-8000-000000000001";
const REVISION_ID = "00000000-0000-4000-8000-000000000010";
const OWN = "Nhắn một người để hẹn lại lịch làm việc chung của tuần này.";
const LIGHT = "Rót một ly nước, ngồi xuống ghế gần nhất và uống chậm từng ngụm.";
const cues = { observation: "Bạn thấy người dịu hơn chưa?", permission: "Không hợp thì bỏ qua." };
const OWN_KEY = "d".repeat(64);
const LIGHT_KEY = "e".repeat(64);

const KEEP = "Giữ để thử hôm nay";
const STOP = "Bỏ giữ việc này";
const REPLACE = "Thay việc đang giữ";
const CONFIRM_REPLACE = "Xác nhận thay việc đang giữ";
const OPEN_REFLECTION = "Mở phần nhìn lại";
const SHOW_ORIGINAL = "Xem việc ban đầu";

type Profile = {
  kind: string;
  mode: "vibe_fallback" | "full_synthesis";
  precision: "unknown" | "approximate" | "exact";
  sourceLevel: "date_only_sun" | "natal_chart";
  personaMode: "vibe" | "aura";
  supplement: { profile_level: number; birth_time_mode: string; time_precision: string; approx_window: string | null };
};

const PROFILES: Profile[] = [
  {
    kind: "date-only", mode: "vibe_fallback", precision: "unknown", sourceLevel: "date_only_sun", personaMode: "vibe",
    supplement: { profile_level: 1, birth_time_mode: "unknown", time_precision: "unknown", approx_window: null },
  },
  {
    kind: "approximate-time", mode: "full_synthesis", precision: "approximate", sourceLevel: "natal_chart", personaMode: "aura",
    supplement: { profile_level: 2, birth_time_mode: "approx_window", time_precision: "approximate", approx_window: "morning" },
  },
  {
    kind: "exact-time", mode: "full_synthesis", precision: "exact", sourceLevel: "natal_chart", personaMode: "aura",
    supplement: { profile_level: 3, birth_time_mode: "exact", time_precision: "exact", approx_window: null },
  },
];

const active = { state: "active", onboarding_status: "completed", expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };

function dailyNote(profile: Profile) {
  return {
    id: NOTE_ID, note_date: "2026-09-02", title: "Đừng biến mình thành deadline.",
    body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.", full_body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
    context_label: "Bản cũ", content_version: "daily-note-v1", persona_mode: profile.personaMode, persona_label: "Mềm",
    persona_version: "persona-v1", source_level: profile.sourceLevel, astrology_source_version: "2.10.03",
    fallback_used: false, fallback_reason: null, awakening: null, sky_chapter: null,
    created_at: "2026-09-02T00:00:00Z",
    reading_projection: {
      scope_key: "a".repeat(64), available_update: null,
      aura_transition: profile.personaMode === "aura"
        ? { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] }
        : null,
      active: {
        revision_id: REVISION_ID, source: "deterministic",
        mode: profile.mode, purpose: "daily_note", tradition: "western", precision: profile.precision,
        sections: {
          hook: "Đừng biến mình thành deadline.", thesis: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
          manifestation: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
          transit: null, micro_action: OWN,
        },
        experiment: { action_key: OWN_KEY, action: OWN, ...cues },
        lighter_action: { action: LIGHT, weight: "light", experiment: { action_key: LIGHT_KEY, action: LIGHT, ...cues } },
        evidence: { title: "Căn cứ trong lá số", claims: ["Ngày sinh đã cung cấp"], framework_disclosure: "Chiêm tinh là một khung diễn giải." },
        disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-02T00:00:00Z",
      },
    },
  };
}

type Kept = {
  id: string; daily_note_id: string; revision_id: string; background_lens: string; action_key: string;
  action: string; observation: string; permission: string; state: "chosen" | "reflected";
  outcome: string | null; version: number; created_at: string; updated_at: string; expires_at: string;
  reflected_at: string | null;
};

/** One kept action per person, replaced or changed only with the id and version the client saw. */
class FakeServer {
  kept: Kept | null = null;
  down = false;
  writes: string[] = [];
  unmocked: string[] = [];
  /** Requests the fake is answering right now. */
  answering = 0;
  private nextId = 1;

  constructor(private readonly profile: Profile) {}

  answer(method: string, path: string, body: Record<string, unknown> | null): { status: number; json?: unknown } | null {
    const key = `${method} ${path}`;
    const conflict = { status: 409, json: { code: "EXPERIMENT_CONFLICT", message: "stale" } };
    switch (key) {
      case "GET /v1/session":
      case "POST /v1/session/renew":
        return { status: 200, json: active };
      case "GET /v1/daily-note":
        return { status: 200, json: dailyNote(this.profile) };
      case `GET /v1/daily-note/${NOTE_ID}/mood`:
        return { status: 200, json: { id: "mood-test", daily_note_id: NOTE_ID, mood: "Đuối", checked_in_at: "2026-09-02T01:00:00Z" } };
      case "GET /v1/daily-note/resonance":
        return { status: 200, json: { consented: false, feedback_count: 0, last_choice: null } };
      case "GET /v1/saved-notes":
        return { status: 200, json: [] };
      case "GET /v1/birth-profile/supplement":
        return { status: 200, json: { profile_id: "profile-test", place_display_name: null, timezone_id: null, ...this.profile.supplement } };
      case "GET /v1/daily-note/experiment":
        return { status: 200, json: this.kept };
      case `PUT /v1/daily-note/${NOTE_ID}/experiment`: {
        this.writes.push(key);
        const actionKey = String(body?.action_key);
        const action = actionKey === OWN_KEY ? OWN : actionKey === LIGHT_KEY ? LIGHT : null;
        if (!action || body?.revision_id !== REVISION_ID || body?.consent_version !== "action-experiment-v1") {
          return { status: 404, json: { code: "EXPERIMENT_TARGET_NOT_FOUND", message: "unknown" } };
        }
        const expectedId = body?.expected_experiment_id ?? null;
        const expectedVersion = body?.expected_version ?? null;
        if (this.kept && this.kept.action_key !== actionKey && (expectedId !== this.kept.id || expectedVersion !== this.kept.version)) return conflict;
        if (!this.kept && expectedId !== null) return conflict;
        if (!this.kept || this.kept.action_key !== actionKey) {
          const now = "2026-09-02T02:00:00Z";
          this.kept = {
            id: `00000000-0000-4000-8000-0000000001${String(this.nextId++).padStart(2, "0")}`,
            daily_note_id: NOTE_ID, revision_id: REVISION_ID, background_lens: typeof body?.background_lens === "string" ? body.background_lens : "auto",
            action_key: actionKey, action, ...cues, state: "chosen", outcome: null, version: 1,
            created_at: now, updated_at: now, expires_at: "2026-09-09T02:00:00Z", reflected_at: null,
          };
        }
        return { status: 200, json: this.kept };
      }
      case "DELETE /v1/daily-note/experiment":
        this.writes.push(key);
        if (!this.kept || body?.experiment_id !== this.kept.id || body?.expected_version !== this.kept.version) return conflict;
        this.kept = null;
        return { status: 204 };
      case "POST /v1/daily-note/experiment/outcome":
        this.writes.push(key);
        if (!this.kept || body?.experiment_id !== this.kept.id || body?.expected_version !== this.kept.version) return conflict;
        this.kept = { ...this.kept, state: "reflected", outcome: String(body?.outcome), version: this.kept.version + 1, reflected_at: "2026-09-02T03:00:00Z", updated_at: "2026-09-02T03:00:00Z" };
        return { status: 200, json: this.kept };
      default:
        return null;
    }
  }

  async attach(page: Page) {
    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      if (this.down) {
        await route.abort("internetdisconnected");
        return;
      }
      this.answering += 1;
      try {
        const reply = this.answer(request.method(), path, request.postDataJSON() as Record<string, unknown> | null);
        if (!reply) {
          this.unmocked.push(`${request.method()} ${path}`);
          await route.fulfill({ status: 503, json: { code: "E2E_UNMOCKED", path } });
          return;
        }
        if (reply.json === undefined) await route.fulfill({ status: reply.status });
        else await route.fulfill({ status: reply.status, json: reply.json });
      } finally {
        this.answering -= 1;
      }
    });
  }
}

/**
 * The control has a screen-reader name, is a 44px target, sits inside the viewport without
 * clipping, and nothing lies on top of it (the "Lưu note" bar, the top bar, a notice) both when
 * it is scrolled to the middle of the screen and when the page is scrolled to its end.
 */
async function expectTappable(page: Page, name: string, width: number) {
  const button = page.getByRole("button", { name, exact: true });
  await expect(button, `"${name}" at ${width}px`).toBeVisible();
  await expect(button).toBeEnabled();
  for (const position of ["middle", "page end"] as const) {
    const layout = await button.evaluate((el, where) => {
      if (where === "middle") el.scrollIntoView({ block: "center", inline: "nearest" });
      else window.scrollTo(0, document.documentElement.scrollHeight);
      const r = el.getBoundingClientRect();
      const inView = r.top >= 0 && r.bottom <= window.innerHeight;
      // Nine points across the target, not only its middle: a bar over one edge leaves the middle
      // free. The side columns sit half a height in, so a rounded corner is never sampled.
      const inset = Math.min(r.width / 2, r.height / 2);
      const xs = [r.left + inset, r.left + r.width / 2, r.right - inset];
      const ys = [r.top + 1, r.top + r.height / 2, r.bottom - 1];
      let coveredBy: string | null = null;
      if (inView) {
        for (const y of ys) {
          for (const x of xs) {
            const hit = document.elementFromPoint(x, y);
            if (coveredBy || (hit && (hit === el || el.contains(hit)))) continue;
            const where = `${Math.round(x - r.left)},${Math.round(y - r.top)} of ${Math.round(r.width)}x${Math.round(r.height)}`;
            coveredBy = hit ? `${hit.tagName}.${String(hit.className)} at ${where}` : `nothing at ${where}`;
          }
        }
      }
      return {
        inView, left: r.left, right: r.right, height: r.height, vw: window.innerWidth,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        clipped: el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight,
        coveredBy,
      };
    }, position);
    const at = `"${name}" at ${width}px, ${position}`;
    expect(layout.overflow, `no horizontal scroll: ${at}`).toBeLessThanOrEqual(0);
    expect(layout.left, `left edge: ${at}`).toBeGreaterThanOrEqual(0);
    expect(layout.right, `right edge: ${at}`).toBeLessThanOrEqual(layout.vw);
    expect(layout.clipped, `not clipped: ${at}`).toBe(false);
    expect(layout.height, `44px target: ${at}`).toBeGreaterThanOrEqual(44);
    expect(layout.coveredBy, `nothing covers it: ${at}`).toBeNull();
    if (position === "middle") expect(layout.inView, `can be scrolled into view: ${at}`).toBe(true);
  }
  await button.scrollIntoViewIfNeeded();
  return button;
}

/** What the note page says about the kept action, in the same words the fake server uses. */
async function screenState(page: Page): Promise<string> {
  const reflected = await page.locator(".reading-content__reflected").count();
  if (reflected) return "reflected";
  if (await page.getByRole("button", { name: STOP, exact: true }).count()) return "chosen";
  if (await page.getByRole("button", { name: KEEP, exact: true }).count()) return "none";
  return "unknown";
}

/**
 * Like screenState, but "busy" while a keep, stop or outcome request has not finished: the page
 * disables these buttons until then, also while a request waits for the network to come back.
 */
async function settledScreenState(page: Page): Promise<string> {
  const state = await screenState(page);
  const name = state === "chosen" ? STOP : state === "none" ? KEEP : null;
  if (name && !(await page.getByRole("button", { name, exact: true }).first().isEnabled())) return "busy";
  return state;
}

function serverState(server: FakeServer): string {
  return server.kept ? server.kept.state : "none";
}

/** The reader is on a "Đuối" day, so the page opens on the lighter action; show the card's own. */
async function showOwnAction(page: Page) {
  await page.getByRole("button", { name: SHOW_ORIGINAL, exact: true }).click();
  await expect(page.locator(".reading-content__action > .reading-content__experiment-action").first()).toHaveText(OWN);
}

// Negative controls: the layout check must fail when something covers the control or shrinks it.
test("the tap-target check catches a covered control and a control under 44px (#688)", async ({ page }) => {
  const server = new FakeServer(PROFILES[0]);
  await server.attach(page);
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/note/today");
  await expectTappable(page, KEEP, 360);

  const bar = await page.addStyleTag({ content: ".note-detail-actions { position: fixed !important; inset: 0 !important; z-index: 999 !important; background: #fff !important; }" });
  await expect(expectTappable(page, KEEP, 360)).rejects.toThrow(/nothing covers it/);
  await bar.evaluate((el) => el.parentNode?.removeChild(el));
  await expectTappable(page, KEEP, 360);

  // A strip over the bottom 16px only: the middle of the control still answers a tap, yet less
  // than 44px of it is free (#750).
  const keepButton = page.getByRole("button", { name: KEEP, exact: true });
  const strip = await keepButton.evaluateHandle((el) => {
    const r = el.getBoundingClientRect();
    const cover = document.createElement("div");
    cover.className = "e2e-partial-cover";
    cover.style.cssText = `position:absolute;left:${r.left + window.scrollX}px;top:${r.bottom - 16 + window.scrollY}px;width:${r.width}px;height:16px;z-index:999;background:#fff;`;
    document.body.appendChild(cover);
    return cover;
  });
  const partly = await keepButton.evaluate((el) => {
    el.scrollIntoView({ block: "center", inline: "nearest" });
    const r = el.getBoundingClientRect();
    const at = (y: number) => document.elementFromPoint(r.left + r.width / 2, y);
    const middle = at(r.top + r.height / 2);
    return { middleFree: middle === el || el.contains(middle), bottom: at(r.bottom - 2)?.className };
  });
  expect(partly, "the strip covers the bottom edge and leaves the middle free").toEqual({ middleFree: true, bottom: "e2e-partial-cover" });
  await expect(expectTappable(page, KEEP, 360)).rejects.toThrow(/nothing covers it/);
  await strip.evaluate((el) => el.remove());
  await expectTappable(page, KEEP, 360);

  await page.addStyleTag({ content: ".reading-content__experiment-button { min-height: 0 !important; height: 30px !important; }" });
  await expect(expectTappable(page, KEEP, 360)).rejects.toThrow(/44px target/);
  expect(server.unmocked, "API calls without a mock").toEqual([]);
});

for (const profile of PROFILES) {
  for (const width of [360, 390]) {
    test(`${profile.kind} at ${width}px: keep, stop, replace, lose the network, record an outcome, reload (#688)`, async ({ page }) => {
      const server = new FakeServer(profile);
      await server.attach(page);
      await page.setViewportSize({ width, height: 800 });
      const shot = (step: string) => page.screenshot({ path: resolve(OUT_DIR, `${profile.kind}-${width}-${step}.png`), fullPage: true, animations: "disabled" });

      // Keep the action on screen (the lighter one).
      await page.goto("/note/today");
      await expect(page.getByText(LIGHT, { exact: true })).toBeVisible();
      await (await expectTappable(page, KEEP, width)).click();
      await expectTappable(page, STOP, width);
      expect(server.kept?.action_key).toBe(LIGHT_KEY);
      await expect(page.locator(".home-status")).toHaveText("Đã giữ một việc nhỏ để thử hôm nay. Bạn có thể dừng bất cứ lúc nào.");
      await shot("kept");

      // Stop keeping it.
      await page.getByRole("button", { name: STOP, exact: true }).click();
      await expectTappable(page, KEEP, width);
      await expect.poll(() => server.kept).toBeNull();

      // Keep it again, then replace it with the card's own action: asks once before replacing.
      await page.getByRole("button", { name: KEEP, exact: true }).click();
      await expect(page.getByRole("button", { name: STOP, exact: true })).toBeVisible();
      await showOwnAction(page);
      await (await expectTappable(page, REPLACE, width)).click();
      expect(server.kept?.action_key, "the first press only asks").toBe(LIGHT_KEY);
      await expect(page.getByText("Việc đang giữ sẽ được thay thế.", { exact: false })).toBeVisible();
      await (await expectTappable(page, CONFIRM_REPLACE, width)).click();
      // The old kept action has its own "stop keeping" button until the replacement is stored.
      await expect(page.locator(".reading-content__held-experiment")).toHaveCount(0);
      await expectTappable(page, STOP, width);
      expect(server.kept?.action_key).toBe(OWN_KEY);

      // Reload: the page opens on the lighter action again and still shows what is kept.
      await page.reload();
      const held = page.locator(".reading-content__held-experiment");
      await expect(held.getByText(OWN, { exact: true })).toBeVisible();
      await expectTappable(page, STOP, width);
      await showOwnAction(page);
      await expect(held).toHaveCount(0);
      expect(await screenState(page)).toBe("chosen");

      // Lose the network, press "stop keeping", get the network back: screen and server agree,
      // whichever way the request went, and they still agree after a reload.
      server.down = true;
      await page.context().setOffline(true);
      await page.getByRole("button", { name: STOP, exact: true }).click();
      await page.waitForTimeout(300);
      server.down = false;
      await page.context().setOffline(false);
      // Agreement counts only once the request has finished and nothing is on the wire: a read on
      // reconnect can show "kept" again while the queued "stop keeping" is still to be sent (#750).
      await expect.poll(async () => `${await settledScreenState(page)} / server ${serverState(server)} / answering ${server.answering}`, { timeout: 10_000 })
        .toMatch(/^(chosen \/ server chosen|none \/ server none) \/ answering 0$/);
      const afterReconnect = serverState(server);
      test.info().annotations.push({ type: "after reconnect", description: afterReconnect });
      await page.reload();
      await showOwnAction(page);
      await expect.poll(() => screenState(page)).toBe(afterReconnect);
      if (afterReconnect === "none") {
        await page.getByRole("button", { name: KEEP, exact: true }).click();
        await expect(page.getByRole("button", { name: STOP, exact: true })).toBeVisible();
      }

      // Record an outcome: only after the reader opens that part themselves (US-03 AC34).
      await expect(page.getByRole("group", { name: "Điều gì đúng với bạn?" })).toHaveCount(0);
      await (await expectTappable(page, OPEN_REFLECTION, width)).click();
      for (const outcome of ["Chưa thử", "Có ích một chút", "Chưa thấy khác", "Không hợp lúc này"]) await expectTappable(page, outcome, width);
      await shot("outcomes");
      await page.getByRole("button", { name: "Có ích một chút", exact: true }).click();
      await expect(page.locator(".reading-content__reflected")).toHaveText("Đã nhìn lại: Có ích một chút");
      expect(server.kept).toMatchObject({ state: "reflected", outcome: "helpful", action_key: OWN_KEY });

      // Reload once more: the recorded outcome is still there.
      await page.reload();
      await showOwnAction(page);
      await expect(page.locator(".reading-content__reflected")).toHaveText("Đã nhìn lại: Có ích một chút");
      await shot("reflected");

      // Home shows the same day's action and still fits the width.
      await page.goto("/home");
      const advice = page.getByRole("complementary", { name: "Việc có thể thử hôm nay" });
      await expect(advice.getByText(LIGHT, { exact: true })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), `Home has no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);

      expect(server.unmocked, "API calls without a mock").toEqual([]);
    });
  }
}
