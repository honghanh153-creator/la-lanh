import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  CANARY, NOT_CHECKED, REQUIRED_SENDS, SAFETY_TEXT, SURFACES, TAROT_QUESTION,
  buildMarks, findMarks, isLocalUrl, maskTimestamps, missingSends, reportLines, scanSurfaces, sendsIn,
} from "./leak-canary-lib.mjs";

const marks = buildMarks({ placeId: "vn-quang-ngai", secrets: ["s3cr3t-session-value-0123456789", "short"] });
const clean = () => Object.fromEntries(SURFACES.map((name) => [name, []]));

test("a clean run has no findings", () => {
  const surfaces = clean();
  surfaces["server-log"].push("INFO:     Application startup complete.", "INFO:     Uvicorn running on http://127.0.0.1:18010");
  surfaces["request-url"].push("http://127.0.0.1:5180/v1/daily-note", "http://127.0.0.1:5180/insights/overview?tradition=western");
  surfaces["browser-history"].push("http://127.0.0.1:5180/tarot/3f2c9d1e-aaaa-4bbb-8ccc-0123456789ab");
  assert.deepEqual(scanSurfaces(surfaces, marks), []);
});

// AC2: a mark in any searched surface turns the run red. One case per surface and per spelling.
const LEAKS = [
  ["server-log", "birth-date", "WARNING app.birth: could not save 1994-02-13"],
  ["server-log", "birth-date", "date 13/02/1994 rejected"],
  ["server-log", "birth-date", "date 13/2/1994 rejected"],
  ["server-log", "birth-time", "ERROR chart failed for local time 03:47"],
  ["server-log", "birthplace", "geo lookup for Quảng Ngãi failed"],
  ["server-log", "birthplace", "geo lookup for quang ngai failed"],
  ["server-log", "birthplace", "place vn-quang-ngai has no offset"],
  ["server-log", "mood", "mood Đuối saved"],
  ["server-log", "tarot-question", `question was: ${TAROT_QUESTION}`],
  ["server-log", "safety-text", `crisis guard matched: ${SAFETY_TEXT}`],
  ["server-log", "session-secret", "cookie la_lanh_guest=s3cr3t-session-value-0123456789"],
  ["request-url", "birth-date", "http://127.0.0.1:5180/v1/birth-profile?birth_date=1994-02-13"],
  ["request-url", "birth-time", "http://127.0.0.1:5180/v1/chart?time=03%3A47"],
  ["request-url", "birthplace", "http://127.0.0.1:5180/v1/birth-places?query=Qu%E1%BA%A3ng%20Ng%C3%A3i"],
  ["request-url", "birthplace", "http://127.0.0.1:5180/v1/birth-places?query=Quang+Ngai"],
  ["request-url", "mood", "http://127.0.0.1:5180/v1/mood?value=%C4%90u%E1%BB%91i"],
  ["request-url", "tarot-question", "http://127.0.0.1:5180/tarot?q=zqcanary690tarot"],
  ["request-url", "tarot-question", "http://127.0.0.1:5180/go?next=%2Ftarot%3Fq%3Dzqcanary690tarot"],
  ["request-url", "tarot-question", "http://127.0.0.1:5180/go?next=%252Ftarot%253Fq%253DZQCANARY690TAROT"],
  ["request-referer", "tarot-question", "http://127.0.0.1:5180/tarot?q=zqcanary690tarot"],
  ["error-report", "safety-text", "Unhandled rejection: zqcanary690safety"],
  ["error-response", "safety-text", "{\"detail\":\"bad question zqcanary690safety\"}"],
  ["browser-history", "birth-date", "http://127.0.0.1:5180/birth?d=13-02-1994"],
  ["current-url", "session-secret", "http://127.0.0.1:5180/home#t=S3CR3T-session-value-0123456789"],
  ["web-storage", "tarot-question", "sessionStorage tarot-draft {\"question\":\"zqcanary690tarot\"}"],
  ["web-storage", "birth-date", "localStorage profile {\"birth_date\":\"1994-02-13\"}"],
];

for (const [surface, kind, text] of LEAKS) {
  test(`${kind} in ${surface} is found: ${text.slice(0, 40)}`, () => {
    const surfaces = clean();
    surfaces[surface].push(text);
    const findings = scanSurfaces(surfaces, marks);
    assert.ok(findings.some((finding) => finding.surface === surface && finding.kind === kind), JSON.stringify(findings));
  });
}

test("a request that leaves the app is a finding even without a mark", () => {
  const surfaces = clean();
  surfaces["external-request"].push("https://fonts.example/css");
  assert.deepEqual(scanSurfaces(surfaces, marks), [{ surface: "external-request", kind: "request-left-the-app", index: 0 }]);
});

test("the birth time is not confused with the clock time of a log line (#457)", () => {
  assert.deepEqual(findMarks("2026-11-19 03:47:12,512 INFO started", marks), []);
  assert.deepEqual(findMarks("2026-11-19T03:47:12.512+07:00 INFO started", marks), []);
  assert.deepEqual(findMarks("[03:47:59] INFO started", marks), []);
  assert.deepEqual(findMarks("2026-11-19 03:47:12 chart failed for 03:47", marks), ["birth-time"]);
  assert.equal(maskTimestamps("at 2026-11-19 03:47"), "at <timestamp>");
});

