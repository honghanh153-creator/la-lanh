import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { deflateSync } from "node:zlib";

import {
  CANARY, NOT_CHECKED, REQUIRED_FILES, REQUIRED_SENDS, SAFETY_TEXT, SURFACES, TAROT_QUESTION,
  buildMarks, canaryServerEnv, dumpWebStorage, findMarks, isLocalUrl, maskLogTime, missingFiles, missingSends, pngMetadata,
  reportLines, scanSurfaces, sendsIn, svgTextOf,
} from "./leak-canary-lib.mjs";
import { prepareQaDatabase } from "./qa-server.mjs";

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
  const inLog = (line) => findMarks(line, marks, { logLine: true });
  assert.deepEqual(inLog("2026-11-19 03:47:12,512 INFO started"), []);
  assert.deepEqual(inLog("2026-11-19T03:47:12.512+07:00 INFO started"), []);
  assert.deepEqual(inLog("[03:47:59] INFO started"), []);
  assert.deepEqual(inLog("2026-11-19 03:47:12 chart failed for 03:47"), ["birth-time"]);
  assert.equal(maskLogTime("2026-11-19 03:47 INFO started"), "<log-time> INFO started");
});

// Codex #753 r2: a leading clock value is log metadata only when a log level follows it. A line
// that simply starts with the submitted birth time is a leak.
test("a log line that starts with the birth time itself is a finding", () => {
  const inLog = (line) => findMarks(line, marks, { logLine: true });
  assert.deepEqual(inLog("03:47:00 is the submitted birth time"), ["birth-time"]);
  assert.deepEqual(inLog("03:47:00"), ["birth-time"]);
  assert.deepEqual(inLog("[03:47:00] chart input"), ["birth-time"]);
  assert.deepEqual(inLog("  03:47:00.000 birth_time_local"), ["birth-time"]);
  assert.deepEqual(inLog("2026-11-19 03:47:00 birth time received"), ["birth-time"]);
  assert.deepEqual(inLog("2026-11-19T03:47:00Z"), ["birth-time"]);
  assert.deepEqual(inLog("03:47:00 information about the user"), ["birth-time"]);
  // Recognised logger shapes stay masked.
  assert.deepEqual(inLog("03:47:12 INFO started"), []);
  assert.deepEqual(inLog("03:47:12.512 | WARNING | slow request"), []);
  assert.deepEqual(inLog("[2026-11-19 03:47:12,512] [ERROR] failed"), []);
  assert.deepEqual(inLog("2026-11-19 03:47:12 - DEBUG - tick"), []);
  // The mask covers the timestamp only: the same value later in the line is still found.
  assert.deepEqual(inLog("03:47:12 INFO birth_time=03:47:00"), ["birth-time"]);
  const surfaces = clean();
  surfaces["server-log"].push("03:47:00 is the submitted birth time");
  assert.deepEqual(scanSurfaces(surfaces, marks).map((finding) => `${finding.surface}:${finding.kind}`), ["server-log:birth-time"]);
});

// Codex #753 r1: masking every clock value with seconds, in every surface, hid a birth time
// written with seconds. Only the time at the start of a log line is log metadata.
test("a birth time written with seconds is found in URLs, payloads, storage and inside a log line", () => {
  const found = (surface, text) => {
    const surfaces = clean();
    surfaces[surface].push(text);
    return scanSurfaces(surfaces, marks).map((finding) => `${finding.surface}:${finding.kind}`);
  };
  assert.deepEqual(found("request-url", "http://127.0.0.1:5180/v1/chart?birth_time=03%3A47%3A00"), ["request-url:birth-time"]);
  assert.deepEqual(found("request-referer", "http://127.0.0.1:5180/birth?t=03:47:00"), ["request-referer:birth-time"]);
  assert.deepEqual(found("error-response", "{\"birth_time_local\":\"03:47:00\"}"), ["error-response:birth-time"]);
  assert.deepEqual(found("web-storage", "localStorage draft {\"birth_time_local\":\"03:47:00\"}"), ["web-storage:birth-time"]);
  assert.deepEqual(found("error-report", "2026-11-19 03:47:00 is not a valid time"), ["error-report:birth-time"]);
  assert.deepEqual(found("server-log", "INFO app.birth: saved birth_time_local=03:47:00"), ["server-log:birth-time"]);
  assert.deepEqual(found("server-log", "2026-11-19 10:02:11 INFO app.birth: saved 2026-11-19T03:47:00"), ["server-log:birth-time"]);
  // Outside a server log nothing is masked, not even at the start of the text.
  assert.deepEqual(found("web-storage", "03:47:00"), ["web-storage:birth-time"]);
});

