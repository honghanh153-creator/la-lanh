// Three-agent dispatch 28.11.2026, part F (#948 AC6): Anti is review-only; a text patch is applied
// by the trusted host only inside an isolated fixture.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { antiRole, antiWrites, applyPatch, inScope, isFixtureRoot, parseEvents, parsePatch, pathReasons, publicPayload } from './collab-anti-patch.mjs';

const ev = list => list.map(e => JSON.stringify(e)).join('\n');
const block = (find, replace) => `<<<<<<< FIND\n${find}\n=======\n${replace}\n>>>>>>> REPLACE`;
const fixture = files => {
  const root = mkdtempSync(join(tmpdir(), 'anti-fixture-'));
  for (const [p, text] of Object.entries(files)) { mkdirSync(join(root, p, '..'), { recursive: true }); writeFileSync(join(root, p), text); }
  return root;
};
const read = (root, p) => readFileSync(join(root, p), 'utf8');

test('anti: review-only until its own PR turns writes on', () => {
  assert.equal(antiWrites, false);
  assert.equal(antiRole, 'review');
  const before = readFileSync('package.json', 'utf8');
  const r = applyPatch({ root: process.cwd(), patch: `*** Edit: package.json\n${block('"name"', '"nam"')}`, scope: ['package.json'] });
  assert.equal(r.ok, false);
  assert.match(r.reasons[0], /Anti chỉ review/);
  assert.equal(readFileSync('package.json', 'utf8'), before, 'the real checkout is never touched');
  assert.equal(isFixtureRoot(tmpdir()), false, 'the temp dir itself is not a fixture');
  assert.equal(isFixtureRoot(homedir()), false);
  const checkout = fixture({ 'scripts/a.mjs': 'a\n' });
  mkdirSync(join(checkout, '.git'));
  mkdirSync(join(checkout, 'sub'));
  assert.equal(isFixtureRoot(join(checkout, 'sub')), false, 'a git checkout under the temp dir is not a fixture');
  assert.match(applyPatch({ root: checkout, patch: `*** Edit: scripts/a.mjs\n${block('a', 'b')}`, scope: ['scripts/'] }).reasons[0], /Anti chỉ review/);
  assert.equal(read(checkout, 'scripts/a.mjs'), 'a\n');
  assert.equal(isFixtureRoot(fixture({})), true);
});

test('anti: a bundle with an unknown event, tool or field is refused whole', () => {
  const good = [
    { type: 'message', text: 'Mình đọc xong.' },
    { type: 'tool_call', name: 'read_file', args: { path: 'scripts/a.mjs' } },
    { type: 'tool_call', name: 'grep', args: { pattern: 'x', path: '.' } },
    { type: 'patch', text: `*** Edit: scripts/a.mjs\n${block('a', 'b')}` },
  ];
  const ok = parseEvents(ev(good));
  assert.equal(ok.ok, true);
  assert.equal(ok.events.length, 4);
  const cases = [
    [{ type: 'shell', text: 'rm -rf /' }, /loại sự kiện lạ shell/],
    [{ type: 'tool_call', name: 'write_file', args: { path: 'a' } }, /công cụ lạ write_file/],
    [{ type: 'tool_call', name: 'run_command', args: { path: 'a' } }, /công cụ lạ/],
    [{ type: 'tool_call', name: 'read_file', args: { path: '/etc/passwd' } }, /tuyệt đối/],
    [{ type: 'tool_call', name: 'read_file', args: { path: '../x' } }, /\.\./],
    [{ type: 'tool_call', name: 'read_file', args: { path: 'a', mode: 'w' } }, /args lạ mode/],
    [{ type: 'message', text: 'x', approve: true }, /trường lạ approve/],
    [{ type: 'verdict', text: 'APPROVE' }, /loại sự kiện lạ verdict/],
  ];
  for (const [bad, why] of cases) {
    const r = parseEvents(ev([...good, bad]));
    assert.equal(r.ok, false, JSON.stringify(bad));
    assert.deepEqual(r.events, [], 'nothing from a refused bundle is used');
    assert.match(r.reasons.join(' | '), why);
  }
  assert.equal(parseEvents(`${ev(good)}\n{not json`).ok, false);
  assert.equal(parseEvents('[1,2]').ok, false);
});

