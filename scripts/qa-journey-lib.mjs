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