// Codex #753 r1: the collector listed cache names and URLs only. The stored answers are read too.
const fakeStore = (items) => ({
  length: Object.keys(items).length,
  key: (index) => Object.keys(items)[index],
  getItem: (key) => items[key],
});
const fakeCaches = (byName) => ({
  keys: async () => Object.keys(byName),
  open: async (name) => ({
    keys: async () => byName[name].map(([request]) => request),
    match: async (request) => byName[name].find(([kept]) => kept === request)?.[1],
  }),
});
const kept = (path, body, headers = {}) => [new Request(`http://127.0.0.1:5180${path}`), new Response(body, { headers })];

test("US-03 AC12: a mark in the body or the headers of a cached answer is a web-storage finding", async () => {
  const scan = async (entries) => {
    const surfaces = clean();
    surfaces["web-storage"] = await dumpWebStorage({
      localStorage: fakeStore({ theme: "dark" }),
      sessionStorage: fakeStore({}),
      caches: fakeCaches({ "note-v1": entries }),
      document: { title: "Lá Lành" },
    });
    return scanSurfaces(surfaces, marks).map((finding) => finding.kind);
  };
  assert.deepEqual(await scan([kept("/v1/note/today", "{\"title\":\"Hôm nay\"}")]), []);
  assert.deepEqual(await scan([kept("/v1/note/today", "{\"birth_date\":\"1994-02-13\"}")]), ["birth-date"]);
  assert.deepEqual(await scan([kept("/v1/note/today", "{}", { "x-profile-place": "vn-quang-ngai" })]), ["birthplace"]);
  assert.deepEqual(await scan([kept("/v1/note/today?q=zqcanary690tarot", "{}")]), ["tarot-question"]);
});

test("the collector reads localStorage, sessionStorage and the title, and works without Cache Storage", async () => {
  const dump = await dumpWebStorage({
    localStorage: fakeStore({ a: "1" }),
    sessionStorage: fakeStore({ b: "2" }),
    document: { title: "Lá Lành" },
  });
  assert.deepEqual(dump, ["localStorage a 1", "sessionStorage b 2", "title Lá Lành"]);
});

// Codex #753 r1: the launcher ignored LA_LANH_DATABASE_URL, so the run wrote to the launcher's
// lasting QA database, or to whatever LA_LANH_QA_DATABASE_URL the caller had set.
test("the run's database is its own scratch file, whatever the caller's environment names", () => {
  const env = canaryServerEnv({
    base: { LA_LANH_QA_DATABASE_URL: "sqlite+aiosqlite:////somewhere/else/kept.db", LA_LANH_DATABASE_URL: "postgresql://not-this", PATH: "/usr/bin" },
    databaseFile: "/tmp/scratch-1/qa.db",
    apiPort: 18_901,
    webPort: 19_401,
  });
  const chosen = prepareQaDatabase({ webPort: 19_401, env, projectRoot: "/tmp/project", tempRoot: "/tmp/never-used" });
  assert.deepEqual(chosen, { databaseUrl: "sqlite+aiosqlite:////tmp/scratch-1/qa.db", cleanup: null, storagePath: null });
  assert.equal(env.LA_LANH_QA_API_PORT, "18901");
  assert.equal(env.LA_LANH_QA_WEB_PORT, "19401");
  assert.equal(env.PATH, "/usr/bin");
});

