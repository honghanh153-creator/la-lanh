// Leak canary (#690): pure parts. A synthetic profile carries easy-to-find values ("marks") in
// its birth date, birth time, birthplace, mood, Tarot question and the text that reaches the
// safety layer. After a real run of the app, every surface that must never carry them is searched.
// #691 adds what leaves the app as a file: the names of downloaded and shared files, the input the
// share image is drawn from, and the metadata inside the PNG.
// No browser and no server here, so this file runs in the collab test suite.
import { inflateSync } from "node:zlib";

// Synthetic values only, not derived from any real person. The date and the place must be valid
// for the app, so they are ordinary values chosen to be rare in logs; the two free-text marks are
// made-up words.
export const CANARY = Object.freeze({
  day: "13",
  month: "02",
  year: "1994",
  hour: "03",
  minute: "47",
  place: "Quảng Ngãi",
  mood: "Đuối",
  tarotMark: "zqcanary690tarot",
  safetyMark: "zqcanary690safety",
});

export const TAROT_QUESTION = `Tuần này mình nên tập trung vào việc gì ${CANARY.tarotMark}?`;
// The phrase is the one the API's own crisis tests use; the safety layer must answer with the
// notice and keep nothing.
export const SAFETY_TEXT = `Dạo này mình chỉ muốn chết thôi, có nên không ${CANARY.safetyMark}`;

// Surfaces of AC2 (#690) plus the web cache of US-03 AC12. Each is a list of strings collected by
// the runner; `external-request` is special: any entry there is a finding by itself.
export const SURFACES = Object.freeze([
  "server-log",
  "request-url",
  "request-referer",
  "external-request",
  "error-report",
  "error-response",
  "browser-history",
  "current-url",
  "web-storage",
  "file-name",
  "share-image",
  "image-metadata",
]);

// Cases the app cannot exercise yet. They are printed as "chưa kiểm" and never count as passed.
export const NOT_CHECKED = Object.freeze([
  ["Che nhanh", "chưa có chức năng"],
  ["Màn tự che khi chuyền máy", "chưa có chức năng"],
  ["Chữ đã vẽ thành điểm ảnh trong ảnh PNG", "máy không đọc chữ trong ảnh; nó kiểm bản SVG mà ảnh được vẽ từ đó"],
  ["File và ảnh chia sẻ trong app di động", "lượt chạy dùng trình duyệt, bảng chia sẻ là bản giả"],
  ["Nhật ký ở mức DEBUG và nhật ký của máy chủ thật", "lượt chạy dùng mức nhật ký mặc định trên máy cục bộ"],
]);

const stripAccents = (text) => text.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D");
const fold = (text) => String(text).normalize("NFC").toLowerCase();

const MONTH_WORDS = ["jan(?:uary)?", "feb(?:ruary)?", "mar(?:ch)?", "apr(?:il)?", "may", "june?", "july?", "aug(?:ust)?", "sep(?:t(?:ember)?)?", "oct(?:ober)?", "nov(?:ember)?", "dec(?:ember)?"];

// The birth date as other writers spell it (Codex #768 r2: EXIF writes "YYYY:MM:DD"). A list of
// fixed spellings always misses one, so the date is matched by its parts: the three part orders
// (year-month-day, day-month-year, month-day-year) with any one character that is not a letter or
// a digit between the parts, with or without leading zeros; and the month as a word, in English
// ("13 Feb 1994", "February 13th, 1994") or Vietnamese ("13 tháng 2 năm 1994", "13 thg 2, 1994").
// A digit just before or after the date means a longer number, not this date. The patterns run on
// folded text (lower case), with and without accents.
function datePatterns({ day, month, year }) {
  const part = (value) => (Number(value) < 10 ? `0?${Number(value)}` : String(Number(value)));
  const [d, m, y] = [part(day), part(month), String(year)];
  const sep = "[^0-9a-z]";
  const gap = "[^0-9a-z]{0,2}";
  const word = MONTH_WORDS[Number(month) - 1];
  const ordinal = "(?:st|nd|rd|th)?";
  const vietnamese = `th(?:áng|ang|g)\\.?\\s?${m}(?![0-9])${gap}(?:n[aă]m)?`;
  return [
    `${y}${sep}${m}${sep}${d}`,
    `${d}${sep}${m}${sep}${y}`,
    `${m}${sep}${d}${sep}${y}`,
    `${d}${ordinal}${gap}${word}${gap}${y}`,
    `${word}${gap}${d}${ordinal}${gap}${y}`,
    `${y}${gap}${word}${gap}${d}`,
    `${d}${gap}${vietnamese}${gap}${y}`,
  ].map((body) => new RegExp(`(?<![0-9])${body}(?![0-9])`));
}

