import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test, type Locator, type Page, type Route } from "@playwright/test";

// Screenshots of the key screens at 390x844 for PR review (ui-screens.yml).
// Same approach as tests/e2e: Vite preview, every /v1 call answered by page.route with fake data.
// The birth date below is the same synthetic fixture the e2e suite uses; nothing here is real.

const OUT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../test-results/ui-screens");
mkdirSync(OUT_DIR, { recursive: true });

type Scenario = {
  onboarding: "none" | "birth_pending" | "completed";
  deepData: boolean;
  ownerClaim: "ok" | "needs_chart";
};

const REVISION_ID = "00000000-0000-4000-8000-000000000010";
const NOTE_ID = "note-test";

const reveal = {
  profile_id: "profile-test",
  snapshot_id: "snapshot-test",
  birth_date: "1990-01-01",
  calculation: {
    status: "certain",
    sign: "capricorn",
    candidates: [],
    provenance: { engine: "swiss_ephemeris", version: "2.10.3", ephemeris_set: "sepl_18+semo_18+seas_18", profile: "natal-date-only-v1" },
  },
  created_at: "2026-08-31T00:00:00Z",
  resumed: false,
};

const dailyNote = {
  id: NOTE_ID, note_date: "2026-09-02", title: "Đừng biến mình thành deadline.",
  body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.", full_body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
  context_label: "Bản cũ", content_version: "daily-note-v1", persona_mode: "vibe", persona_label: "Mềm",
  persona_version: "persona-v1", source_level: "date_only", astrology_source_version: "2.10.03",
  fallback_used: false, fallback_reason: null, awakening: null, sky_chapter: null,
  created_at: "2026-09-02T00:00:00Z",
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    active: {
      revision_id: REVISION_ID, source: "deterministic",
      mode: "vibe_fallback", purpose: "daily_note", tradition: "western", precision: "unknown",
      sections: {
        hook: "Đừng biến mình thành deadline.", thesis: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
        manifestation: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
        transit: null, micro_action: "Bỏ một việc không cần xong hôm nay.",
      },
      evidence: { title: "Căn cứ trong lá số", claims: ["Ngày sinh đã cung cấp"], framework_disclosure: "Chiêm tinh là một khung diễn giải." },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-02T00:00:00Z",
    },
  },
};

const claimDetail = {
  hook: "Một tín hiệu riêng.", meaning: "Một lớp nghĩa có căn cứ.", manifestation: "Một biểu hiện đời thường.",
  watch_for: "Một điểm cần quan sát.", micro_action: "Một việc nhỏ để thử.", evidence: ["Một vị trí trong chart"],
};

const insightsLocked = {
  status: "locked", required_fields: ["birth_time", "birth_place"], reading: null,
  bodies: [], houses_available: false, time_precision: "unknown",
};

const insightsReady = {
  status: "ready", required_fields: [], houses_available: true, time_precision: "exact", bodies: [],
  reading: {
    tradition: "western", config_hash: "abc123456789", observed_at: "2026-09-04T00:00:00Z",
    disclaimer: "Nội dung tham khảo.",
    provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
    claims: [
      { ...claimDetail, id: "mercury-sign", domain: "mind", title: "Mạch suy nghĩ", summary: "Một lớp đọc thử.", factor_refs: ["natal:mercury"], confidence: "high" },
      { ...claimDetail, id: "venus-sign", domain: "relating", title: "Cách kết nối", summary: "Một lớp đọc thử.", factor_refs: ["natal:venus"], confidence: "high" },
      { ...claimDetail, id: "mars-sign", domain: "drive", title: "Động lực", summary: "Một lớp đọc thử.", factor_refs: ["natal:mars"], confidence: "high" },
    ],
  },
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
    active: {
      revision_id: REVISION_ID, source: "deterministic",
      mode: "full_synthesis", purpose: "aura", tradition: "western", precision: "exact",
      sections: {
        hook: "Nhiều lớp trong bạn đang nói cùng lúc.",
        thesis: "Bạn vừa cần tự do, vừa cần một nơi đủ chắc để quay về.",
        manifestation: "Ngoài đời có thể trông như việc bạn đổi nhịp rất nhanh.",
        transit: null, micro_action: "Chọn một việc cần rõ trước tối nay.",
      },
      evidence: { title: "Căn cứ trong lá số", claims: ["Sao Thủy ở Song Tử"], framework_disclosure: "Khung diễn giải." },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-07T00:00:00Z",
    },
  },
};

