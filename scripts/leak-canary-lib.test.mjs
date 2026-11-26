import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { deflateSync } from "node:zlib";

import {
  CANARY, NOT_CHECKED, PNG_ALLOWED_CHUNKS, PNG_CHUNK_NOT_ALLOWED, REQUIRED_FILES, REQUIRED_SENDS, SAFETY_TEXT, SURFACES, TAROT_QUESTION,
  buildMarks, canaryServerEnv, dumpWebStorage, findMarks, isLocalUrl, maskLogTime, missingFiles, missingSends, notAllowedPngChunks, pngMetadata,
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

const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(bytes) {
  let c = 0xffffffff;
  for (const byte of bytes) c = CRC_TABLE[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
// A chunk as a PNG reader accepts it: length, type, body and the CRC of type + body.
function pngChunk(type, body = Buffer.alloc(0)) {
  const head = Buffer.alloc(8);
  head.writeUInt32BE(body.length, 0);
  head.write(type, 4, "latin1");
  const tail = Buffer.alloc(4);
  tail.writeUInt32BE(crc32(Buffer.concat([head.subarray(4), body])), 0);
  return Buffer.concat([head, body, tail]);
}
// An EXIF block (TIFF) holding one field, in IFD0 or in the Exif sub-IFD, in either byte order.
function exifBlock({ big = false, tag, type, value, inExifIfd = false }) {
  const number = (size, n) => {
    const out = Buffer.alloc(size);
    if (size === 2) (big ? out.writeUInt16BE(n) : out.writeUInt16LE(n));
    else (big ? out.writeUInt32BE(n) : out.writeUInt32LE(n));
    return out;
  };
  const ifd = (fieldTag, fieldType, count, offset) => Buffer.concat([number(2, 1), number(2, fieldTag), number(2, fieldType), number(4, count), number(4, offset), number(4, 0)]);
  const head = Buffer.concat([Buffer.from(big ? "MM" : "II", "latin1"), number(2, 42), number(4, 8)]);
  if (!inExifIfd) return Buffer.concat([head, ifd(tag, type, value.length, 26), value]);
  return Buffer.concat([head, ifd(0x8769, 4, 1, 26), ifd(tag, type, value.length, 44), value]);
}
const utf16le = (text) => Buffer.from(text, "utf16le");
const utf16be = (text) => Buffer.from(text, "utf16le").swap16();
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
    ["eXIf ImageDescription (ASCII)", pngChunk("eXIf", exifBlock({ tag: 0x010e, type: 2, value: Buffer.from("born 13/02/1994\0", "latin1") })), "birth-date"],
    ["eXIf XPComment (UTF-16LE)", pngChunk("eXIf", exifBlock({ tag: 0x9c9c, type: 1, value: utf16le("câu hỏi zqcanary690tarot\0") })), "tarot-question"],
    ["eXIf XPComment at an odd offset", pngChunk("eXIf", exifBlock({ tag: 0x9c9c, type: 1, value: Buffer.concat([Buffer.alloc(1), utf16le("zqcanary690safety\0")]) })), "safety-text"],
    ["eXIf UserComment (UTF-16BE, Exif IFD)", pngChunk("eXIf", exifBlock({ big: true, tag: 0x9286, type: 7, inExifIfd: true, value: Buffer.concat([Buffer.from("UNICODE\0", "latin1"), utf16be("mood Đuối")]) })), "mood"],
    ["eXIf UTF-16BE at an odd offset", pngChunk("eXIf", exifBlock({ big: true, tag: 0x9c9c, type: 1, value: Buffer.concat([Buffer.alloc(1), utf16be("Quảng Ngãi")]) })), "birthplace"],
    // EXIF writes dates as "YYYY:MM:DD HH:MM:SS" (Codex #768 r2): one case per date tag.
    ["eXIf DateTime", pngChunk("eXIf", exifBlock({ tag: 0x0132, type: 2, value: Buffer.from("1994:02:13 00:00:00\0", "latin1") })), "birth-date"],
    ["eXIf DateTimeOriginal (Exif IFD)", pngChunk("eXIf", exifBlock({ tag: 0x9003, type: 2, inExifIfd: true, value: Buffer.from("1994:02:13 00:00:00\0", "latin1") })), "birth-date"],
    ["eXIf DateTimeDigitized (Exif IFD, big-endian)", pngChunk("eXIf", exifBlock({ big: true, tag: 0x9004, type: 2, inExifIfd: true, value: Buffer.from("1994:02:13 00:00:00\0", "latin1") })), "birth-date"],
    ["eXIf GPSDateStamp", pngChunk("eXIf", exifBlock({ tag: 0x001d, type: 2, value: Buffer.from("1994:02:13\0", "latin1") })), "birth-date"],
    ["tEXt Creation Time (RFC 1123)", pngChunk("tEXt", Buffer.from("Creation Time\0Sun, 13 Feb 1994 00:00:00 GMT", "latin1")), "birth-date"],
    ["iTXt XMP date", pngChunk("iTXt", Buffer.from("XML:com.adobe.xmp\0\0\0\0\0<xmp:CreateDate>1994-02-13T00:00:00</xmp:CreateDate>", "utf8")), "birth-date"],
    ["sPLT palette name",pngChunk("sPLT", Buffer.concat([Buffer.from("born 1994-02-13\0\x08", "latin1"), Buffer.alloc(6)])), "birth-date"],
    ["tIME", pngChunk("tIME", time), "birth-date"],
    ["unknown chunk", pngChunk("prVt", Buffer.from("mood Đuối", "utf8")), "mood"],
  ];
  for (const [name, chunk, kind] of cases) assert.ok(metadataFindings(png(chunk)).includes(kind), name);
});

