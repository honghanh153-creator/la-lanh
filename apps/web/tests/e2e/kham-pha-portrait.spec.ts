import { expect, test, type Page } from "@playwright/test";

// Lesson L08 (agreement 12.11 item F): the Khám phá portrait with real-length text at 360 and 390px,
// text at 200% and reduced motion: the summary reads in full, a claim opens, its evidence opens,
// and going back leaves Khám phá usable. US-07 AC13 asks for 200% text and Reduce Motion.
// Plan critiqued by Codex on 14.11 (SỬA): the real font size is measured (not just a style added),
// the summary must not be clamped or cut (with a negative control), and reduced motion is checked
// by its effect: no element keeps a running animation or transition.
// Text: product sentences from apps/api/app/domains/content/copy_registry.json, not filler.
// Synthetic profile and data only.
const SECTIONS = {
  hook: "Lúc trưa, bạn thân nhắn xin dời buổi cà phê đã hẹn chiều nay sang tuần sau, nhưng chưa nói ngày nào.",
  thesis: "Khi thấy người khác làm cùng việc nhưng nhanh hơn, bạn có thể quên mỗi người bắt đầu ở một chỗ khác.",
  manifestation: "Trong nhóm chat lớp, mọi người khoe kết quả thi, còn bạn đọc hết rồi tắt máy mà không nói điểm mình.",
  transit: null,
  micro_action: "Khi người kia nói món canh hôm nay hơi mặn, bạn giải thích ngay rằng mình nấu theo cách này lâu rồi.",
};
const EVIDENCE = ["Mặt Trăng ở Bọ Cạp", "Mặt Trăng ở Nhà 8", "Mặt Trăng đối đỉnh Thiên Vương · orb 0.42°"];
const CLAIM = {
  id: "moon-sign", domain: "emotions", title: "Nhịp cảm xúc", confidence: "high",
  summary: "Đồng nghiệp gửi bình chọn phần mềm mới, cả nhóm chọn cùng một cái, bạn sắp chọn theo dù chưa dùng thử.",
  hook: "Nhóm lớp có tin nhắn của thầy dặn tuần sau đọc trước chương ba, trong khi môn này dùng hai cuốn sách.",
  meaning: "Khóa học dạy những thứ bạn không dùng khi làm việc, nhưng lúc nghĩ đến chuyện nghỉ, bạn lại tiếc tiền.",
  manifestation: SECTIONS.manifestation, watch_for: SECTIONS.thesis, micro_action: SECTIONS.micro_action,
  evidence: EVIDENCE, factor_refs: ["natal:moon:sign:scorpio", "natal:moon:house:8"],
};
const OVERVIEW = {
  status: "ready", required_fields: [], houses_available: true, time_precision: "exact", bodies: [],
  reading: {
    tradition: "western", config_hash: "abc123456789", observed_at: "2026-11-06T00:00:00Z", disclaimer: "Nội dung tham khảo.",
    provenance: { engine: "swiss_ephemeris", version: "2.10.03", release_commit: "x", ephemeris_set: "se1", profile: "v2", tradition: "western", zodiac: "tropical", ayanamsa: null, config_hash: "abc123456789" },
    claims: [CLAIM],
  },
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
    active: {
      revision_id: "11111111-1111-4111-8111-111111111111", source: "deterministic",
      mode: "full_synthesis", purpose: "aura", tradition: "western", precision: "exact", sections: SECTIONS,
      evidence: { title: "Căn cứ trong lá số", claims: EVIDENCE, framework_disclosure: "Khung diễn giải." },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-11-07T00:00:00Z",
    },
  },
};

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
    profile_id: "profile-test", profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null,
  } }));
  await page.route("**/v1/insights/overview**", async (route) => route.fulfill({ status: 200, json: OVERVIEW }));
});
test.afterEach(() => {
  expect(unmocked, "API calls without a mock").toEqual([]);
});

// 200% text, then wait until the browser applied it: with reduced motion the app keeps a near-zero
// transition, so the computed size changes on the next frames, not at once.
async function bigText(page: Page) {
  const base = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize));
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  await expect.poll(() => page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize)), { message: "root text doubled" }).toBeGreaterThanOrEqual(base * 1.95);
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(() => done(null)))));
}