const savedNote = {
  id: "33333333-3333-4333-8333-333333333333", daily_note_id: "44444444-4444-4444-8444-444444444444",
  revision_id: null, saved_at: "2026-09-01T08:00:00Z",
  note_snapshot: { title: "Ghi chú thử nghiệm đã lưu", body: "Đoạn văn thử nghiệm của note đã lưu." },
};

const shareArtifact = {
  id: "share-test", daily_note_id: NOTE_ID, format: "story_9_16",
  safe_snapshot: {
    title: "Đừng biến mình thành deadline.", body: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
    context_label: "Vibe · một lớp", content_version: "daily-note-v1", persona_mode: "vibe",
    persona_label: "Mềm", persona_version: "persona-v1", watermark: "Lá Lành",
  },
  token: "share-token", public_path: "/share/share-token",
  created_at: "2026-09-02T00:00:00Z", expires_at: "2026-09-16T00:00:00Z", revision_id: REVISION_ID,
};

function session(onboarding: Exclude<Scenario["onboarding"], "none">) {
  return { state: "active", onboarding_status: onboarding, expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };
}

type Reply = { status: number; json?: unknown; headers?: Record<string, string> };

function answer(scenario: Scenario, method: string, path: string): Reply | null {
  const signedIn = scenario.onboarding !== "none";
  const key = `${method} ${path}`;
  switch (key) {
    case "GET /v1/session":
      return signedIn ? { status: 200, json: session(scenario.onboarding as "completed") } : { status: 401, json: { code: "GUEST_SESSION_MISSING" } };
    case "POST /v1/session/renew":
    case "GET /v1/session/onboarding-status":
    case "POST /v1/session/onboarding-status":
      return signedIn ? { status: 200, json: session(scenario.onboarding as "completed") } : { status: 401, json: { code: "GUEST_SESSION_MISSING" } };
    case "POST /v1/guest-sessions":
      return {
        status: 201, headers: { "set-cookie": "la_lanh_csrf=csrf-test; Path=/; SameSite=Lax" },
        json: { ...session("birth_pending"), csrf_token: "csrf-test", resumed: false },
      };
    case "POST /v1/session/birth-profile-consent":
      return { status: 204 };
    case "GET /v1/birth-profile":
      return scenario.onboarding === "completed" ? { status: 200, json: reveal } : { status: 404, json: { code: "BIRTH_PROFILE_NOT_FOUND" } };
    case "GET /v1/birth-profile/supplement":
      return scenario.deepData
        ? { status: 200, json: { profile_id: "profile-test", profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null } }
        : { status: 200, json: { profile_id: "profile-test", profile_level: 1, birth_time_mode: "unknown", time_precision: "unknown", place_display_name: null, timezone_id: null, approx_window: null } };
    case "GET /v1/daily-note":
      return { status: 200, json: dailyNote };
    case `GET /v1/daily-note/${NOTE_ID}/mood`:
      return { status: 200, json: null };
    case "GET /v1/daily-note/resonance":
      return { status: 200, json: { consented: false, feedback_count: 0, last_choice: null } };
    case "GET /v1/daily-note/experiment":
      return { status: 200, json: null };
    case "GET /v1/saved-notes":
      return { status: 200, json: [savedNote] };
    case "GET /v1/share-artifacts":
      return { status: 200, json: { items: [], next_cursor: null } };
    case `POST /v1/daily-note/${NOTE_ID}/share-artifacts`:
      return { status: 200, json: shareArtifact };
    case "GET /v1/insights/overview":
      return { status: 200, json: scenario.deepData ? insightsReady : insightsLocked };
    case "GET /v1/insights/current-sky":
      return { status: 200, json: {
        observed_at: "2026-09-28T00:00:00Z", tradition: "western", config_hash: "sky-test",
        bodies: [{ body: "sun", sign: "libra", longitude: 185, degree_in_sign: 5, retrograde: false }],
        note: "Ảnh chụp bầu trời, không phải lời phán.",
      } };
    case "POST /v1/identity/claim":
      return scenario.ownerClaim === "ok"
        ? { status: 200, json: { expires_at: "2026-12-30T00:00:00Z", principal_id: "00000000-0000-4000-8000-000000000001", resumed: true } }
        : { status: 401, json: { code: "OWNER_CHART_REQUIRED" } };
    case "GET /v1/radar/requests":
      return { status: 200, json: [] };
    case "GET /v1/birth-places/search":
      return { status: 200, json: [] };
    default:
      return null;
  }
}