// Every spelling of a mark that would still identify the value: {kind, forms, clock, patterns}.
// In a log line, `clock` marks are searched after the line's own timestamp is masked (see maskLogTime).
export function buildMarks({ canary = CANARY, placeId = null, secrets = [] } = {}) {
  const { day, month, year, hour, minute } = canary;
  const plainPlace = stripAccents(canary.place);
  const marks = [
    {
      kind: "birth-date",
      forms: [
        `${year}-${month}-${day}`, `${day}/${month}/${year}`, `${day}-${month}-${year}`,
        `${day}.${month}.${year}`, `${year}${month}${day}`, `${day}${month}${year}`,
        `${Number(day)}/${Number(month)}/${year}`, `${year}/${month}/${day}`, `${month}${day}${year}`,
      ],
      patterns: datePatterns(canary),
    },
    { kind: "birth-time", clock: true, forms: [`${hour}:${minute}`, `${hour}h${minute}`] },
    {
      kind: "birthplace",
      forms: [
        canary.place, plainPlace, plainPlace.replace(/\s+/g, "-"), plainPlace.replace(/\s+/g, "_"),
        plainPlace.replace(/\s+/g, ""), canary.place.replace(/\s+/g, "+"), plainPlace.replace(/\s+/g, "+"),
        ...(placeId ? [placeId] : []),
      ],
    },
    { kind: "mood", forms: [canary.mood, canary.mood.normalize("NFD")] },
    { kind: "tarot-question", forms: [canary.tarotMark] },
    { kind: "safety-text", forms: [canary.safetyMark] },
  ];
  // Session secrets (cookie values, CSRF token) read at run time. Short values are skipped: they
  // would match by accident.
  const long = [...new Set(secrets.filter((value) => typeof value === "string" && value.length >= 16))];
  if (long.length) marks.push({ kind: "session-secret", forms: long });
  return marks.map((mark) => ({ ...mark, forms: [...new Set(mark.forms.map(fold))] }));
}