// The birth date in every way a file, a header or a log can write it: any one separator between
// the parts, the three part orders, with or without leading zeros, and with the month as a word.
test("#691 AC3: the birth date is found in every date spelling, not only the ones the app writes", () => {
  const spellings = [
    "1994:02:13 00:00:00", "1994:02:13", "1994 02 13", "1994_02_13", "1994.2.13", "1994\\02\\13",
    "13 02 1994", "13_02_1994", "13:02:1994", "13.2.1994", "13-2-1994",
    "02/13/1994", "2/13/1994", "02-13-1994",
    "13 Feb 1994", "13-Feb-1994", "13 February 1994", "Feb 13, 1994", "February 13th, 1994", "1994 Feb 13",
    "13 tháng 2 năm 1994", "13 tháng 02, 1994", "13 thg 2, 1994", "ngay 13 thang 2 nam 1994",
  ];
  for (const text of spellings) assert.deepEqual(findMarks(`taken ${text} end`, marks), ["birth-date"], text);
});

test("#691 AC3: another date, or the same digits inside a longer number, is not the birth date", () => {
  const others = [
    "1994:02:14 00:00:00", "1994:12:13", "1993:02:13", "13 Mar 1994", "Feb 13, 1995", "14 tháng 2 năm 1994",
    "13 tháng 12 năm 1994", "v1994.2.130", "21994:02:13x", "id 213 1994 7", "2026:11:21 03:46:59",
  ];
  for (const text of others) assert.deepEqual(findMarks(`taken ${text} end`, marks), [], text);
});

