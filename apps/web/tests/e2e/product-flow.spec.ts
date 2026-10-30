import { expect, test } from "@playwright/test";

import type { components } from "@la-lanh/contracts";

type DailyNote = components["schemas"]["DailyNoteResponse"];

const reveal = {
  profile_id: "profile-test",
  snapshot_id: "snapshot-test",
  birth_date: "1990-01-01",
  calculation: {
    status: "certain",
    sign: "capricorn",
    candidates: [],
    provenance: {
      engine: "swiss_ephemeris",
      version: "2.10.3",
      ephemeris_set: "sepl_18+semo_18+seas_18",
      profile: "natal-date-only-v1",
    },
  },
  created_at: "2026-08-31T00:00:00Z",
  resumed: false,
};

// The suite runs against Vite preview only, with no API process: every /v1 call a test does not
// mock answers with an explicit failure instead of a proxy ECONNREFUSED, and the test fails listing
// those paths (registered first, so the specific routes in each test take precedence).
let unmocked: string[] = [];
test.beforeEach(async ({ page }) => {
  unmocked = [];
  await page.route("**/v1/**", async (route) => {
    const path = `${route.request().method()} ${new URL(route.request().url()).pathname}`;
    unmocked.push(path);
    await route.fulfill({ status: 503, json: { code: "E2E_UNMOCKED", path } });
  });
  await page.route("**/v1/session/renew", async (route) => route.fulfill({ status: 200, json: {
    state: "active", onboarding_status: "completed", expires_at: "2026-09-30T00:00:00Z", resumed: true, session_epoch: "epoch-test",
  } }));
  await page.route("**/v1/session/birth-profile-consent", async (route) => route.fulfill({ status: 204 }));
  // US-24: /tarot asks whether the human reader is on; it is off, as everywhere today.
  await page.route("**/v1/human-tarot/availability", async (route) => route.fulfill({ status: 200, json: {
    enabled: false, accepting: false, reason: "disabled", local_date: "2026-09-01", closes_at: "2026-09-01T11:00:00Z",
    release_at: "2026-09-01T15:00:00Z", daily_limit: 10, remaining: 10, consent_version: "human-tarot-v1", current_request_id: null,
  } }));
});
test.afterEach(() => {
  expect(unmocked, "API calls without a mock").toEqual([]);
});

