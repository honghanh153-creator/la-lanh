// Leak canary (#690): pure parts. A synthetic profile carries easy-to-find values ("marks") in
// its birth date, birth time, birthplace, mood, Tarot question and the text that reaches the
// safety layer. After a real run of the app, every surface that must never carry them is searched.
// No browser and no server here, so this file runs in the collab test suite.

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
]);

// Cases the app cannot exercise yet. They are printed as "chưa kiểm" and never count as passed.
export const NOT_CHECKED = Object.freeze([
  ["Che nhanh", "chưa có chức năng"],
  ["Màn tự che khi chuyền máy", "chưa có chức năng"],
  ["Tên file tải về và ảnh chia sẻ", "việc #691"],
  ["Nhật ký ở mức DEBUG và nhật ký của máy chủ thật", "lượt chạy dùng mức nhật ký mặc định trên máy cục bộ"],
]);

const stripAccents = (text) => text.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D");
const fold = (text) => String(text).normalize("NFC").toLowerCase();

// Every spelling of a mark that would still identify the value: {kind, forms, clock}.
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
        `${Number(day)}/${Number(month)}/${year}`, `${year}/${month}/${day}`,
      ],
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
// or a clock time with seconds.
const LINE_TIME = /^(\s*[[(]?)(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?|\d{1,2}:\d{2}:\d{2}(?:[.,]\d+)?)/i;

// A birth time such as "03:47" is also the clock time of every log line written in that minute
// (#457). Only that one piece of log metadata is masked: the time at the start of a log line.
// A clock value anywhere else (a payload, a URL, storage, the rest of the line) stays searchable,
// with or without seconds, so "03:47:00" in a query or in JSON is still a finding.
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
  const masked = logLine ? plain.map(maskLogTime) : plain;
  const kinds = [];
  for (const mark of marks) {
    const haystacks = mark.clock ? masked : plain;
    const forms = [...mark.forms, ...mark.forms.map((form) => fold(stripAccents(form)))];
    if (forms.some((form) => haystacks.some((view) => view.includes(form)))) kinds.push(mark.kind);
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
});

// Plain report lines. No value of a mark, no URL and no log line is printed.
export function reportLines({ surfaces, findings, missing, planted = null }) {
  const lines = [];
  for (const name of SURFACES) {
    const hits = findings.filter((finding) => finding.surface === name);
    const count = (surfaces[name] ?? []).length;
    const kinds = [...new Set(hits.map((hit) => hit.kind))].join(", ");
    lines.push(`${hits.length ? "ĐỎ  " : "đạt "} ${SURFACE_NAMES[name]}: ${count} mục${hits.length ? `, thấy dấu: ${kinds}` : ""}`);
  }
  for (const kind of missing) lines.push(`ĐỎ   lượt chạy chưa gửi dấu "${kind}" tới API, nên chưa kiểm được gì cho dấu này`);
  for (const [name, reason] of NOT_CHECKED) lines.push(`chưa kiểm ${name} (${reason})`);
  if (planted) lines.push(`(đã cố ý chèn dấu vào "${planted}" để thử máy kiểm)`);
  const red = findings.length > 0 || missing.length > 0;
  lines.push(red ? "Kết quả: ĐỎ" : "Kết quả: đạt (các ca \"chưa kiểm\" không tính là đạt)");
  return lines;
}
