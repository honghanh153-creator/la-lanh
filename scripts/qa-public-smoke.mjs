import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";

// Use a fresh cookie jar and synthetic records only; never attach a real session.
const origin = new URL(process.argv[2] ?? "").origin;
assert.equal(process.env.LA_LANH_SMOKE_WRITE_CONSENT, "synthetic-only",
  "Set LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only to create and delete QA-only data.");
assert.ok(origin.startsWith("https://") || origin.startsWith("http://127.0.0.1:"));
const cookies = new Map();
let csrf = "";
let createdGuest = false;
const completed = [];

async function request(path, { method = "GET", body, expected = 200, anonymous = false } = {}) {
  const response = await fetch(`${origin}${path}`, {
    method,
    headers: {
      origin,
      "content-type": "application/json",
      ...(!anonymous ? {
        cookie: [...cookies].map(([name, value]) => `${name}=${value}`).join("; "),
        "x-csrf-token": csrf,
      } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(60_000),
  });
  for (const value of response.headers.getSetCookie()) {
    const pair = value.split(";", 1)[0];
    const split = pair.indexOf("=");
    cookies.set(pair.slice(0, split), pair.slice(split + 1));
  }
  // Never print response bodies, credentials, private IDs or capability URLs.
  assert.equal(response.status, expected, `Unexpected HTTP status for ${method} API operation`);
  const content = await response.text();
  const data = content ? JSON.parse(content) : null;
  return { data, response };
}

try {
  await request("/v1/ready");
  const { data: guest } = await request("/v1/guest-sessions", {
    method: "POST", body: {
      consent_version: "birth-profile-v1", purpose: "birth_profile_basic",
      idempotency_key: `release-qa-${randomUUID()}`,
    },
  });
  csrf = guest.csrf_token;
  createdGuest = true;
  const { data: birth } = await request("/v1/birth-profile", {
    method: "POST", body: { birth_date: "1990-03-15" },
  });
  assert.equal(birth.calculation_kind, "date_only_sun");
  const { data: basic } = await request("/v1/daily-note");
  assert.ok(basic.reading_projection.active.sections.hook);
  completed.push("guest → date-only birth → daily note");

  const { data: work } = await request("/v1/daily-note/context", {
    method: "POST", body: { background_lens: "work" },
  });
  assert.notEqual(work.scope_key, basic.reading_projection.scope_key);
  const { data: share } = await request(`/v1/daily-note/${basic.id}/share-artifacts`, {
    method: "POST", body: { revision_id: work.active.revision_id, background_lens: "work" },
  });
  const { data: preview, response: previewResponse } = await request(
    `/v1/share-artifacts/${share.token}`, { anonymous: true },
  );
  assert.equal(preview.safe_snapshot.title, work.active.sections.hook);
  assert.equal(previewResponse.headers.get("referrer-policy"), "no-referrer");
  assert.ok(!JSON.stringify(preview).includes("1990-03-15"));
  await request(`/v1/share-artifacts/${share.id}`, { method: "DELETE", expected: 204 });
  await request(`/v1/share-artifacts/${share.token}`, { anonymous: true, expected: 404 });
  completed.push("work context → safe share → revoke");

  const { data: supplement } = await request("/v1/birth-profile/supplement", {
    method: "POST", body: {
      birth_time_mode: "exact", birth_time_local: "08:15", place_id: "vn-hanoi",
      consent_version: "birth-profile-deep-v1",
    },
  });
  assert.equal(supplement.profile_level, 3);
  const { data: full } = await request("/v1/daily-note");
  assert.equal(full.persona_mode, "aura");
  if (full.reading_projection.available_update) {
    const { data: activated } = await request(
      `/v1/reading-projections/${full.reading_projection.scope_key}/activate`, {
        method: "PUT", body: {
          expected_revision_id: full.reading_projection.available_update.revision_id,
        },
      },
    );
    assert.equal(activated.active.mode, "full_synthesis");
  }
  await request("/v1/insights/overview?tradition=western");
  await request("/v1/insights/overview?tradition=jyotish");
  await request("/v1/insights/readings/aura?tradition=western");
  await request("/v1/insights/current-sky?tradition=western");
  completed.push("optional exact-time chart → Aura activation → Western/Jyotish/Natal/Sky");

  for (const [spread, count] of [["one_card", 1], ["three_card", 3], ["five_card", 5]]) {
    let { data: tarot } = await request("/v1/tarot/sessions", {
      method: "POST", expected: 201, body: {
        context: "work", question: "Mình nên chia việc nhóm thế nào cho rõ hơn?",
        spread, origin: "direct", idempotency_key: `release-qa-${randomUUID()}`,
      },
    });
    for (let index = 0; index < count; index += 1) {
      ({ data: tarot } = await request(`/v1/tarot/sessions/${tarot.id}/selections`, {
        method: "PUT", body: { fan_index: index, expected_version: tarot.version },
      }));
    }
    assert.equal(tarot.state, "complete");
    assert.equal(tarot.reading.positions.length, count);
    await request(`/v1/tarot/sessions/${tarot.id}`, { anonymous: true, expected: 401 });
    await request(`/v1/tarot/sessions/${tarot.id}`, { method: "DELETE", expected: 204 });
    completed.push(`Tarot ${count} cards → private result → QA cleanup`);
  }

  await request("/v1/identity/claim", { method: "POST" });
  for (const mode of ["exact", "unknown"]) {
    const { data: radar } = await request("/v1/radar/private-checks", {
      method: "POST", body: {
        recipient_label: "QA tổng hợp", context: "friend", voice: "straight_warm",
        birth_date: "1996-07-21", birth_time_mode: mode,
        ...(mode === "exact" ? { birth_time_local: "19:40" } : {}),
        place_id: "vn-dak-lak", consent_version: "radar-authorized-input-v1",
        authorization_attested: true,
      },
    });
    assert.equal(radar.mode, "private_check");
    assert.equal(radar.sections.length, 4);
    assert.ok(!JSON.stringify(radar).includes("1996-07-21"));
    await request(`/v1/radar/results/${radar.request_id}`, { anonymous: true, expected: 404 });
    await request(`/v1/radar/results/${radar.request_id}`, { method: "DELETE", expected: 204 });
    completed.push(`Radar ${mode} birth time → private report → QA cleanup`);
  }
} finally {
  if (createdGuest) {
    await request("/v1/guest-session", { method: "DELETE", expected: 204 });
    completed.push("QA guest and associated data deleted");
  }
  console.log(JSON.stringify({ checks: completed }, null, 2));
}