// Calls with no fake answer get 503 and are listed in the test annotations, so a screen that
// starts calling a new endpoint is visible in the report instead of silently half-rendered.
async function mockApi(page: Page, scenario: Scenario) {
  const unmocked: string[] = [];
  await page.route("**/v1/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const reply = answer(scenario, request.method(), path);
    if (reply === null) {
      unmocked.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 503, json: { code: "SCREENS_UNMOCKED", path } });
      return;
    }
    await route.fulfill(reply.status === 204 ? { status: 204, headers: reply.headers } : { status: reply.status, json: reply.json, headers: reply.headers });
  });
  return unmocked;
}

async function shoot(page: Page, name: string, ready: Locator) {
  await expect(ready).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: resolve(OUT_DIR, `${name}.png`), fullPage: true, animations: "disabled" });
}

const signedIn: Scenario = { onboarding: "completed", deepData: false, ownerClaim: "needs_chart" };

const screens: Array<{ name: string; scenario: Scenario; path: string; ready: (page: Page) => Locator; before?: (page: Page) => Promise<void> }> = [
  {
    name: "01-welcome", path: "/welcome",
    scenario: { onboarding: "none", deepData: false, ownerClaim: "needs_chart" },
    ready: (page) => page.getByRole("button", { name: "Đồng ý & bắt đầu" }),
  },
  {
    name: "02-birth-date", path: "/birth",
    scenario: { onboarding: "birth_pending", deepData: false, ownerClaim: "needs_chart" },
    ready: (page) => page.getByRole("button", { name: "Khớp tín hiệu" }),
  },
  {
    name: "03-reveal", path: "/reveal", scenario: signedIn,
    ready: (page) => page.getByRole("button", { name: "Mở Note hôm nay" }),
  },
  {
    name: "04-home-note-mood", path: "/home", scenario: signedIn,
    ready: (page) => page.getByRole("region", { name: "Hôm nay bạn thấy sao?" }).getByRole("button", { name: "Chọn cảm giác hôm nay" }),
    before: async (page) => {
      await expect(page.getByRole("region", { name: "Note hôm nay" }).getByRole("heading", { name: "Đừng biến mình thành deadline." })).toBeVisible();
    },
  },
  {
    name: "05-note-detail", path: "/note/today", scenario: signedIn,
    ready: (page) => page.getByRole("button", { name: /^Lưu/ }),
  },
  {
    name: "06-saved", path: "/saved", scenario: signedIn,
    ready: (page) => page.getByText("Ghi chú thử nghiệm đã lưu"),
  },
  {
    name: "07-kham-pha-locked", path: "/insights", scenario: signedIn,
    ready: (page) => page.getByRole("link", { name: "Thêm giờ & nơi sinh" }),
  },
  {
    name: "08-kham-pha-unlocked", path: "/insights", scenario: { ...signedIn, deepData: true },
    ready: (page) => page.getByRole("heading", { name: "Nhiều lớp trong bạn đang nói cùng lúc." }),
  },
  {
    name: "09-radar-start-date-only-gate", path: "/radar/start", scenario: signedIn,
    ready: (page) => page.getByRole("heading", { name: "Chart của bạn cần có trước." }),
  },
  {
    name: "10-radar-start-full-form", path: "/radar/start", scenario: { ...signedIn, deepData: true, ownerClaim: "ok" },
    ready: (page) => page.getByRole("button", { name: /Check kín ngay/ }),
  },
  {
    name: "11-card", path: "/card", scenario: signedIn,
    ready: (page) => page.getByRole("heading", { name: "Đừng biến mình thành deadline." }),
  },
  {
    name: "12-card-share-link", path: "/card", scenario: signedIn,
    ready: (page) => page.getByRole("status"),
    before: async (page) => {
      await page.getByRole("button", { name: /safe link/i }).click();
    },
  },
];

for (const screen of screens) {
  test(screen.name, async ({ page }) => {
    const unmocked = await mockApi(page, screen.scenario);
    await page.goto(screen.path);
    if (screen.before) await screen.before(page);
    await shoot(page, screen.name, screen.ready(page));
    if (unmocked.length) {
      const description = Array.from(new Set(unmocked)).join(", ");
      test.info().annotations.push({ type: "unmocked", description });
      console.log(`${screen.name}: no fake answer for ${description}`);
    }
  });
}
