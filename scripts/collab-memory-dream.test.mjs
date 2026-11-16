import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { apply, contradictions, dream, prune, reportLine } from './collab-memory-dream.mjs';
import { parseRules, sheetPath } from './collab-rules.mjs';

const sheet = readFileSync(sheetPath(), 'utf8');
const { facts } = parseRules(sheet);
const entry = (name, description, body, type = 'feedback') => `---\nname: ${name}\ndescription: ${description}\nmetadata:\n  type: ${type}\n---\n\n${body}\n`;

// A synthetic memory folder (never the owner's): a pointer, a current rule, a stale cap, an entry
// already marked old, two near-duplicates and one entry missing from the index.
function store() {
  const dir = mkdtempSync(join(tmpdir(), 'dream-mem-'));
  const files = {
    'luat-dang-hieu-luc.md': entry('luat-dang-hieu-luc', 'pointer', '- R3: [[ask-in-file]]\n- R8/R9: [[cap-now]] [[cap-stale]]'),
    'ask-in-file.md': entry('ask-in-file', 'Owner: put questions in the decisions file', 'Never ask in chat.'),
    'cap-now.md': entry('cap-now', 'Codex cap is 80 a day', 'The Codex cap is 80 runs; work until 23:59.'),
    'cap-stale.md': entry('cap-stale', 'Codex budget', 'Keep the Codex cap at 60 runs a day. The loop stops at 23:00.'),
    'old-gate.md': entry('old-gate', '9h plan gate [OLD]', 'Morning approval gate at nine before reviews; Codex cap 32.'),
    'dup-a.md': entry('dup-a', 'persona run', 'Nightly persona simulation picks two hundred random personas from thousand fake profiles every evening.'),
    'dup-b.md': entry('dup-b', 'persona run again', 'Nightly persona simulation picks two hundred random personas from thousand fake profiles each evening.'),
    'not-indexed.md': entry('not-indexed', 'An entry nobody indexed', 'Plain note.'),
  };
  for (const [f, t] of Object.entries(files)) writeFileSync(join(dir, f), t);
  writeFileSync(join(dir, 'MEMORY.md'), ['luat-dang-hieu-luc', 'ask-in-file', 'cap-now', 'cap-stale', 'old-gate', 'dup-a', 'dup-b', 'gone'].map(s => `- [${s}](${s}.md) — hook`).join('\n'));
  return { dir, files };
}

