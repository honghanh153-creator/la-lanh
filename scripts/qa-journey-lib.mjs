// Shared pieces of the post-release product journey (scripts/qa-product-journey.mjs) and its
// release gate. Pure functions only, so they run in the collab test suite without a browser.

// A synthetic person, not derived from any real person.
export const PERSONA = Object.freeze({ day: "21", month: "09", year: "1996", hour: "07", minute: "30", place: "Đà Nẵng" });

// Loading lines the app shows while it fetches. Ordinary text that merely says "đang" is content.
export const LOADING = /(Đang tìm tín hiệu|đang mở đúng hồ sơ|Đang tải|Đang mở lại|Đang khóa bộ bài|Đang tính|Loading)/i;

// Route segments that can carry IDs or capability tokens are never written out.
export function redactRoute(url) {
  const { pathname, search } = new URL(url);
  const path = pathname
    .split("/")
    .map((part, index, parts) => {
      const previous = parts[index - 1];
      if (part && ["share", "i", "result", "received", "tarot"].includes(previous)) return ":id";
      if (/^[A-Za-z0-9_-]{16,}$/.test(part) || /^[0-9a-f-]{32,36}$/i.test(part)) return ":id";
      return part;
    })
    .join("/");
  const keep = new URLSearchParams();
  for (const [key, value] of new URLSearchParams(search)) {
    if (["tradition", "tab", "view"].includes(key)) keep.set(key, value);
  }
  const query = keep.toString();
  return query ? `${path}?${query}` : path;
}

// Release gate (owner, 13.11.2026): a production release is not finished until a real product
// journey ran on production and both reviews reached the owner. Every receipt from this date on
// must carry the section below; scripts/qa-journey-lib.test.mjs enforces it in CI.
export const RECEIPT_GATE_SINCE = "2026-11-13";
export const RECEIPT_REQUIREMENTS = Object.freeze([
  ["section", /^## Product journey$/m],
  ["journey result", /required failed: 0; guest deleted: true/],
  ["Claude review", /^- Claude review: \S/m],
  ["Codex review", /^- Codex review: \S/m],
  ["owner report", /^- Owner report: \S/m],
]);

export function receiptGaps(text) {
  return RECEIPT_REQUIREMENTS.filter(([, pattern]) => !pattern.test(text)).map(([name]) => name);
}

// Content verdict (lesson L03; agreement 12.11 item A): a page or API answer that lost its synthesis,
// or still shows temporary text, fails; valid sparse data passes. Report mode first: the verdict is
// printed and saved, and only LA_LANH_QA_CONTENT=enforce turns a content finding into an exit code.
// Flow errors (HTTP status, start-up, a step that broke) always fail, in both modes.
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - whether a synthesis is expected comes from the scenario (an exact birth time was given), never
//   from the answer being checked, so an answer that lost both its mode and its synthesis fails;
// - the synthesis is checked by its own sections in the API and by its own block on the screen;
//   an API answer with the synthesis and a screen without it fails;
// - only display strings are scanned: a JSON null or a number is data, not temporary text.
export const SYNTHESIS_SECTIONS = Object.freeze(["hook", "thesis", "manifestation", "micro_action"]);
export const PLACEHOLDER = Object.freeze([
  ["lorem", /lorem ipsum/i],
  ["todo", /\b(TODO|TBD|FIXME)\b/],
  ["template", /\{\{[^}]*\}\}|\$\{[^}]*\}|%\(\w+\)s/],
  ["js-leak", /\b(undefined|NaN)\b|\[object Object\]|\bnull\b/],
  ["temporary", /nội dung tạm|chữ tạm|placeholder|\bxxx+\b/i],
]);

// Every string leaf with its path. Numbers, booleans and null are data and are skipped.
export function displayStrings(value, path = "") {
  if (typeof value === "string") return [{ path: path || "(text)", text: value }];
  if (Array.isArray(value)) return value.flatMap((item, i) => displayStrings(item, `${path}[${i}]`));
  if (value && typeof value === "object") return Object.entries(value).flatMap(([key, item]) => displayStrings(item, path ? `${path}.${key}` : key));
  return [];
}

const placeholderFindings = (entries, where) => entries.flatMap(({ path, text }) =>
  PLACEHOLDER.filter(([, pattern]) => pattern.test(text)).map(([name]) => `${where}-placeholder:${name}@${path}`));
const filled = (text) => typeof text === "string" && text.replace(/\s+/g, " ").trim().length > 0;
const squash = (text) => String(text ?? "").normalize("NFC").replace(/\s+/g, " ").trim();

// expect: { synthesis: boolean } from the scenario. api: the reading projection's `active` object
// (or null when the step has no API answer). ui: { text, synthesis } from the screen, or null.
// api undefined: the step has no API answer to check; api null: the answer had no reading at all.
export function contentVerdict({ expect, api, ui = null }) {
  const findings = [];
  if (api === null && expect.synthesis) findings.push("api-synthesis-missing:answer");
  if (api !== undefined && api !== null) {
    findings.push(...placeholderFindings(displayStrings(api?.sections ?? {}), "api"));
    if (expect.synthesis) {
      if (api?.mode !== "full_synthesis") findings.push("api-synthesis-missing:mode");
      for (const section of SYNTHESIS_SECTIONS) if (!filled(api?.sections?.[section])) findings.push(`api-synthesis-missing:${section}`);
    }
  }
  if (ui !== null) {
    findings.push(...placeholderFindings([{ path: "screen", text: ui.text ?? "" }], "ui"));
    if (expect.synthesis) {
      if (!filled(ui.synthesis)) findings.push("ui-synthesis-missing");
      else if (api && filled(api.sections?.hook) && !squash(ui.synthesis).includes(squash(api.sections.hook))) findings.push("ui-synthesis-not-the-api-synthesis");
    }
  }
  return { status: findings.length ? "FAIL" : "PASS", findings: [...new Set(findings)] };
}

export const contentMode = (env = process.env) => (env.LA_LANH_QA_CONTENT === "enforce" ? "enforce" : "report");
// Exit code contribution of the content verdicts: only enforce mode fails on them.
export const contentExit = (verdicts, mode) => (mode === "enforce" && verdicts.some((v) => v.status !== "PASS") ? 1 : 0);