// S57: searching for marks finds only what the marks describe. A chunk outside the allowed list
// is red on its own, so a new way of writing data into the image cannot pass unseen.
test("#691 AC3 (S57): a chunk outside the allowed list is red even with no mark in it", () => {
  const cases = [
    ["text", pngChunk("tEXt", Buffer.from("Software\0canvas", "latin1"))],
    ["EXIF", pngChunk("eXIf", exifBlock({ tag: 0x0131, type: 2, value: Buffer.from("canvas export\0", "latin1") }))],
    ["palette name", pngChunk("sPLT", Buffer.concat([Buffer.from("web safe\0\x08", "latin1"), Buffer.alloc(6)]))],
    ["colour profile", pngChunk("iCCP", Buffer.from("sRGB\0\0", "latin1"))],
    ["time", pngChunk("tIME", Buffer.from([0x07, 0xea, 11, 24, 9, 30, 0]))],
    ["private chunk", pngChunk("prVt", Buffer.from([1, 2, 3]))],
    ["newer public chunk", pngChunk("cICP", Buffer.from([1, 13, 0, 1]))],
  ];
  for (const [name, chunk] of cases) assert.deepEqual(metadataFindings(png(chunk)), [PNG_CHUNK_NOT_ALLOWED], name);
  // Every allowed chunk together stays clean.
  const allowed = PNG_ALLOWED_CHUNKS.filter((type) => !["IHDR", "IDAT", "IEND"].includes(type));
  assert.deepEqual(metadataFindings(png(...allowed.map((type) => pngChunk(type, Buffer.alloc(4))))), []);
  // The list holds no chunk that carries text, a name, a date or embedded data.
  for (const type of ["tEXt", "zTXt", "iTXt", "eXIf", "tIME", "sPLT", "iCCP"]) assert.ok(!PNG_ALLOWED_CHUNKS.includes(type), type);
  // Only the "chunks …" line of the image surface is read; other surfaces and lines are not.
  assert.deepEqual(notAllowedPngChunks("chunks IHDR tEXt tEXt prVt IDAT IEND"), ["tEXt", "prVt"]);
  assert.deepEqual(notAllowedPngChunks("tEXt\nComment"), []);
  const elsewhere = clean();
  elsewhere["file-name"].push("chunks tEXt");
  assert.deepEqual(scanSurfaces(elsewhere, marks), []);
});

test("#691 AC3 (S57): the report names the chunk type, in plain words, and never its content", () => {
  const surfaces = clean();
  const { chunks, texts } = pngMetadata(png(pngChunk("tEXt", Buffer.from("Software\0canvas", "latin1"))));
  surfaces["image-metadata"].push(`chunks ${chunks.join(" ")}`, ...texts);
  const lines = reportLines({ surfaces, findings: scanSurfaces(surfaces, marks), missing: [] });
  const line = lines.find((entry) => entry.includes("thông tin kèm trong file ảnh PNG"));
  assert.match(line, /^ĐỎ/);
  assert.match(line, /không nằm trong danh sách được phép: tEXt$/);
  assert.ok(!lines.join("\n").includes("canvas"));
  assert.equal(lines.at(-1), "Kết quả: ĐỎ");
});

test("#691 AC3: metadata without a mark carries no mark finding in any reading", () => {
  const harmless = png(
    pngChunk("eXIf", exifBlock({ tag: 0x0131, type: 2, value: Buffer.from("canvas export\0", "latin1") })),
    pngChunk("eXIf", exifBlock({ tag: 0x9c9c, type: 1, value: utf16le("ảnh chia sẻ\0") })),
    pngChunk("eXIf", exifBlock({ tag: 0x9003, type: 2, inExifIfd: true, value: Buffer.from("2026:11:21 09:30:00\0", "latin1") })),
    pngChunk("sPLT", Buffer.concat([Buffer.from("web safe\0\x08", "latin1"), Buffer.alloc(6)])),
  );
  assert.deepEqual(pngMetadata(harmless).chunks, ["IHDR", "eXIf", "eXIf", "eXIf", "sPLT", "IDAT", "IEND"]);
  assert.equal(pngMetadata(harmless).texts.length, 4);
  // No mark is found; the only finding is that these chunks are not on the allowed list (S57).
  assert.deepEqual([...new Set(metadataFindings(harmless))], [PNG_CHUNK_NOT_ALLOWED]);
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
