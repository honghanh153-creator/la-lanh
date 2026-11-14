import assert from "node:assert/strict";
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { LOADING, PERSONA, RECEIPT_GATE_SINCE, receiptGaps, redactRoute } from "./qa-journey-lib.mjs";

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
