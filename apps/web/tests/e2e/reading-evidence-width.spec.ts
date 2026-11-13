import { expect, test } from "@playwright/test";

// Fix-forward #233: G2 evidence for PR #219 (Vietnamese names for every body in aspect lines).
// The longest names (Thiên Vương, Diêm Vương, Nút Bắc) must wrap inside the evidence list at
// 360 and 390px, with no horizontal scroll and no clipped line. Synthetic data only.
const EVIDENCE = [
  "Mặt Trăng ở Bọ Cạp",
  "Mặt Trăng ở Nhà 8",
  "Mặt Trăng đối đỉnh Thiên Vương · orb 0.42°",
  "Mặt Trăng đồng cung Diêm Vương · orb 1.24°",
  "Mặt Trăng quincunx Nút Bắc · orb 2.07°",
];

let unmocked: string[] = [];
test.beforeEach(async ({ page }) => {
  unmocked = [];
  await page.route("**/v1/**", async (route) => {
    const path = `${route.request().method()} ${new URL(route.request().url()).pathname}`;
    unmocked.push(path);
    await route.fulfill({ status: 503, json: { code: "E2E_UNMOCKED", path } });
  });
  const active = { state: "active", onboarding_status: "completed", expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };
  await page.route("**/v1/session", async (route) => route.fulfill({ status: 200, json: active }));
  await page.route("**/v1/session/renew", async (route) => route.fulfill({ status: 200, json: active }));
  await page.route("**/v1/birth-profile/supplement", async (route) => route.fulfill({ status: 200, json: {
    profile_id: "profile-test", profile_level: 2, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null,
  } }));
  await page.route("**/v1/insights/overview**", async (route) => route.fulfill({ status: 200, json: {
    status: "ready", required_fields: [], houses_available: true, time_precision: "exact", bodies: [],
    reading: {
      tradition: "western", config_hash: "abc123456789", observed_at: "2026-11-06T00:00:00Z",
      disclaimer: "Nội dung tham khảo.",
      provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
      claims: [{
        id: "moon-sign", domain: "emotions", title: "Nhịp cảm xúc", summary: "Mặt Trăng ở Bọ Cạp · Nhà 8.", confidence: "high",
        hook: "Một tín hiệu riêng.", meaning: "Một lớp nghĩa.", manifestation: "Một biểu hiện đời thường.",
        watch_for: "Một điểm cần quan sát.", micro_action: "Một việc nhỏ để thử.",
        evidence: EVIDENCE,
        factor_refs: ["natal:moon:sign:scorpio", "natal:moon:house:8"],
      }],
    },
  } }));
});
test.afterEach(() => {
  expect(unmocked, "API calls without a mock").toEqual([]);
});

test("aspect lines with long Vietnamese names fit at 360 and 390px (#233)", async ({ page }) => {
  for (const width of [360, 390]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/insights/moon-sign?tradition=western");
    await page.getByText("Căn cứ trong lá số").click();
    for (const line of EVIDENCE) await expect(page.getByText(line, { exact: true })).toBeVisible();
    const layout = await page.evaluate(measureLayout);
    expect(layout.overflow, `no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);
    expect(layout.items).toHaveLength(EVIDENCE.length);
    for (const item of layout.items) {
      expect(item.left, `${item.text} at ${width}px`).toBeGreaterThanOrEqual(0);
      expect(item.right, `${item.text} at ${width}px`).toBeLessThanOrEqual(layout.vw);
      expect(item.clipped, `${item.text} is not clipped at ${width}px`).toBe(false);
    }
  }
  // Negative control (#271): a height cap below one line (li line-height is 1.5) must count as clipping.
  await page.addStyleTag({ content: ".reading-evidence li { max-height: 1em !important; overflow: hidden !important; }" });
  const capped = await page.evaluate(measureLayout);
  expect(capped.items.some((item) => item.clipped), "vertical clipping is detected").toBe(true);
});

// Runs in the page. An item is clipped when its content overflows either axis.
function measureLayout() {
  return {
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    vw: window.innerWidth,
    items: Array.from(document.querySelectorAll(".reading-evidence li")).map((el) => {
      const r = el.getBoundingClientRect();
      return { text: el.textContent ?? "", left: r.left, right: r.right, clipped: el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight };
    }),
  };
}
