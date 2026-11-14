import assert from "node:assert/strict";
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { LOADING, PERSONA, RECEIPT_GATE_SINCE, contentExit, contentMode, contentVerdict, receiptGaps, redactRoute } from "./qa-journey-lib.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const O = "https://la-lanh.example";

test("routes never carry IDs or capability tokens", () => {
  assert.equal(redactRoute(`${O}/share/AbCdEf0123456789_-xyzABCDEFGHIJKLMNOPQRSTU`), "/share/:id");
  assert.equal(redactRoute(`${O}/tarot/3f1c2b7e-1111-4a2b-9c3d-0123456789ab`), "/tarot/:id");
  assert.equal(redactRoute(`${O}/radar/result/42`), "/radar/result/:id");
  assert.equal(redactRoute(`${O}/radar/i/short`), "/radar/i/:id");
  assert.equal(redactRoute(`${O}/insights/overview?tradition=jyotish&token=secret`), "/insights/overview?tradition=jyotish");
  assert.equal(redactRoute(`${O}/home`), "/home");
});

test("loading lines are told apart from content that says 'đang'", () => {
  assert.ok(LOADING.test("Lá đang mở đúng hồ sơ của bạn…"));
  assert.ok(LOADING.test("Đang tìm tín hiệu của bạn…"));
  assert.ok(!LOADING.test("Đúng bản đang mở · không kèm ngày / giờ / nơi sinh"));
  assert.ok(!LOADING.test("Bạn đang muốn gỡ chuyện gì?"));
});

test("the journey persona is a plain synthetic date", () => {
  assert.match(`${PERSONA.year}-${PERSONA.month}-${PERSONA.day}`, /^\d{4}-\d{2}-\d{2}$/);
});

test("receipt gate names every missing piece", () => {
  assert.deepEqual(receiptGaps("# Release\n"), ["section", "journey result", "Claude review", "Codex review", "owner report"]);
  const done = [
    "## Product journey",
    "- Run: required failed: 0; guest deleted: true",
    "- Claude review: ok",
    "- Codex review: ok",
    "- Owner report: sent in chat 13.11 22:40",
  ].join("\n");
  assert.deepEqual(receiptGaps(done), []);
});

test("every production receipt since the gate carries a product journey and owner report", () => {
  const reviews = join(root, "docs/reviews");
  const receipts = readdirSync(reviews)
    .map((name) => /^production-release-(\d{4}-\d{2}-\d{2})/.exec(name))
    .filter((match) => match && match[1] >= RECEIPT_GATE_SINCE)
    .map((match) => join(reviews, match[0], "receipt.md"))
    .filter((path) => existsSync(path));
  assert.ok(receipts.length > 0, "expected at least the 2026-11-13 receipt");
  for (const path of receipts) {
    assert.deepEqual(receiptGaps(readFileSync(path, "utf8")), [], path);
  }
});

// L03 (agreement 12.11 item A). Synthetic sections only.
const fullSynthesis = Object.freeze({
  mode: "full_synthesis",
  sections: { hook: "Bạn hợp nhịp làm chậm mà chắc.", thesis: "Bạn nghĩ kỹ trước khi nói.", manifestation: "Bạn ghi việc ra giấy trước khi bắt đầu.", micro_action: "Hôm nay chọn một việc nhỏ và làm xong." },
});
const sparse = Object.freeze({ mode: "basic", sections: { hook: "Hôm nay hợp để dọn một góc bàn." } });

test("a dropped synthesis or placeholder text fails; valid sparse data passes", () => {
  assert.deepEqual(contentVerdict({ expect: { synthesis: true }, api: fullSynthesis }), { status: "PASS", findings: [] });
  assert.deepEqual(contentVerdict({ expect: { synthesis: false }, api: sparse }), { status: "PASS", findings: [] }, "date-only data without a synthesis is valid");
  const dropped = contentVerdict({ expect: { synthesis: true }, api: { mode: "basic", sections: { hook: "x" } } });
  assert.equal(dropped.status, "FAIL", "the expectation comes from the scenario: losing mode and synthesis together still fails");
  assert.ok(dropped.findings.includes("api-synthesis-missing:mode") && dropped.findings.includes("api-synthesis-missing:thesis"));
  assert.deepEqual(contentVerdict({ expect: { synthesis: true }, api: null }).findings, ["api-synthesis-missing:answer"], "an answer with no reading at all");
  const blank = contentVerdict({ expect: { synthesis: true }, api: { ...fullSynthesis, sections: { ...fullSynthesis.sections, micro_action: "  " } } });
  assert.deepEqual(blank.findings, ["api-synthesis-missing:micro_action"]);
  for (const text of ["Lorem ipsum dolor", "TODO: viết lại", "Xin chào {{name}}", "Giá trị undefined", "[object Object]", "nội dung tạm"]) {
    const v = contentVerdict({ expect: { synthesis: false }, api: { mode: "basic", sections: { hook: text } } });
    assert.equal(v.status, "FAIL", text);
    assert.match(v.findings[0], /^api-placeholder:\w[\w-]*@hook$/);
  }
});

test("an API answer with the synthesis and a screen without it fails", () => {
  const ui = { text: "Khám phá\nBạn hợp nhịp làm chậm mà chắc.\nBạn nghĩ kỹ trước khi nói.", synthesis: "Bạn hợp nhịp làm chậm mà chắc. Bạn nghĩ kỹ trước khi nói." };
  assert.equal(contentVerdict({ expect: { synthesis: true }, api: fullSynthesis, ui }).status, "PASS");
  assert.deepEqual(contentVerdict({ expect: { synthesis: true }, api: fullSynthesis, ui: { text: "Khám phá", synthesis: "" } }).findings, ["ui-synthesis-missing"]);
  assert.deepEqual(contentVerdict({ expect: { synthesis: true }, api: fullSynthesis, ui: { text: "Khám phá", synthesis: "Một câu khác hẳn." } }).findings, ["ui-synthesis-not-the-api-synthesis"]);
  assert.deepEqual(contentVerdict({ expect: { synthesis: true }, api: fullSynthesis, ui: { ...ui, text: `${ui.text}\nTBD` } }).findings, ["ui-placeholder:todo@screen"]);
});

test("a JSON null is data, not placeholder text; report mode relaxes content findings only", () => {
  assert.equal(contentVerdict({ expect: { synthesis: false }, api: { mode: "basic", sections: { hook: "Ổn.", extra: null, count: 0 } } }).status, "PASS");
  const fail = [{ status: "FAIL", findings: ["api-synthesis-missing:mode"] }];
  assert.equal(contentMode({}), "report");
  assert.equal(contentMode({ LA_LANH_QA_CONTENT: "enforce" }), "enforce");
  assert.equal(contentExit(fail, "report"), 0);
  assert.equal(contentExit(fail, "enforce"), 1);
  assert.equal(contentExit([{ status: "PASS", findings: [] }], "enforce"), 0);
});
