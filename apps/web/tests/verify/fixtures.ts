import type { Page, Route } from "@playwright/test";

// Fake API answers for the verification run (scripts/verify/verify.mjs).
// Same data and approach as tests/screens/key-screens.spec.ts: every /v1 call is answered by
// page.route with synthetic data. The birth date is the e2e suite's synthetic fixture; no real
// person's data, token or secret is used anywhere here.

export type FixtureName =
  | "guest"
  | "birth-pending"
  | "signed-in"
  | "signed-in-deep"
  | "insights-error"
  | "radar-result"
  | "radar-public-invite";

type Flags = {
  onboarding: "none" | "birth_pending" | "completed";
  deepData: boolean;
  ownerClaim: "ok" | "needs_chart";
  insightsError?: boolean;
  radarResult?: boolean;
  publicInvite?: boolean;
};

const FIXTURES: Record<FixtureName, Flags> = {
  guest: { onboarding: "none", deepData: false, ownerClaim: "needs_chart" },
  "birth-pending": { onboarding: "birth_pending", deepData: false, ownerClaim: "needs_chart" },
  "signed-in": { onboarding: "completed", deepData: false, ownerClaim: "needs_chart" },
  "signed-in-deep": { onboarding: "completed", deepData: true, ownerClaim: "ok" },
  "insights-error": { onboarding: "completed", deepData: true, ownerClaim: "ok", insightsError: true },
  "radar-result": { onboarding: "completed", deepData: true, ownerClaim: "ok", radarResult: true },
  "radar-public-invite": { onboarding: "none", deepData: false, ownerClaim: "needs_chart", publicInvite: true },
};

export const FIXTURE_NAMES = Object.keys(FIXTURES) as FixtureName[];