test('anti: paths outside the repo, in protected places or outside the scope are refused', () => {
  for (const p of ['/abs', '~/.claude/x', 'C:/x', 'a/../b', './a', 'a//b', 'a\\b', 'a\u0000b', '.git/config', 'x/.git/HEAD', '.github/workflows/ci.yml', '.claude/settings.json', '.env', 'apps/api/.env.local', 'node_modules/x/index.js', 'docs/operations/luat-dang-hieu-luc.md', '', 'a'.repeat(301)]) {
    assert.ok(pathReasons(p).length, `refused: ${JSON.stringify(p)}`);
  }
  for (const p of ['scripts/collab-anti-patch.mjs', 'docs/operations/x.md', 'apps/web/src/a.ts']) assert.deepEqual(pathReasons(p), []);
  assert.equal(inScope('scripts/a.mjs', ['scripts/']), true);
  assert.equal(inScope('scripts-x/a.mjs', ['scripts/']), false);
  assert.equal(inScope('scripts/a.mjs', ['scripts/a.mj']), false);
  assert.equal(inScope('scripts/a.mjs', []), false, 'an empty scope allows nothing');
});

test('anti: a malformed patch is refused', () => {
  const bad = [
    ['', /không có file/],
    ['*** Edit: a.txt\n', /không có khối/],
    [block('a', 'b'), /FIND trước/],
    ['*** Edit: a.txt\n<<<<<<< FIND\na\n=======\nb\n', /chưa đóng/],
    ['*** Edit: a.txt\nrm -rf /\n', /dòng lạ/],
    [`*** Edit: a.txt\n${block('a', 'b')}\n*** Edit: a.txt\n${block('c', 'd')}`, /lặp lại/],
    [`*** Edit: a.txt\n<<<<<<< FIND\n=======\nb\n>>>>>>> REPLACE`, /FIND rỗng/],
    [`*** Edit: a.txt\n<<<<<<< FIND\na\n<<<<<<< FIND\n=======\nb\n>>>>>>> REPLACE`, /FIND hỏng/],
  ];
  for (const [text, why] of bad) {
    const r = parsePatch(text);
    assert.equal(r.ok, false, text);
    assert.match(r.reasons.join(' | '), why);
  }
  const ok = parsePatch(`*** Edit: a.txt\n${block('x\ny', 'z')}\n${block('q', '')}`);
  assert.deepEqual(ok.files, [{ path: 'a.txt', edits: [{ find: 'x\ny', replace: 'z' }, { find: 'q', replace: '' }] }]);
});

test('anti fixture: the host applies a valid patch across files, all or nothing', () => {
  const root = fixture({ 'scripts/a.mjs': 'const a = 1;\nexport { a };\n', 'docs/b.md': '# B\nmột\n' });
  const patch = `*** Edit: scripts/a.mjs\n${block('const a = 1;', 'const a = 2;')}\n\n*** Edit: docs/b.md\n${block('một', 'hai $& $1')}`;
  const r = applyPatch({ root, patch, scope: ['scripts/', 'docs/b.md'] });
  assert.deepEqual(r, { ok: true, written: ['scripts/a.mjs', 'docs/b.md'], reasons: [] });
  assert.equal(read(root, 'scripts/a.mjs'), 'const a = 2;\nexport { a };\n');
  assert.equal(read(root, 'docs/b.md'), '# B\nhai $& $1\n', 'replacement text is literal');
  // One bad file refuses the whole patch: the good file stays as it was.
  const again = applyPatch({ root, patch: `*** Edit: scripts/a.mjs\n${block('const a = 2;', 'const a = 3;')}\n*** Edit: docs/b.md\n${block('không có', 'x')}`, scope: ['scripts/', 'docs/'] });
  assert.equal(again.ok, false);
  assert.match(again.reasons.join(' | '), /FIND gặp 0 lần/);
  assert.equal(read(root, 'scripts/a.mjs'), 'const a = 2;\nexport { a };\n');
});