test("short secrets are not searched for; every mark is searched in lower case", () => {
  assert.ok(!marks.some((mark) => mark.forms.includes("short")));
  assert.deepEqual(findMarks("QUẢNG NGÃI", marks), ["birthplace"]);
});

test("a finding never carries the value that was found", () => {
  const surfaces = clean();
  surfaces["server-log"].push(`question was: ${TAROT_QUESTION} from 1994-02-13`);
  const findings = scanSurfaces(surfaces, marks);
  const lines = reportLines({ surfaces, findings, missing: [] }).join("\n");
  assert.ok(!lines.includes("1994"));
  assert.ok(!lines.includes(CANARY.tarotMark));
  assert.match(lines, /ĐỎ\s+nhật ký máy chủ: 1 mục, thấy dấu: birth-date, tarot-question/);
  assert.match(lines, /Kết quả: ĐỎ/);
});

test("requests inside the app are local; everything else left it", () => {
  const origin = "http://127.0.0.1:5180";
  assert.equal(isLocalUrl("http://127.0.0.1:5180/v1/daily-note", origin), true);
  assert.equal(isLocalUrl("data:image/png;base64,AAAA", origin), true);
  assert.equal(isLocalUrl("http://127.0.0.1:8010/v1/daily-note", origin), false);
  assert.equal(isLocalUrl("https://example.com/", origin), false);
  assert.equal(isLocalUrl("not a url", origin), false);
});

test("coverage: the bodies that carry each mark are recognised, GET and other paths are not", () => {
  assert.deepEqual(sendsIn("POST", "/v1/birth-profile", "{\"birth_date\":\"1994-02-13\"}"), ["birth-date"]);
  assert.deepEqual(sendsIn("POST", "/v1/birth-profile/supplement", "{\"birth_time_mode\":\"exact\",\"birth_time_local\":\"03:47\",\"place_id\":\"vn-quang-ngai\"}"), ["birth-time"]);
  assert.deepEqual(sendsIn("POST", "/v1/birth-places/search", "{\"query\":\"Quảng Ngãi\"}"), ["birthplace"]);
  assert.deepEqual(sendsIn("PUT", "/v1/daily-note/abc/mood", "{\"mood\":\"Đuối\"}"), ["mood"]);
  assert.deepEqual(sendsIn("POST", "/v1/tarot/sessions", JSON.stringify({ question: TAROT_QUESTION })), ["tarot-question"]);
  assert.deepEqual(sendsIn("POST", "/v1/tarot/sessions", JSON.stringify({ question: SAFETY_TEXT })), ["safety-text"]);
  assert.deepEqual(sendsIn("GET", "/v1/daily-note/abc/mood", "{\"mood\":\"Đuối\"}"), []);
  assert.deepEqual(sendsIn("PUT", "/v1/other", "{\"mood\":\"Đuối\"}"), []);
  assert.deepEqual(sendsIn("POST", "/v1/x", "{\"created_at\":\"2026-11-19T03:47:00Z\"}"), []);
});

test("a run that did not send every mark is red, and the report says which", () => {
  assert.deepEqual(missingSends(new Set(REQUIRED_SENDS)), []);
  const missing = missingSends(new Set(REQUIRED_SENDS.filter((kind) => kind !== "mood")));
  assert.deepEqual(missing, ["mood"]);
  const lines = reportLines({ surfaces: clean(), findings: [], missing }).join("\n");
  assert.match(lines, /chưa gửi dấu "mood"/);
  assert.match(lines, /Kết quả: ĐỎ/);
});

test("AC3: cases the app cannot exercise are printed as not checked, never as passed", () => {
  const lines = reportLines({ surfaces: clean(), findings: [], missing: [] });
  for (const [name] of NOT_CHECKED) {
    const line = lines.find((entry) => entry.includes(name));
    assert.ok(line?.startsWith("chưa kiểm"), name);
  }
  assert.ok(NOT_CHECKED.some(([name]) => name === "Che nhanh"));
  assert.ok(NOT_CHECKED.some(([name]) => name === "Màn tự che khi chuyền máy"));
  assert.match(lines.at(-1), /không tính là đạt/);
});

test("the check runs in the author check and its runbook exists", () => {
  const scripts = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")).scripts;
  assert.equal(scripts["verify:leak"], "node scripts/leak-canary.mjs");
  assert.match(scripts["qa:test"], /pnpm qa:build && .*node scripts\/leak-canary\.mjs/);
  assert.match(scripts["collab:test"], /scripts\/leak-canary-lib\.test\.mjs/);
  assert.match(scripts.check, /pnpm qa:test/);
  const runbook = readFileSync(new URL("../docs/operations/leak-canary-runbook.md", import.meta.url), "utf8");
  assert.match(runbook, /pnpm verify:leak/);
  assert.match(runbook, /--plant/);
});