test("guest can reveal, save mood, and create a share card", async ({ page }) => {
  let guestCreated = false;
  let birthProfileCreates = 0;
  let birthProfileReads = 0;
  let dailyNoteReads = 0;
  let savedRevisionId: string | null = null;
  let sharedRevisionId: string | null = null;
  let moodSaved: string | null = null;
  await page.route("**/v1/session", async (route) => {
    await route.fulfill(guestCreated ? {
      status: 200,
      json: { state: "active", onboarding_status: "birth_pending", expires_at: "2026-09-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" },
    } : { status: 401, json: { code: "GUEST_SESSION_MISSING" } });
  });
  await page.route("**/v1/guest-sessions", async (route) => {
    guestCreated = true;
    await route.fulfill({
      status: 201,
      headers: { "set-cookie": "la_lanh_csrf=csrf-test; Path=/; SameSite=Lax" },
      json: {
        state: "active",
        onboarding_status: "birth_pending",
        expires_at: "2026-09-30T00:00:00Z",
        csrf_token: "csrf-test",
        resumed: false,
        session_epoch: "epoch-test",
      },
    });
  });
  await page.route("**/v1/birth-profile", async (route) => {
    if (route.request().method() === "POST") {
      birthProfileCreates += 1;
      await route.fulfill({ status: 201, json: reveal });
      return;
    }
    birthProfileReads += 1;
    await route.fulfill({ status: 200, json: reveal });
  });
  await page.route("**/v1/session/onboarding-status", async (route) => {
    await route.fulfill({ status: 200, json: { state: "active", onboarding_status: "completed", expires_at: "2026-09-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" } });
  });
  await page.route("**/v1/daily-note", async (route) => {
    dailyNoteReads += 1;
    await route.fulfill({ status: 200, json: {
      id: "note-test", note_date: "2026-09-02", title: "Đừng biến mình thành deadline.",
      body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.", full_body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
      context_label: "Bản cũ", content_version: "daily-note-v1", persona_mode: "vibe", persona_label: "Mềm",
      persona_version: "persona-v1", source_level: "date_only", astrology_source_version: "2.10.03",
      fallback_used: false, fallback_reason: null, awakening: null, sky_chapter: null,
      created_at: "2026-09-02T00:00:00Z",
      reading_projection: {
        scope_key: "a".repeat(64), available_update: null,
        active: {
          revision_id: "00000000-0000-4000-8000-000000000010", source: "deterministic",
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
    } });
  });
  await page.route("**/v1/daily-note/note-test/mood", async (route) => {
    if (route.request().method() === "GET") return route.fulfill({ status: 200, json: null });
    moodSaved = (route.request().postDataJSON() as { mood?: string }).mood ?? null;
    await route.fulfill({ status: 200, json: { id: "mood-test", daily_note_id: "note-test", mood: "Chill", checked_in_at: "2026-09-02T00:00:00Z" } });
  });
  await page.route("**/v1/daily-note/resonance", async (route) => route.fulfill({ status: 200, json: {
    consented: false, feedback_count: 0, last_choice: null,
  } }));
  await page.route("**/v1/daily-note/experiment", async (route) => route.fulfill({ status: 200, json: null }));
  await page.route("**/v1/saved-notes", async (route) => route.fulfill({ status: 200, json: [] }));
  await page.route("**/v1/daily-note/note-test/saved", async (route) => {
    savedRevisionId = (route.request().postDataJSON() as { revision_id?: string }).revision_id ?? null;
    await route.fulfill({ status: 200, json: { id: "saved-test", daily_note_id: "note-test", note_snapshot: {}, saved_at: "2026-09-02T00:00:00Z", revision_id: savedRevisionId } });
  });
  await page.route("**/v1/daily-note/note-test/share-artifacts", async (route) => {
    sharedRevisionId = (route.request().postDataJSON() as { revision_id?: string }).revision_id ?? null;
    await route.fulfill({ status: 200, json: {
      id: "share-test", daily_note_id: "note-test", format: "story_9_16",
      safe_snapshot: {
        title: "Đừng biến mình thành deadline.", body: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
        context_label: "Vibe · một lớp", content_version: "daily-note-v1", persona_mode: "vibe",
        persona_label: "Mềm", persona_version: "persona-v1", watermark: "Lá Lành",
      },
      token: "share-token", public_path: "/share/share-token",
      created_at: "2026-09-02T00:00:00Z", expires_at: "2026-09-16T00:00:00Z",
      revision_id: sharedRevisionId,
    } });
  });
  await page.route("**/v1/birth-profile/supplement", async (route) => route.fulfill({ status: 404, json: { code: "BIRTH_PROFILE_NOT_FOUND" } }));
  await page.route("**/v1/insights/overview**", async (route) => route.fulfill({ status: 200, json: {
    status: "locked", required_fields: ["birth_time", "birth_place"], reading: null,
    bodies: [], houses_available: false, time_precision: "unknown",
  } }));
  await page.route("**/v1/insights/current-sky**", async (route) => route.fulfill({ status: 200, json: {
    observed_at: "2026-09-28T00:00:00Z", tradition: "western", config_hash: "sky-test",
    bodies: [{ body: "sun", sign: "libra", longitude: 185, degree_in_sign: 5, retrograde: false }],
    note: "Ảnh chụp bầu trời, không phải lời phán.",
  } }));

  await page.goto("/welcome");
  await page.getByRole("button", { name: "Đồng ý & bắt đầu" }).click();
  await expect(page).toHaveURL(/\/birth$/);

  await page.getByRole("textbox", { name: "Ngày" }).fill("01");
  await page.getByRole("textbox", { name: "Tháng" }).fill("01");
  await page.getByRole("textbox", { name: "Năm" }).fill("1990");
  await page.getByRole("button", { name: "Khớp tín hiệu" }).click();

  await expect(page.getByRole("heading", { name: "Vibe · Mềm" })).toBeVisible();
  await expect(page.getByText("Mặt Trời Ma Kết", { exact: false })).toBeVisible();
  expect(birthProfileCreates).toBe(1);
  expect(birthProfileReads).toBe(0);
  expect(dailyNoteReads).toBe(1);
  await page.getByRole("button", { name: "Mở Note hôm nay" }).click();

  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByRole("heading", { level: 1, name: "Hôm nay có gì đáng để ý?" })).toBeVisible();
  const note = page.getByRole("region", { name: "Note hôm nay" });
  await expect(note.getByRole("heading", { name: "Đừng biến mình thành deadline." })).toBeVisible();
  expect(birthProfileReads).toBe(0);

  await page.getByRole("link", { name: /Rút Tarot/ }).click();
  await expect(page).toHaveURL(/\/tarot$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/home$/);

  await page.getByRole("navigation", { name: "Điều hướng chính" }).getByRole("link", { name: "Khám phá" }).click();
  await expect(page).toHaveURL(/\/insights$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByText("Lá Chứng")).toHaveCount(0);

  await page.getByRole("button", { name: "Chọn mood hôm nay" }).click();
  await page.getByRole("button", { name: /Chill/ }).click();
  await expect.poll(() => moodSaved).toBe("Chill");

  await note.getByRole("link", { name: "Đọc đầy đủ" }).click();
  await expect(page).toHaveURL(/\/note\/today$/);
  await page.getByRole("button", { name: /^Lưu/ }).click();
  await expect(page.getByRole("button", { name: /Đã lưu/ })).toBeVisible();
  expect(savedRevisionId).toBe("00000000-0000-4000-8000-000000000010");

  await page.goto("/card");
  await expect(page.getByRole("heading", { name: "Đừng biến mình thành deadline." })).toBeVisible();
  await page.getByRole("button", { name: /safe link/i }).click();
  await expect(page.getByRole("status")).toContainText("Không kèm ngày/giờ/nơi sinh");
  expect(sharedRevisionId).toBe("00000000-0000-4000-8000-000000000010");
});

test("under-18 birth date is stopped before any personal data is sent", async ({ page }) => {
  let birthProfileRequests = 0;
  await page.route("**/v1/session", async (route) => route.fulfill({ status: 200, json: { state: "active", onboarding_status: "birth_pending", expires_at: "2026-09-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" } }));
  await page.route("**/v1/birth-profile", async (route) => {
    birthProfileRequests += 1;
    await route.fulfill({ status: 500, json: { code: "SHOULD_NOT_BE_CALLED" } });
  });

  await page.goto("/birth");
  await page.getByRole("textbox", { name: "Ngày" }).fill("01");
  await page.getByRole("textbox", { name: "Tháng" }).fill("01");
  await page.getByRole("textbox", { name: "Năm" }).fill("2020");
  await page.getByRole("button", { name: "Khớp tín hiệu" }).click();

  await expect(page.getByRole("alert")).toContainText("từ 18 tuổi");
  expect(birthProfileRequests).toBe(0);
});

test("guest can add exact birth time and place only after explicit deep-data consent", async ({ page }) => {
  let submittedSupplement: Record<string, unknown> | null = null;
  let auraActivated = false;
  let heldExperiment: components["schemas"]["ExperimentResponse"] | null = null;
  let chosenExperimentBody: Record<string, unknown> | null = null;
  let undoExperimentBody: Record<string, unknown> | null = null;
  const scopeKey = "c".repeat(64);
  const transitionId = "t".repeat(64);
  const vibeRevisionId = "00000000-0000-4000-8000-000000000020";
  const auraRevisionId = "00000000-0000-4000-8000-000000000021";
  const actionKey = "e".repeat(64);
  const vibeReading = {
    revision_id: vibeRevisionId,
    source: "deterministic" as const,
    mode: "vibe_fallback" as const,
    purpose: "daily_note" as const,
    tradition: "western" as const,
    precision: "unknown" as const,
    sections: {
      hook: "Đầu đã hiểu, tim chưa chắc.",
      thesis: "Một lớp đọc nhẹ từ ngày sinh.",
      manifestation: "Bạn đang cần một khoảng dừng trước khi trả lời.",
      transit: null,
      micro_action: "Chậm lại một nhịp.",
    },
    evidence: { title: "Căn cứ", claims: ["Ngày sinh đã cung cấp"], framework_disclosure: "Khung diễn giải." },
    disclaimer: "Quyền quyết định vẫn ở bạn.",
    created_at: "2026-09-06T00:00:00Z",
    experiment: null,
  };
  const auraReading = {
    revision_id: auraRevisionId,
    source: "generated" as const,
    mode: "full_synthesis" as const,
    purpose: "daily_note" as const,
    tradition: "western" as const,
    precision: "exact" as const,
    sections: {
      hook: "Bạn không cần đoán hộ một người đang im lặng.",
      thesis: "Moon, House và transit đang cùng chỉ về nhu cầu nói rõ.",
      manifestation: "Bạn có thể đang lấp khoảng trống bằng suy diễn.",
      transit: "Một transit ngắn đang làm chủ đề giao tiếp rõ hơn.",
      micro_action: "Hỏi một câu rõ ràng thay vì đoán thêm.",
    },
    evidence: { title: "Căn cứ", claims: ["Moon trong House", "Transit hiện tại"], framework_disclosure: "Khung diễn giải." },
    disclaimer: "Quyền quyết định vẫn ở bạn.",
    created_at: "2026-09-06T00:01:00Z",
    experiment: {
      action_key: actionKey,
      action: "Hỏi một câu rõ ràng thay vì đoán thêm.",
      observation: "Để ý xem câu hỏi có làm cuộc trò chuyện bớt mơ hồ không.",
      permission: "Bạn có thể bỏ qua hoặc dừng bất cứ lúc nào.",
    },
  };
  await page.route("**/v1/birth-places/search", async (route) => {
    await route.fulfill({
      status: 200,
      json: [{
        place_id: "place-hanoi",
        display_name: "Hà Nội, Việt Nam",
        country_code: "VN",
        timezone_id: "Asia/Ho_Chi_Minh",
      }],
    });
  });
  // A date-only profile: the editor answers with nothing saved yet (404 means no profile at all).
  await page.route("**/v1/birth-profile/supplement/edit", async (route) => route.fulfill({ status: 200, json: {
    birth_time_mode: "unknown", birth_time_local: null, approx_window: null, place: null,
  } }));
  await page.route("**/v1/birth-profile/supplement", async (route) => {
    if (route.request().method() === "POST") {
      submittedSupplement = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({
        status: 200,
        json: {
          profile_level: 3,
          birth_time_mode: "exact",
          birth_time_local: "08:15",
          approx_window: null,
          time_precision: "exact",
          place_display_name: "Hà Nội, Việt Nam",
          timezone_id: "Asia/Ho_Chi_Minh",
          chart_snapshot_id: "snapshot-deep",
        },
      });
      return;
    }
    await route.fulfill({ status: 404, json: { code: "BIRTH_SUPPLEMENT_NOT_FOUND" } });
  });
  await page.route("**/v1/daily-note", async (route) => {
    if (submittedSupplement === null) {
      await route.fulfill({ status: 409, json: { code: "SUPPLEMENT_REQUIRED" } });
      return;
    }
    const auraNote = {
      id: "note-aura",
      note_date: "2026-09-06",
      title: "Đầu đã hiểu, tim chưa chắc.",
      body: "Một note đã được viết lại từ toàn chart.",
      full_body: "Một note đã được viết lại từ toàn chart và transit hiện tại.",
      context_label: "Nguyên tố trội Khí · Mặt Trời Song Tử",
      content_version: "daily-note-v3",
      persona_mode: "aura",
      persona_label: "Lanh",
      persona_version: "persona-v2",
      source_level: "natal_chart",
      astrology_source_version: "2.10.03",
      fallback_used: false,
      fallback_reason: null,
      created_at: "2026-09-06T00:00:00Z",
      awakening: {
        headline: "Aura của bạn vừa thức tỉnh",
        summary: "Note giờ được đọc từ cách các hành tinh cá nhân thương lượng với nhau.",
        factors: ["Mặt Trời · Song Tử", "Mặt Trăng · Cự Giải", "Sao Kim · Sư Tử"],
        precision_label: "Chart chính xác theo giờ, nơi sinh và múi giờ đã chọn",
        scoring_version: "aura-element-modality-v1",
        confidence: "high",
      },
      sky_chapter: {
        title: "Món quà: một pattern hôm nay",
        summary: "Sao Thổ đang đối thoại với Sao Kim trong lá số gốc.",
        phase: "approaching",
        phase_label: "Đang lên",
        signal_label: "Sao Thổ x Sao Kim · đối thoại với",
        orb: 1.2,
        observed_at: "2026-09-06T12:00:00Z",
        orb_policy_version: "transit-orbs-v1",
        ranking_version: "sky-chapter-salience-v1",
        disclaimer: "Gợi ý chiêm nghiệm, không phải dự đoán định mệnh.",
      },
      reading_projection: {
        scope_key: scopeKey,
        active: auraActivated ? auraReading : vibeReading,
        available_update: auraActivated ? null : {
          revision_id: auraRevisionId,
          message: "Aura đã sẵn sàng",
          content: auraReading,
        },
        aura_transition: {
          profile_readiness: "aura_ready",
          transition_id: transitionId,
          acknowledged: auraActivated,
          unlock_layers: ["multi_factor", "house_arena", "current_sky"],
        },
      },
    } satisfies DailyNote;
    await route.fulfill({
      status: 200,
      json: auraNote,
    });
  });
  await page.route("**/v1/reading-projections/**/activate", async (route) => {
    const body = route.request().postDataJSON() as { expected_revision_id?: string };
    expect(body.expected_revision_id).toBe(auraRevisionId);
    auraActivated = true;
    await route.fulfill({
      status: 200,
      json: {
        scope_key: scopeKey,
        active: auraReading,
        available_update: null,
        aura_transition: {
          profile_readiness: "aura_ready",
          transition_id: transitionId,
          acknowledged: true,
          unlock_layers: ["multi_factor", "house_arena", "current_sky"],
        },
      },
    });
  });
  await page.route("**/v1/daily-note/note-aura/mood", async (route) => route.fulfill({ status: 200, json: null }));
  await page.route("**/v1/saved-notes", async (route) => route.fulfill({ status: 200, json: [] }));
  await page.route("**/v1/daily-note/resonance", async (route) => route.fulfill({ status: 200, json: { consented: false, feedback_count: 0, last_choice: null } }));
  await page.route("**/v1/daily-note/note-aura/experiment", async (route) => {
    chosenExperimentBody = route.request().postDataJSON() as Record<string, unknown>;
    heldExperiment = {
      id: "00000000-0000-4000-8000-000000000030",
      version: 1,
      daily_note_id: "note-aura",
      revision_id: auraRevisionId,
      state: "chosen",
      background_lens: "auto",
      action_key: actionKey,
      action: auraReading.experiment.action,
      observation: auraReading.experiment.observation,
      permission: auraReading.experiment.permission,
      outcome: null,
      created_at: "2026-09-06T00:02:00Z",
      updated_at: "2026-09-06T00:02:00Z",
      expires_at: "2026-10-06T00:02:00Z",
      reflected_at: null,
    };
    await route.fulfill({ status: 200, json: heldExperiment });
  });
  await page.route("**/v1/daily-note/experiment", async (route) => {
    if (route.request().method() === "DELETE") {
      undoExperimentBody = route.request().postDataJSON() as Record<string, unknown>;
      heldExperiment = null;
      await route.fulfill({ status: 204 });
      return;
    }
    await route.fulfill({ status: 200, json: heldExperiment });
  });

  await page.route("**/v1/session", async (route) => route.fulfill({ status: 200, json: {
    state: "active", onboarding_status: "completed", expires_at: "2026-09-30T00:00:00Z", resumed: true, session_epoch: "epoch-test",
  } }));
  await page.goto("/birth-time");
  await page.getByRole("button", { name: "Thêm để mở lớp mới" }).click();
  await page.getByRole("combobox", { name: "Giờ (0–23)" }).selectOption("08");
  await page.getByRole("combobox", { name: "Phút (0–59)" }).selectOption("15");
  await page.getByRole("button", { name: "Tiếp tục" }).click();
  await page.getByLabel("Thành phố / tỉnh").fill("Hà Nội");
  await page.getByRole("button", { name: /Hà Nội, Việt Nam/ }).click();
  await page.getByRole("button", { name: "Dùng nơi đã chọn" }).click();

  await expect(page.getByRole("button", { name: "Mở lớp Moon / House" })).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Mở lớp Moon / House" }).click();

  await expect(page).toHaveURL(/\/aura-cutover$/);
  await expect(page.getByRole("heading", { name: "Aura không tự thay Note của bạn." })).toBeFocused();
  await expect(page.getByText("Các House và lĩnh vực đời sống")).toBeVisible();
  await page.getByRole("button", { name: "Dùng Aura hôm nay" }).click();

  await expect(page).toHaveURL(/\/home$/);
  expect(auraActivated).toBe(true);
  await page.getByRole("region", { name: "Note hôm nay" }).getByRole("link", { name: "Đọc đầy đủ" }).click();
  await expect(page).toHaveURL(/\/note\/today$/);
  await page.getByRole("button", { name: "Giữ để thử hôm nay" }).click();
  await expect(page.getByRole("button", { name: "Bỏ giữ việc này" })).toBeVisible();
  expect(chosenExperimentBody).toMatchObject({
    revision_id: auraRevisionId,
    background_lens: "auto",
    action_key: actionKey,
    consent_version: "action-experiment-v1",
  });

  await page.getByRole("button", { name: "Bỏ giữ việc này" }).click();
  await expect(page.getByRole("button", { name: "Giữ để thử hôm nay" })).toBeVisible();
  expect(undoExperimentBody).toMatchObject({
    experiment_id: "00000000-0000-4000-8000-000000000030",
    expected_version: 1,
  });
  expect(submittedSupplement).toMatchObject({
    birth_time_mode: "exact",
    birth_time_local: "08:15",
    place_id: "place-hanoi",
    consent_version: "birth-profile-deep-v1",
  });
});