test('anti fixture: an ambiguous FIND, a missing file, a symlink or a path outside the scope writes nothing', () => {
  const root = fixture({ 'scripts/a.mjs': 'x\nx\n', 'scripts/ok.mjs': 'y\n' });
  const outside = mkdtempSync(join(tmpdir(), 'anti-outside-'));
  writeFileSync(join(outside, 'secret.txt'), 'giữ nguyên\n');
  symlinkSync(outside, join(root, 'linked'));
  symlinkSync(join(outside, 'secret.txt'), join(root, 'scripts', 'file-link.txt'));
  const cases = [
    [`*** Edit: scripts/a.mjs\n${block('x', 'z')}`, /FIND gặp 2 lần/],
    [`*** Edit: scripts/none.mjs\n${block('x', 'z')}`, /không có file/],
    [`*** Edit: linked/secret.txt\n${block('giữ', 'đổi')}`, /symlink/],
    [`*** Edit: scripts/file-link.txt\n${block('giữ', 'đổi')}`, /symlink/],
    [`*** Edit: other/ok.mjs\n${block('y', 'z')}`, /ngoài phạm vi/],
    [`*** Edit: .github/x.yml\n${block('y', 'z')}`, /thư mục bị cấm/],
  ];
  for (const [patch, why] of cases) {
    const r = applyPatch({ root, patch: `*** Edit: scripts/ok.mjs\n${block('y', 'changed')}\n${patch}`, scope: ['scripts/', 'linked/', '.github/'] });
    assert.equal(r.ok, false, patch);
    assert.match(r.reasons.join(' | '), why);
    assert.equal(read(root, 'scripts/ok.mjs'), 'y\n', 'the valid file in the same patch is not written');
  }
  assert.equal(readFileSync(join(outside, 'secret.txt'), 'utf8'), 'giữ nguyên\n');
  assert.equal(applyPatch({ root, patch: `*** Edit: scripts/ok.mjs\n${block('y', 'z')}`, scope: [] }).ok, false, 'no scope, no write');
});

test('anti: only public tracked repo text goes to Anti; a refusal never echoes the match', () => {
  const tracked = new Set(['scripts/a.mjs', 'docs/b.md']);
  assert.deepEqual(publicPayload([{ path: 'scripts/a.mjs', text: 'export const a = 1; // noreply@anthropic.com, user@example.com' }], { tracked }), { ok: true, reasons: [] });
  const key = `ghp_${'A'.repeat(36)}`;
  const cases = [
    [{ path: 'notes/private.md', text: 'x' }, /không phải file đã track/],
    [{ path: '~/.claude/projects/x.jsonl', text: 'x' }, /tuyệt đối/],
    [{ path: 'scripts/a.mjs', text: `nhìn ${homedir()}/.cache` }, /đường dẫn máy riêng/],
    [{ path: 'scripts/a.mjs', text: 'xem /Users/someone/Documents/a' }, /đường dẫn máy riêng/],
    [{ path: 'docs/b.md', text: 'đọc ~/.claude/projects/abc' }, /file riêng của agent/],
    [{ path: 'docs/b.md', text: 'liên hệ ai.do@gmail.com' }, /email/],
    [{ path: 'docs/b.md', text: `token ${key}` }, /secret/],
    [{ path: 'docs/b.md', text: '-----BEGIN OPENSSH PRIVATE KEY-----' }, /secret/],
  ];
  for (const [item, why] of cases) {
    const r = publicPayload([{ path: 'scripts/a.mjs', text: 'ok' }, item], { tracked });
    assert.equal(r.ok, false, item.path);
    assert.match(r.reasons.join(' | '), why);
    assert.doesNotMatch(r.reasons.join(' | '), /gmail|ghp_|OPENSSH|someone/, 'the matched text is not repeated');
  }
  assert.equal(publicPayload([], { tracked }).ok, false);
});