export const IDS = {
  revision: "00000000-0000-4000-8000-000000000010",
  note: "note-test",
  radarRequest: "00000000-0000-4000-8000-000000000020",
  shareToken: "share-token-test",
  inviteToken: "invite-token-test",
  tarotSession: "00000000-0000-4000-8000-000000000030",
} as const;

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
  id: IDS.note, note_date: "2026-09-02", title: "Đừng biến mình thành deadline.",
  body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.", full_body: "Bạn được phép nghỉ trước khi mọi thứ hoàn hảo.",
  context_label: "Bản cũ", content_version: "daily-note-v1", persona_mode: "vibe", persona_label: "Mềm",
  persona_version: "persona-v1", source_level: "date_only", astrology_source_version: "2.10.03",
  fallback_used: false, fallback_reason: null, awakening: null, sky_chapter: null,
  created_at: "2026-09-02T00:00:00Z",
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    active: {
      revision_id: IDS.revision, source: "deterministic",
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

export const insightsReady = {
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
      revision_id: IDS.revision, source: "deterministic",
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

const safeSnapshot = {
  title: "Đừng biến mình thành deadline.", body: "Ngoài đời có thể trông như việc bạn cố thêm một chút dù đã mệt.",
  context_label: "Vibe · một lớp", content_version: "daily-note-v1", persona_mode: "vibe",
  persona_label: "Mềm", persona_version: "persona-v1", watermark: "Lá Lành",
};

const shareArtifact = {
  id: "share-test", daily_note_id: IDS.note, format: "story_9_16", safe_snapshot: safeSnapshot,
  token: IDS.shareToken, public_path: `/share/${IDS.shareToken}`,
  created_at: "2026-09-02T00:00:00Z", expires_at: "2026-09-16T00:00:00Z", revision_id: IDS.revision,
};

const radarResult = {
  request_id: IDS.radarRequest,
  mode: "private_check",
  version: "radar-result-v1",
  headline: "Hai bạn bắt sóng theo hai nhịp khác nhau.",
  summary: "Có lực hút và cũng có điểm cần nói rõ.",
  dimensions: [{
    key: "communication", label: "Giao tiếp", signal: "Có tín hiệu",
    body: "Hỏi thẳng sẽ dễ hiểu nhau hơn đoán ý.", evidence_ids: ["evidence-1"],
  }],
  strongest_contacts: [],
  disclaimer: "Dùng để soi lại trải nghiệm thật, không thay cho quyết định của bạn.",
};

const accountStatus = {
  account_inactivity_days: 365, daily_note_hours: 24, google_login_enabled: false, guest_inactivity_days: 30,
  history_days: 30, login_enabled: false, masked_email: null, profile_expires_at: null, signed_in: false,
};

function session(onboarding: "birth_pending" | "completed") {
  return { state: "active", onboarding_status: onboarding, expires_at: "2026-12-30T00:00:00Z", resumed: true, session_epoch: "epoch-test" };
}

type Reply = { status: number; json?: unknown; headers?: Record<string, string> };

function answer(flags: Flags, method: string, path: string): Reply | null {
  const signedIn = flags.onboarding !== "none";
  const sessionReply: Reply = signedIn
    ? { status: 200, json: session(flags.onboarding as "completed") }
    : { status: 401, json: { code: "GUEST_SESSION_MISSING" } };
  const key = `${method} ${path}`;
  switch (key) {
    case "GET /v1/session":
    case "POST /v1/session/renew":
    case "GET /v1/session/onboarding-status":
    case "POST /v1/session/onboarding-status":
    case "PUT /v1/session/onboarding-status":
    case "PATCH /v1/session/onboarding-status":
      return sessionReply;
    case "POST /v1/guest-sessions":
      return {
        status: 201, headers: { "set-cookie": "la_lanh_csrf=csrf-test; Path=/; SameSite=Lax" },
        json: { ...session("birth_pending"), csrf_token: "csrf-test", resumed: false },
      };
    case "POST /v1/session/birth-profile-consent":
      return { status: 204 };
    case "GET /v1/account":
      return { status: 200, json: accountStatus };
    case "GET /v1/session/history-retention":
      return { status: 200, json: { activated_at: null, daily_note_hours: 24, enabled: false, history_days: 30, saved_notes_kept: true } };
    case "GET /v1/session/content-rewrite-consent":
      return { status: 200, json: { consented: false, enabled: false, pilot_eligible: false } };
    case "GET /v1/birth-profile":
      return flags.onboarding === "completed" ? { status: 200, json: reveal } : { status: 404, json: { code: "BIRTH_PROFILE_NOT_FOUND" } };
    case "GET /v1/birth-profile/supplement":
      return flags.deepData
        ? { status: 200, json: { profile_id: "profile-test", profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: null, timezone_id: null, approx_window: null } }
        : { status: 200, json: { profile_id: "profile-test", profile_level: 1, birth_time_mode: "unknown", time_precision: "unknown", place_display_name: null, timezone_id: null, approx_window: null } };
    case "GET /v1/daily-note":
      return { status: 200, json: dailyNote };
    case `GET /v1/daily-note/${IDS.note}/mood`:
      return { status: 200, json: null };
    case "GET /v1/daily-note/resonance":
      return { status: 200, json: { consented: false, feedback_count: 0, last_choice: null } };
    case "GET /v1/daily-note/experiment":
      return { status: 200, json: null };
    case "GET /v1/saved-notes":
      return { status: 200, json: [savedNote] };
    case "GET /v1/share-artifacts":
      return { status: 200, json: { items: [], next_cursor: null } };
    case `POST /v1/daily-note/${IDS.note}/share-artifacts`:
      return { status: 200, json: shareArtifact };
    case `GET /v1/share-artifacts/${IDS.shareToken}`:
      return { status: 200, json: { expires_at: "2026-12-16T00:00:00Z", format: "story_9_16", safe_snapshot: safeSnapshot } };
    case "GET /v1/insights/overview":
      if (flags.insightsError) {
        return { status: 422, json: { type: "about:blank", title: "Unprocessable", status: 422, code: "READING_CONTENT_REJECTED", detail: "Insight reading is temporarily unavailable" } };
      }
      return { status: 200, json: flags.deepData ? insightsReady : insightsLocked };
    case "GET /v1/insights/current-sky":
      return { status: 200, json: {
        observed_at: "2026-09-28T00:00:00Z", tradition: "western", config_hash: "sky-test",
        bodies: [{ body: "sun", sign: "libra", longitude: 185, degree_in_sign: 5, retrograde: false }],
        note: "Ảnh chụp bầu trời, không phải lời phán.",
      } };
    case "POST /v1/identity/claim":
      return flags.ownerClaim === "ok"
        ? { status: 200, json: { expires_at: "2026-12-30T00:00:00Z", principal_id: "00000000-0000-4000-8000-000000000001", resumed: true } }
        : { status: 401, json: { code: "OWNER_CHART_REQUIRED" } };
    case "GET /v1/radar/requests":
      return { status: 200, json: flags.radarResult ? [{
        id: IDS.radarRequest, recipient_label: "Bạn A", context: "friend", voice: "straight_warm", mode: "private_check",
        status: "completed", created_at: "2026-10-20T03:00:00Z", expires_at: "2026-11-19T03:00:00Z", share_url: null,
      }] : [] };
    case "GET /v1/radar/received":
      return { status: 200, json: { items: flags.radarResult ? [{
        request_id: IDS.radarRequest, context: "friend", voice: "straight_warm", completed_at: "2026-10-20T03:00:00Z", expires_at: "2026-11-19T03:00:00Z",
      }] : [], next_before: null } };
    case `GET /v1/radar/results/${IDS.radarRequest}`:
    case `GET /v1/radar/received/${IDS.radarRequest}`:
      return flags.radarResult ? { status: 200, json: radarResult } : { status: 404, json: { code: "RADAR_RESULT_NOT_FOUND" } };
    case "GET /v1/public/radar/receipt":
      return flags.radarResult ? { status: 200, json: { ...radarResult, mode: "consented_invite" } } : { status: 404, json: { code: "RADAR_RESULT_NOT_FOUND" } };
    case `GET /v1/public/radar/${IDS.inviteToken}`:
    case "GET /v1/public/radar/current":
      return flags.publicInvite
        ? { status: 200, json: { request_id: IDS.radarRequest, context: "friend", voice: "straight_warm", expires_at: "2026-11-19T03:00:00Z", consent_version: "radar-pair-v1",
          requires_exact_birth_profile: false, privacy_note: "Bản thử: chỉ dùng dữ liệu giả." } }
        : { status: 404, json: { code: "RADAR_INVITE_NOT_FOUND" } };
    case "GET /v1/birth-places/search":
      return { status: 200, json: [] };
    case "GET /v1/birth-profile/supplement/edit":
      return { status: 200, json: { approx_window: null, birth_time_local: null, birth_time_mode: "unknown", place: null } };
    case "GET /v1/la-chung/requests":
      return { status: 200, json: [] };
    case `GET /v1/la-chung/results/${IDS.radarRequest}`:
      return { status: 404, json: { code: "LA_CHUNG_RESULT_NOT_FOUND" } };
    case `GET /v1/tarot/sessions/${IDS.tarotSession}`:
      return { status: 404, json: { code: "TAROT_SESSION_NOT_FOUND" } };
    default:
      return null;
  }
}

export type MockLog = { unmocked: string[]; expectedErrors: string[] };

/**
 * Answers every /v1 call. Calls with no fake answer get 503 and are listed, so a screen that
 * starts calling a new endpoint shows up in the report instead of silently half-rendering.
 */
export async function mockApi(page: Page, fixture: FixtureName): Promise<MockLog> {
  if (!FIXTURES[fixture]) throw new Error(`Unknown fixture "${fixture}". Known: ${FIXTURE_NAMES.join(", ")}`);
  // A copy per page: accepting consent on Welcome creates a guest session, so later calls in the
  // same walk see birth_pending (like the real API) instead of 401.
  const flags: Flags = { ...FIXTURES[fixture] };
  const log: MockLog = { unmocked: [], expectedErrors: [] };
  await page.route("**/v1/**", async (route: Route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const reply = answer(flags, request.method(), path);
    if (reply === null) {
      log.unmocked.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 503, json: { code: "VERIFY_UNMOCKED", path } });
      return;
    }
    if (request.method() === "POST" && path === "/v1/guest-sessions" && flags.onboarding === "none") flags.onboarding = "birth_pending";
    if (reply.status >= 400) log.expectedErrors.push(`${request.method()} ${path} ${reply.status}`);
    await route.fulfill(reply.status === 204 ? { status: 204, headers: reply.headers } : { status: reply.status, json: reply.json, headers: reply.headers });
  });
  return log;
}