test("Khám phá reads, opens a claim and its evidence, and comes back at 360/390px, 200% text, reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const width of [360, 390]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/insights?tradition=western");
    const card = page.locator(".insight-synthesis");
    await expect(card.getByRole("heading", { name: SECTIONS.hook })).toBeVisible();
    const before = await page.evaluate(measureSummary);
    await bigText(page);
    const after = await page.evaluate(measureSummary);
    // The real size doubled; a style that did not apply would leave it unchanged.
    expect(after.rootPx, `root text at ${width}px`).toBeGreaterThanOrEqual(before.rootPx * 1.95);
    expect(after.thesisPx, `summary text at ${width}px`).toBeGreaterThanOrEqual(before.thesisPx * 1.5);
    expect(after.overflow, `no horizontal scroll at ${width}px`).toBeLessThanOrEqual(0);
    for (const part of after.parts) {
      expect(part.text.replace(/\s+/g, " ").trim(), "the whole sentence is in the page").toBe(part.expected);
      expect(part.clipped, `${part.name} is not clamped or cut at ${width}px`).toBe(false);
      expect(part.left, `${part.name} starts inside the screen`).toBeGreaterThanOrEqual(0);
      expect(part.right, `${part.name} ends inside the screen`).toBeLessThanOrEqual(after.vw + 0.5);
    }
    expect(after.moving, `nothing animates with reduced motion at ${width}px`).toEqual([]);

    // A claim (nhận định) opens, its evidence opens, and back returns to a usable Khám phá.
    await page.getByRole("link", { name: new RegExp(CLAIM.title) }).click();
    await expect(page).toHaveURL(/\/insights\/moon-sign/);
    await page.getByText("Căn cứ trong lá số").first().click();
    for (const line of EVIDENCE) await expect(page.getByText(line, { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), `detail fits at ${width}px`).toBeLessThanOrEqual(0);
    await page.goBack();
    await expect(page).toHaveURL(/\/insights\?/);
    await expect(page.locator(".insight-synthesis").getByRole("heading", { name: SECTIONS.hook })).toBeVisible();
    await expect(page.getByRole("link", { name: new RegExp(CLAIM.title) })).toBeEnabled();
  }
});

test("the checks see a cut summary and a running animation (negative controls)", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/insights?tradition=western");
  await expect(page.locator(".insight-synthesis").getByRole("heading", { name: SECTIONS.hook })).toBeVisible();
  await bigText(page);
  await page.addStyleTag({ content: ".insight-synthesis p { display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }" });
  const clamped = await page.evaluate(measureSummary);
  expect(clamped.parts.find((p) => p.name === "thesis")?.clipped, "a one-line clamp counts as cut").toBe(true);
  await page.addStyleTag({ content: "@keyframes e2e-spin { to { transform: rotate(1turn); } } .insight-synthesis h2 { animation: e2e-spin 2s linear infinite; }" });
  const moving = await page.evaluate(measureSummary);
  expect(moving.moving.length, "a running animation is seen").toBeGreaterThan(0);
});

// Runs in the page. Clipped: content overflows its box on either axis (clamp, max-height, ellipsis).
function measureSummary() {
  const css = (el: Element) => getComputedStyle(el);
  const px = (el: Element | null) => (el ? parseFloat(css(el).fontSize) : 0);
  const card = document.querySelector(".insight-synthesis");
  const parts = [["hook", "h2"], ["thesis", "p:not(.reading-mode)"]].map(([name, selector]) => {
    const el = card?.querySelector(selector) as HTMLElement | null;
    const r = el?.getBoundingClientRect();
    return {
      name, text: el?.innerText ?? "", left: r?.left ?? -1, right: r?.right ?? Infinity,
      expected: name === "hook" ? "Lúc trưa, bạn thân nhắn xin dời buổi cà phê đã hẹn chiều nay sang tuần sau, nhưng chưa nói ngày nào." : "Khi thấy người khác làm cùng việc nhưng nhanh hơn, bạn có thể quên mỗi người bắt đầu ở một chỗ khác.",
      clipped: !el || el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1,
    };
  });
  // Reduced motion by its effect: any element in the page with a running animation or a
  // transition longer than 10 ms.
  const seconds = (value: string) => Math.max(...value.split(",").map((v) => (v.trim().endsWith("ms") ? parseFloat(v) / 1000 : parseFloat(v)) || 0));
  const moving = Array.from(document.querySelectorAll("main *")).filter((el) => {
    const s = css(el);
    const animated = s.animationName !== "none" && seconds(s.animationDuration) > 0.01 && s.animationPlayState !== "paused";
    return animated || seconds(s.transitionDuration) > 0.01 && s.transitionProperty !== "none";
  }).map((el) => `${el.tagName.toLowerCase()}.${String((el as HTMLElement).className).split(" ")[0]}`).slice(0, 10);
  return {
    rootPx: px(document.documentElement), thesisPx: px(card?.querySelector("p:not(.reading-mode)") ?? null),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, vw: window.innerWidth, parts, moving,
  };
}