// The time a logger writes at the start of its line, bare or in brackets: a date with a clock time,
// or a clock time with seconds, and then the line's level in capitals ("03:47:12 INFO",
// "[2026-11-19 03:47:12,512] [ERROR]", "03:47:12.5 | WARNING |"). The level is what tells a logger's
// own timestamp from a value: a line that just starts with a clock time may be the birth time
// itself, so it is not masked (Codex #753 r2).
const LINE_TIME = /^(\s*[[(]?)(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?|\d{1,2}:\d{2}:\d{2}(?:[.,]\d+)?)(?=[\])]?[\s|,:-]*[[(]?(?:TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|CRITICAL|FATAL)(?![A-Za-z0-9_]))/;

// A birth time such as "03:47" is also the clock time of every log line written in that minute
// (#457). Only that one piece of log metadata is masked: the time at the start of a log line in a
// recognised logger format. A clock value anywhere else (a payload, a URL, storage, the rest of the
// line, the start of a line without a level) stays searchable, with or without seconds, so
// "03:47:00" in a query, in JSON or alone on a log line is still a finding.
export function maskLogTime(line) {
  return line.replace(LINE_TIME, "$1<log-time>");
}

function decoded(text) {
  try {
    return decodeURIComponent(text.replace(/\+/g, " "));
  } catch {
    return text;
  }
}

// The text as written, percent-decoded once and twice (a value can be encoded again inside a
// query value), and without accents.
function views(text) {
  const once = decoded(text);
  const all = new Set([text, once, decoded(once)]);
  for (const view of [...all]) all.add(stripAccents(view));
  return [...all].map(fold);
}

// Findings for one piece of text: [{kind}] for each mark found, once per kind. `logLine` says the
// text is one line of a server log, the only place where a leading timestamp is masked.
export function findMarks(text, marks, { logLine = false } = {}) {
  const plain = views(String(text));
  // Masked before folding: the level must be in capitals, as loggers write it.
  const masked = logLine ? views(maskLogTime(String(text))) : plain;
  const kinds = [];
  for (const mark of marks) {
    const haystacks = mark.clock ? masked : plain;
    const forms = [...mark.forms, ...mark.forms.map((form) => fold(stripAccents(form)))];
    const spelled = forms.some((form) => haystacks.some((view) => view.includes(form)));
    const matched = (mark.patterns ?? []).some((pattern) => haystacks.some((view) => pattern.test(view)));
    if (spelled || matched) kinds.push(mark.kind);
  }
  return kinds;
}

// surfaces: {name: string[]}. Returns findings {surface, kind, index}. The value itself is never
// put in a finding: the report must be safe to paste into a public PR.
export function scanSurfaces(surfaces, marks) {
  const findings = [];
  for (const name of SURFACES) {
    const entries = surfaces[name] ?? [];
    entries.forEach((entry, index) => {
      if (name === "external-request") {
        findings.push({ surface: name, kind: "request-left-the-app", index });
        return;
      }
      // S57: a share image may only hold the chunks on the allowed list, mark or no mark.
      if (name === "image-metadata" && notAllowedPngChunks(entry).length) findings.push({ surface: name, kind: PNG_CHUNK_NOT_ALLOWED, index });
      for (const kind of findMarks(entry, marks, { logLine: name === "server-log" })) findings.push({ surface: name, kind, index });
    });
  }
  return findings;
}

// Everything the page keeps: localStorage, sessionStorage, and for each Cache entry its URL, the
// headers and the body of the stored answer (US-03 AC12), plus the page title. It runs inside the
// page through page.evaluate, so it must not use anything outside its own body; `env` is the
// page's global object there and a stand-in in tests.
export async function dumpWebStorage(env = globalThis) {
  const entries = [];
  for (const [name, store] of [["localStorage", env.localStorage], ["sessionStorage", env.sessionStorage]]) {
    if (!store) continue;
    for (let i = 0; i < store.length; i += 1) {
      const key = store.key(i);
      entries.push(`${name} ${key} ${store.getItem(key)}`);
    }
  }
  if (env.caches) {
    for (const name of await env.caches.keys()) {
      const cache = await env.caches.open(name);
      for (const request of await cache.keys()) {
        const response = await cache.match(request);
        const headers = response ? [...response.headers].map(([key, value]) => `${key}: ${value}`).join("\n") : "";
        const body = response ? await response.clone().text() : "";
        entries.push(`cache ${name} ${request.url}\n${headers}\n${body}`);
      }
    }
  }
  if (env.document) entries.push(`title ${env.document.title}`);
  return entries;
}

// The text a share image is drawn from. The app builds one SVG, shows it and draws the PNG from
// that same string, so the SVG is the whole input of the picture. Takes the SVG or its data URL.
// Embedded base64 payloads (the fonts) are cut out: they are not text, and a long random string
// can contain a short mark by accident. Numeric character references are turned back into letters.
export function svgTextOf(source) {
  let svg = String(source ?? "");
  if (svg.startsWith("data:")) {
    const body = svg.slice(svg.indexOf(",") + 1);
    try {
      svg = decodeURIComponent(body);
    } catch {
      svg = body;
    }
  }
  return svg
    .replace(/(data:[a-z0-9.+/-]+(?:;[a-z0-9=-]+)*;base64,)[A-Za-z0-9+/=\s]+/gi, "$1<payload>")
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(Number.parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(Number(dec)));
}

const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
// Chunks that only describe pixels and colour. Every other chunk can carry text or a date.
// sPLT is not in this list: it starts with a free-text palette name.
const PNG_PIXEL_CHUNKS = new Set(["IHDR", "PLTE", "IDAT", "IEND", "tRNS", "gAMA", "cHRM", "sRGB", "sBIT", "bKGD", "pHYs", "hIST", "acTL", "fcTL", "fdAT"]);

// S57 (#691 AC3): the image the app hands out may only hold chunks from this list. It is the
// pixel list above, checked on 24.11.2026 against the chunk list of the W3C PNG specification
// (editor's draft, section 4.7.2, https://w3c.github.io/png/). Left out on purpose: the chunks
// that carry text, a name, a date or embedded data (tEXt, zTXt, iTXt, eXIf, tIME, sPLT, iCCP),
// chunks added by newer editions (cICP, mDCV) until the app is known to write them, and every
// private or unknown chunk. Searching for marks only finds what the marks describe; a chunk
// that is not on the list is red even when no mark is found in it.
export const PNG_CHUNK_NOT_ALLOWED = "png-chunk-not-allowed";
export const PNG_ALLOWED_CHUNKS = Object.freeze([...PNG_PIXEL_CHUNKS]);

// Chunk types of one "chunks A B C" line (as leak-canary writes it) that are not allowed, once
// each. Any other line gives [].
export function notAllowedPngChunks(line) {
  const text = String(line);
  if (!text.startsWith("chunks ")) return [];
  return [...new Set(text.slice(7).split(" ").filter((type) => type !== "" && !PNG_PIXEL_CHUNKS.has(type)))];
}

function inflated(data) {
  try {
    return inflateSync(data);
  } catch {
    return null;
  }
}

// Every way the bytes of a metadata field can be read as text. EXIF writes some fields with two
// bytes per letter (XPComment, UserComment "UNICODE"), in either byte order and starting at any
// offset, so the bytes are read as UTF-16 in both byte orders, from offset 0 and from offset 1.
function wideViews(bytes) {
  const even = Buffer.concat([bytes, Buffer.alloc(bytes.length % 2)]);
  return [even.toString("utf16le"), Buffer.from(even).swap16().toString("utf16le")];
}
function textViews(bytes) {
  return [bytes.toString("latin1"), bytes.toString("utf8"), ...wideViews(bytes), ...wideViews(bytes.subarray(1))];
}

// What a PNG says besides its pixels (AC3 of #691): {chunks, texts}. `chunks` lists every chunk
// type in order; `texts` has one entry for each chunk that is not pure pixel data: text chunks
// (tEXt, zTXt, iTXt, with compressed parts unpacked), EXIF (eXIf), the modification time (tIME),
// suggested palettes (sPLT, for their name), colour profiles and chunks this list does not know.
// Each is given in every reading of textViews, so two-byte EXIF text is found too. Throws when the bytes are not a PNG.
export function pngMetadata(bytes) {
  const data = Buffer.from(bytes);
  if (data.length < 8 || PNG_SIGNATURE.some((byte, index) => data[index] !== byte)) throw new Error("không phải file PNG");
  const chunks = [];
  const texts = [];
  let offset = 8;
  while (offset + 12 <= data.length) {
    const length = data.readUInt32BE(offset);
    const type = data.toString("latin1", offset + 4, offset + 8);
    const body = data.subarray(offset + 8, offset + 8 + length);
    if (body.length < length) throw new Error("file PNG bị cụt");
    chunks.push(type);
    if (type === "tIME" && length === 7) {
      const two = (value) => String(value).padStart(2, "0");
      texts.push(`tIME ${body.readUInt16BE(0)}-${two(body[2])}-${two(body[3])} ${two(body[4])}:${two(body[5])}:${two(body[6])}`);
    } else if (!PNG_PIXEL_CHUNKS.has(type)) {
      // Compressed parts start after a keyword and a few flag bytes; trying each zero byte as the
      // start covers zTXt, iTXt and iCCP without a parser for each.
      const unpacked = [];
      for (let at = body.indexOf(0); at !== -1 && unpacked.length < 4; at = body.indexOf(0, at + 1)) {
        for (const skip of [1, 2, 3]) {
          const plain = inflated(body.subarray(at + skip));
          if (plain?.length) unpacked.push(plain);
        }
      }
      texts.push([type, ...[body, ...unpacked].flatMap(textViews)].join("\n"));
    }
    offset += 12 + length;
  }
  if (chunks.at(-1) !== "IEND") throw new Error("file PNG bị cụt");
  return { chunks, texts };
}

// Files the run must have taken out of the app. Without them the three file surfaces would pass
// without looking at anything.
export const REQUIRED_FILES = Object.freeze(["note-card-png", "note-card-share", "birth-card-png", "birth-card-share", "data-export-file"]);

export function missingFiles(collected) {
  return REQUIRED_FILES.filter((kind) => !collected.has(kind));
}

// Environment of the QA launcher for one run. The launcher takes its database from
// LA_LANH_QA_DATABASE_URL and overwrites LA_LANH_DATABASE_URL, so the scratch path goes there;
// it also replaces a value inherited from the caller, which could name an existing database.
export function canaryServerEnv({ base = {}, databaseFile, apiPort, webPort }) {
  return {
    ...base,
    LA_LANH_QA_DATABASE_URL: `sqlite+aiosqlite:///${databaseFile}`,
    LA_LANH_QA_API_PORT: String(apiPort),
    LA_LANH_QA_WEB_PORT: String(webPort),
  };
}

// True when the URL belongs to the app under test. Anything else is a request that left it.
export function isLocalUrl(url, origin) {
  try {
    const target = new URL(url);
    if (["data:", "blob:", "about:"].includes(target.protocol)) return true;
    return target.origin === new URL(origin).origin;
  } catch {
    return false;
  }
}

// What the journey must have sent to the API for the check to mean anything. A run that never
// sent a mark would pass without looking at anything.
export const REQUIRED_SENDS = Object.freeze(["birth-date", "birth-time", "birthplace", "mood", "tarot-question", "safety-text"]);

export function missingSends(sent) {
  return REQUIRED_SENDS.filter((kind) => !sent.has(kind));
}

// Which marks a request body carries. Bodies are the allowed channel; this is only used to prove
// coverage. Birth time is matched on its field so a timestamp cannot stand in for it.
export function sendsIn(method, path, body, { canary = CANARY } = {}) {
  if (method === "GET" || typeof body !== "string" || body === "") return [];
  const text = fold(body);
  const sent = [];
  if (text.includes(`${canary.year}-${canary.month}-${canary.day}`)) sent.push("birth-date");
  if (text.includes(`"birth_time_local":"${canary.hour}:${canary.minute}`) || text.includes(`"birth_time_local": "${canary.hour}:${canary.minute}`)) sent.push("birth-time");
  if (path.includes("/birth-places/search") && text.includes(fold(canary.place))) sent.push("birthplace");
  if (/\/mood$/.test(path) && text.includes(fold(canary.mood))) sent.push("mood");
  if (text.includes(canary.tarotMark)) sent.push("tarot-question");
  if (text.includes(canary.safetyMark)) sent.push("safety-text");
  return sent;
}

const SURFACE_NAMES = Object.freeze({
  "server-log": "nhật ký máy chủ",
  "request-url": "đường mạng (URL và query)",
  "request-referer": "header Referer",
  "external-request": "request ra ngoài app",
  "error-report": "báo lỗi (console, lỗi trang)",
  "error-response": "nội dung câu trả lời lỗi của API",
  "browser-history": "lịch sử trình duyệt",
  "current-url": "URL hiện tại",
  "web-storage": "bộ nhớ trình duyệt (localStorage, sessionStorage, nội dung Cache)",
  "file-name": "tên file tải về và file đưa vào bảng chia sẻ",
  "share-image": "ảnh chia sẻ (bản SVG ảnh được vẽ từ đó, chữ mô tả ảnh, tiêu đề chia sẻ)",
  "image-metadata": "thông tin kèm trong file ảnh PNG",
});

// Plain report lines. No value of a mark, no URL and no log line is printed.
export function reportLines({ surfaces, findings, missing, missingFiles: noFiles = [], planted = null }) {
  const lines = [];
  for (const name of SURFACES) {
    const hits = findings.filter((finding) => finding.surface === name);
    const count = (surfaces[name] ?? []).length;
    const kinds = [...new Set(hits.map((hit) => hit.kind))];
    const marks = kinds.filter((kind) => kind !== PNG_CHUNK_NOT_ALLOWED).join(", ");
    // Chunk type names (four letters) are printed; their content never is.
    const odd = [...new Set(hits.filter((hit) => hit.kind === PNG_CHUNK_NOT_ALLOWED).flatMap((hit) => notAllowedPngChunks((surfaces[name] ?? [])[hit.index]).map((type) => type.replace(/[^A-Za-z]/g, "?"))))].join(", ");
    const why = [marks && `thấy dấu: ${marks}`, odd && `ảnh có phần không nằm trong danh sách được phép: ${odd}`].filter(Boolean).join("; ");
    lines.push(`${hits.length ? "ĐỎ  " : "đạt "} ${SURFACE_NAMES[name]}: ${count} mục${why ? `, ${why}` : ""}`);
  }
  for (const kind of missing) lines.push(`ĐỎ   lượt chạy chưa gửi dấu "${kind}" tới API, nên chưa kiểm được gì cho dấu này`);
  for (const kind of noFiles) lines.push(`ĐỎ   lượt chạy chưa lấy được "${kind}" từ app, nên chưa kiểm được gì cho file này`);
  for (const [name, reason] of NOT_CHECKED) lines.push(`chưa kiểm ${name} (${reason})`);
  if (planted) lines.push(`(đã cố ý chèn dấu vào "${planted}" để thử máy kiểm)`);
  const red = findings.length > 0 || missing.length > 0 || noFiles.length > 0;
  lines.push(red ? "Kết quả: ĐỎ" : "Kết quả: đạt (các ca \"chưa kiểm\" không tính là đạt)");
  return lines;
}
