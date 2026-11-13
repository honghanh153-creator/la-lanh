import { expect, test } from "@playwright/test";

// Fix-forward #225: G2 evidence for the #143 E2 content-error state on /insights
// (360/390px, no horizontal scroll, keyboard reachable, announced as an alert). Synthetic data only.
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
  await page.route("**/v1/insights/overview**", async (route) => route.fulfill({ status: 422, json: {
    type: "about:blank", title: "Unprocessable", status: 422, code: "READING_CONTENT_REJECTED", detail: "Insight reading is temporarily unavailable",
  } }));
});
test.afterEach(() => {
  expect(unmocked, "API calls without a mock").toEqual([]);
});

test("a rejected reading stays usable at 360 and 390px (#225)", async ({ page }) => {
  for (const width of [360, 390]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/insights");
    const alert = page.getByRole("alert").filter({ has: page.getByRole("heading", { name: "Chưa mở được bản đọc." }) });
    await expect(alert).toBeVisible();
    await expect(alert.getByText("Không cần điền lại khi thông tin đã đủ.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Thử lại" })).toHaveCount(0);
    const layout = await page.evaluate(() => {
      const box = document.querySelector(".cosmic-state[role=alert]")!.getBoundingClientRect();
      return { overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, left: box.left, right: box.right, vw: window.innerWidth };
    });
    expect(layout.overflow).toBeLessThanOrEqual(0);
    expect(layout.left).toBeGreaterThanOrEqual(0);
    expect(layout.right).toBeLessThanOrEqual(layout.vw);
    // The heading and message must be fully readable: no overflow clipping inside the
    // element or by any clipping ancestor up to the alert.
    const clipped = await page.evaluate(() => {
      const root = document.querySelector(".cosmic-state[role=alert]") as HTMLElement;
      const out: string[] = [];
      for (const el of Array.from(root.querySelectorAll<HTMLElement>("h1, h2, h3, p"))) {
        if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) out.push(`${el.tagName} overflows itself`);
        const r = el.getBoundingClientRect();
        for (let a = el.parentElement; a; a = a.parentElement) {
          const st = getComputedStyle(a);
          if (st.overflowX !== "visible" || st.overflowY !== "visible" || a === root) {
            const c = a.getBoundingClientRect();
            if (r.left < c.left - 1 || r.right > c.right + 1 || r.top < c.top - 1 || r.bottom > c.bottom + 1) out.push(`${el.tagName} clipped by ${a.tagName}`);
          }
          if (a === root) break;
        }
      }
      return out;
    });
    expect(clipped, `error text is not clipped at ${width}px`).toEqual([]);
  }
});

test("a rejected reading can be left by keyboard (#225)", async ({ page, isMobile }) => {
  test.skip(isMobile, "touch emulation has no Tab focus; the desktop project covers the keyboard");
  await page.goto("/insights");
  await expect(page.getByRole("heading", { name: "Chưa mở được bản đọc." })).toBeVisible();
  // Keyboard: Tab moves forward from the top through the page controls without a trap,
  // and every focused control is visible on screen.
  const seen: string[] = [];
  for (let i = 0; i < 14; i += 1) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body) return null;
      const r = el.getBoundingClientRect();
      let shown = el.checkVisibility({ opacityProperty: true, visibilityProperty: true });
      for (let a: HTMLElement | null = el; a && shown; a = a.parentElement) if (Number(getComputedStyle(a).opacity) === 0) shown = false;
      const inViewport = r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < window.innerWidth && r.top < window.innerHeight;
      return { name: el.getAttribute("aria-label") ?? el.textContent?.trim() ?? "", visible: shown && inViewport };
    });
    if (!focused) continue;
    expect(focused.visible, `${focused.name} is visible when focused`).toBe(true);
    seen.push(focused.name);
  }
  expect(seen).toContain("Về hôm nay");
  expect(seen).toContain("Cách tính");
  expect(seen.some((name) => name.startsWith("Tây phương"))).toBe(true);
  expect(seen.some((name) => name.startsWith("Jyotish"))).toBe(true);
});