test('dream: proposes stale marks, duplicates, reference checks and index fixes in a NEW store only', () => {
  const { dir, files } = store();
  const out = join(mkdtempSync(join(tmpdir(), 'dream-out-')), '2026-11-17');
  const summary = dream({ memory: dir, out, sheet, date: '2026-11-17' });
  // The real store is untouched, byte for byte.
  for (const [f, t] of Object.entries(files)) assert.equal(readFileSync(join(dir, f), 'utf8'), t, f);
  const changes = JSON.parse(readFileSync(join(out, 'changes.json'), 'utf8'));
  assert.deepEqual(changes.stale.map(s => s.file), ['cap-stale.md']);
  assert.deepEqual(changes.stale[0].rules.sort(), ['R8', 'R9']);
  const index = readFileSync(join(out, 'memory', 'MEMORY.md'), 'utf8');
  assert.match(index, /\[cap-stale \[OLD → R8\]\]\(cap-stale\.md\)/);
  // An entry already marked old is history: not flagged again, never "verified".
  assert.doesNotMatch(index, /old-gate \[OLD →/);
  // Reference-checked only for entries linked to a rule id with no contradiction; the note names the sheet version.
  assert.deepEqual(changes.rulesChecked.map(v => v.file).sort(), ['ask-in-file.md', 'cap-now.md']);
  assert.match(readFileSync(join(out, 'memory', 'cap-now.md'), 'utf8'), /^metadata:\n {2}rules-checked: "2026-11-17 docs\/operations\/luat-dang-hieu-luc\.md@[0-9a-f]{16} \(R8, R9; chỉ kiểm Id và số\)"/m);
  assert.doesNotMatch(readFileSync(join(out, 'memory', 'cap-stale.md'), 'utf8'), /rules-checked/);
  assert.deepEqual(changes.duplicates.map(d => d.files), [['dup-a.md', 'dup-b.md']]);
  assert.deepEqual(changes.indexAdded, ['not-indexed.md']);
  assert.deepEqual(changes.indexMissingFile, ['gone.md']);
  assert.match(readFileSync(join(out, 'diff.patch'), 'utf8'), /\+ {2}rules-checked:/);
  // Private like the memory: owner-only modes.
  for (const f of ['diff.patch', 'summary.json', 'changes.json', 'manifest.json', 'memory/MEMORY.md']) assert.equal(statSync(join(out, f)).mode & 0o777, 0o600, f);
  assert.equal(statSync(join(out, 'memory')).mode & 0o777, 0o700);
  assert.equal(existsSync(join(out, 'before')), false);
  // The summary is counts and rule ids only: no memory text can reach the report.
  const text = readFileSync(join(out, 'summary.json'), 'utf8');
  for (const t of Object.values(files)) for (const line of t.split('\n').filter(l => l.length > 12)) assert.equal(text.includes(line), false, line);
  assert.deepEqual({ stale: summary.stale, duplicates: summary.duplicates, rulesChecked: summary.rulesChecked }, { stale: 1, duplicates: 1, rulesChecked: 2 });
  assert.match(reportLine(summary), /^Trí nhớ đổi gì: đề xuất đánh dấu 1 mục cũ \(R8, R9\)/);
  assert.equal(reportLine(null), 'Trí nhớ: đêm qua chưa chạy dọn.');
});

test('dream: a stale cap, stop time or retired report slot is caught; history lines are not', () => {
  assert.deepEqual(contradictions('Keep the Codex cap at 60 a day.', facts).map(c => c.rule), ['R8']);
  assert.deepEqual(contradictions('trần Codex 32 lượt', facts).map(c => c.rule), ['R8']);
  assert.deepEqual(contradictions('The loop stops at 23:00.', facts).map(c => c.rule), ['R9']);
  assert.deepEqual(contradictions('Send the report at 08:00.', facts).map(c => c.rule), ['R5']);
  assert.deepEqual(contradictions('Codex cap 80; no new work after 23:35, stops 23:59.', facts), []);
  assert.deepEqual(contradictions('The old cap was 60 (replaced by 80).', facts), []);
  assert.deepEqual(contradictions('drop the 08:00 report', facts), []);
});

test('dream: a run on an empty folder writes an empty proposal, never crashes', () => {
  const dir = mkdtempSync(join(tmpdir(), 'dream-empty-'));
  mkdirSync(dir, { recursive: true });
  const out = join(mkdtempSync(join(tmpdir(), 'dream-out-')), 'x');
  assert.deepEqual(dream({ memory: dir, out, sheet, date: '2026-11-17' }).stale, 0);
});

test('dream apply: only accepted files, only when the source and the rules did not change', () => {
  const { dir, files } = store();
  const out = join(mkdtempSync(join(tmpdir(), 'dream-out-')), '2026-11-17');
  dream({ memory: dir, out, sheet, date: '2026-11-17' });
  // The owner's entry changed after the proposal: refused, not overwritten.
  writeFileSync(join(dir, 'ask-in-file.md'), `${files['ask-in-file.md']}\nnew line\n`);
  const r = apply({ out, memory: dir, accept: ['cap-now.md', 'ask-in-file.md', 'luat-dang-hieu-luc.md', '../x.md', 'dup-a.md'], sheet });
  assert.deepEqual(r.applied, ['cap-now.md']);
  assert.deepEqual(r.refused.map(x => x.why), ['file gốc đã đổi sau đề xuất', 'không sửa mục trỏ luật', 'tên file không hợp lệ', 'không có trong đề xuất']);
  assert.match(readFileSync(join(dir, 'cap-now.md'), 'utf8'), /rules-checked/);
  assert.match(readFileSync(join(dir, 'ask-in-file.md'), 'utf8'), /new line/);
  // The rules sheet moved since the proposal: nothing is applied.
  const moved = apply({ out, memory: dir, accept: ['MEMORY.md'], sheet: `${sheet}\n` });
  assert.deepEqual(moved.applied, []);
  assert.equal(moved.refused[0].why, 'bảng luật đã đổi sau đề xuất');
});

test('dream: symlinks in the memory folder are skipped, the proposal cannot live inside it, old proposals expire', () => {
  const { dir } = store();
  const secret = join(mkdtempSync(join(tmpdir(), 'outside-')), 'secret.md');
  writeFileSync(secret, entry('secret', 'outside file', 'Codex cap 60.'));
  symlinkSync(secret, join(dir, 'link.md'));
  const out = join(mkdtempSync(join(tmpdir(), 'dream-out-')), '2026-11-17');
  dream({ memory: dir, out, sheet, date: '2026-11-17' });
  assert.equal(existsSync(join(out, 'memory', 'link.md')), false);
  assert.doesNotMatch(readFileSync(join(out, 'changes.json'), 'utf8'), /link\.md/);
  assert.throws(() => dream({ memory: dir, out: join(dir, 'proposal'), sheet, date: '2026-11-17' }), /outside the memory folder/);
  const root = mkdtempSync(join(tmpdir(), 'dream-root-'));
  for (const d of ['2026-10-01', '2026-11-10', 'keep-me']) mkdirSync(join(root, d));
  assert.deepEqual(prune(root, '2026-11-17'), ['2026-10-01']);
  assert.equal(existsSync(join(root, 'keep-me')), true);
});