test("both callers of the launcher pass the database under the name it reads, and wait for its output to close", () => {
  for (const file of ["leak-canary.mjs", "qa-cli-smoke.mjs"]) {
    const source = readFileSync(new URL(`./${file}`, import.meta.url), "utf8");
    assert.ok(!/\bLA_LANH_DATABASE_URL:/.test(source), `${file} sets a name the launcher overwrites`);
    assert.match(source, /drainOnStop\(/, file);
    assert.ok(!/once\("exit"/.test(source), `${file} still waits for exit only`);
  }
  assert.match(readFileSync(new URL("./qa-cli-smoke.mjs", import.meta.url), "utf8"), /LA_LANH_QA_DATABASE_URL: databaseUrl/);
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

// #691: file names, the share image and the metadata inside the PNG.
const FILE_LEAKS = [
  ["file-name", "birth-date", "la-lanh-note-1994-02-13.png"],
  ["file-name", "birth-date", "la-khai-sinh-13021994-story.png"],
  ["file-name", "birthplace", "la-lanh-quang-ngai.json"],
  ["file-name", "birthplace", "attachment; filename*=UTF-8''la-lanh-Qu%E1%BA%A3ng%20Ng%C3%A3i.json"],
  ["file-name", "session-secret", "la-lanh-s3cr3t-session-value-0123456789.json"],
  ["share-image", "birth-date", "<svg><text>Sinh ngày 13/02/1994</text></svg>"],
  ["share-image", "birth-time", "<svg><text>03:47</text></svg>"],
  ["share-image", "mood", "alt Thẻ note hôm nay, mood Đuối"],
  ["share-image", "tarot-question", "share title Lá Lành\ntext zqcanary690tarot\nurl "],
  ["image-metadata", "birthplace", "tEXt\nComment\u0000Quang Ngai"],
];

for (const [surface, kind, text] of FILE_LEAKS) {
  test(`#691 ${kind} in ${surface} is found: ${text.slice(0, 40)}`, () => {
    const surfaces = clean();
    surfaces[surface].push(text);
    const findings = scanSurfaces(surfaces, marks);
    assert.ok(findings.some((finding) => finding.surface === surface && finding.kind === kind), JSON.stringify(findings));
  });
}

test("#691 the app's own file names are clean", () => {
  const surfaces = clean();
  surfaces["file-name"].push(
    "la-lanh-note-story_9_16.png", "la-lanh-note-square_1_1.png", "la-khai-sinh-story.png", "la-khai-sinh-square.png",
    "la-lanh-du-lieu-cua-toi.json", "attachment; filename=\"la-lanh-du-lieu-cua-toi.json\"",
  );
  assert.deepEqual(scanSurfaces(surfaces, marks), []);
});

test("#691 the share image text is the SVG without font payloads, with character references read", () => {
  const payload = "QUJD".repeat(40);
  const svg = `<svg><style>@font-face{src:url(data:font/woff2;base64,${payload}duoi${payload})}</style><text>Qu&#7843;ng Ng&#xe3;i</text></svg>`;
  const text = svgTextOf(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`);
  assert.ok(!text.includes(payload), "font payload is cut out");
  assert.match(text, /data:font\/woff2;base64,<payload>/);
  assert.match(text, /Quảng Ngãi/);
  // A short mark spelled by accident inside the payload is not a finding; the place in the text is.
  assert.deepEqual(findMarks(text, marks), ["birthplace"]);
  assert.equal(svgTextOf(svg), text);
  assert.equal(svgTextOf(null), "");
});

function pngChunk(type, body = Buffer.alloc(0)) {
  const head = Buffer.alloc(8);
  head.writeUInt32BE(body.length, 0);
  head.write(type, 4, "latin1");
  return Buffer.concat([head, body, Buffer.alloc(4)]);
}
const PNG_HEAD = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const png = (...extra) => Buffer.concat([PNG_HEAD, pngChunk("IHDR", Buffer.alloc(13)), ...extra, pngChunk("IDAT", Buffer.from([1, 2, 3])), pngChunk("IEND")]);

function metadataFindings(bytes) {
  const surfaces = clean();
  const { chunks, texts } = pngMetadata(bytes);
  surfaces["image-metadata"].push(`chunks ${chunks.join(" ")}`, ...texts);
  return scanSurfaces(surfaces, marks).map((finding) => finding.kind);
}

test("#691 AC3: a PNG with only pixel chunks has no metadata text", () => {
  const plain = png(pngChunk("sRGB", Buffer.from([0])), pngChunk("pHYs", Buffer.alloc(9)));
  assert.deepEqual(pngMetadata(plain), { chunks: ["IHDR", "sRGB", "pHYs", "IDAT", "IEND"], texts: [] });
  assert.deepEqual(metadataFindings(plain), []);
});

test("#691 AC3: a mark planted in any PNG metadata chunk turns the check red", () => {
  const time = Buffer.alloc(7);
  time.writeUInt16BE(1994, 0);
  time.set([2, 13, 3, 47, 0], 2);
  const international = Buffer.concat([Buffer.from("Comment\0\x01\0\0\0", "latin1"), deflateSync(Buffer.from("câu hỏi zqcanary690tarot"))]);
  const cases = [
    ["tEXt", pngChunk("tEXt", Buffer.from("Comment\0born 1994-02-13", "latin1")), "birth-date"],
    ["tEXt in UTF-8", pngChunk("tEXt", Buffer.from("Comment\0Quảng Ngãi", "utf8")), "birthplace"],
    ["zTXt compressed", pngChunk("zTXt", Buffer.concat([Buffer.from("Comment\0\0", "latin1"), deflateSync(Buffer.from("zqcanary690safety"))])), "safety-text"],
    ["iTXt compressed", pngChunk("iTXt", international), "tarot-question"],
    ["eXIf", pngChunk("eXIf", Buffer.from("MM\0*\0\0\0\x08UserComment 13/02/1994", "latin1")), "birth-date"],
    ["tIME", pngChunk("tIME", time), "birth-date"],
    ["unknown chunk", pngChunk("prVt", Buffer.from("mood Đuối", "utf8")), "mood"],
  ];
  for (const [name, chunk, kind] of cases) assert.ok(metadataFindings(png(chunk)).includes(kind), name);
});

test("#691 a file that is not a whole PNG breaks the run instead of passing", () => {
  assert.throws(() => pngMetadata(Buffer.from("not a png at all")), /không phải file PNG/);
  assert.throws(() => pngMetadata(png().subarray(0, 40)), /bị cụt/);
});

test("#691 a run that did not take every file out of the app is red, and the report says which", () => {
  assert.deepEqual(missingFiles(new Set(REQUIRED_FILES)), []);
  const noFiles = missingFiles(new Set(REQUIRED_FILES.filter((kind) => kind !== "birth-card-png")));
  assert.deepEqual(noFiles, ["birth-card-png"]);
  const lines = reportLines({ surfaces: clean(), findings: [], missing: [], missingFiles: noFiles }).join("\n");
  assert.match(lines, /chưa lấy được "birth-card-png"/);
  assert.match(lines, /Kết quả: ĐỎ/);
  assert.match(reportLines({ surfaces: clean(), findings: [], missing: [] }).at(-1), /Kết quả: đạt/);
});

test("#691 pixels and the mobile share sheet are reported as not checked", () => {
  assert.ok(NOT_CHECKED.some(([name]) => name === "Chữ đã vẽ thành điểm ảnh trong ảnh PNG"));
  assert.ok(NOT_CHECKED.some(([name]) => name === "File và ảnh chia sẻ trong app di động"));
  assert.ok(!NOT_CHECKED.some(([, reason]) => reason.includes("#691")));
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
