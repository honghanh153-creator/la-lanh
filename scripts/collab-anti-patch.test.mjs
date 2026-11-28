// Three-agent dispatch 28.11.2026, part F (#948 AC6): Anti is review-only; a text patch is applied
// by the trusted host only inside an isolated fixture or a job worktree it made (Codex r1 on #955).
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { antiRole, applyPatch, buildSnapshot, fsIo, inScope, isFixtureRoot, parseEvents, parsePatch, pathReasons, publicPayload, trackedFiles, trustedGit } from './collab-anti-patch.mjs';

const ev = list => list.map(e => JSON.stringify(e)).join('\n');
const block = (find, replace) => `<<<<<<< FIND\n${find}\n=======\n${replace}\n>>>>>>> REPLACE`;
const fixture = files => {
  const root = mkdtempSync(join(tmpdir(), 'anti-fixture-'));
  for (const [p, text] of Object.entries(files)) { mkdirSync(join(root, p, '..'), { recursive: true }); writeFileSync(join(root, p), text); }
  return root;
};
const read = (root, p) => readFileSync(join(root, p), 'utf8');

test('anti: review-only; the host writes only in a temp fixture or an Anti job worktree', () => {
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
  for (const p of ['/abs', '~/.claude/x', 'C:/x', 'a/../b', './a', 'a//b', 'a\\b', 'a\u0000b', '.git/config', 'x/.git/HEAD', '.github/workflows/ci.yml', '.claude/settings.json', '.env', 'apps/api/.env.local', 'node_modules/x/index.js', 'docs/operations/luat-dang-hieu-luc.md', '', 'a'.repeat(301),
    // Codex r1 on #955: case and Unicode aliases, protected ancestors, tool config and gate files.
    '.GitHub/workflows/ci.yml', 'X/.GIT/config', 'apps/.ENV', 'apps/.env.d/x.txt', '.Claude/settings.json', 'apps/.vscode/settings.json', 'package.json', 'apps/web/package.json', 'AGENTS.md', 'apps/CLAUDE.md',
    'scripts/collab-anti-patch.mjs', 'Scripts/Collab-trust.mjs', 'scripts/codex-review.mjs', 'scripts/lessons/L90.json', 'scripts/private-guard.mjs', 'docs/operations/x.md', 'DOCS/Operations/x.md', 'docs/ca\u0301.md']) {
    assert.ok(pathReasons(p).length, `refused: ${JSON.stringify(p)}`);
  }
  for (const p of ['apps/web/src/a.ts', 'docs/product/x.md', 'scripts/check-copy.mjs', 'docs/c\u00e1.md']) assert.deepEqual(pathReasons(p), [], p);
  assert.equal(inScope('Docs/A.md', ['docs/']), true, 'scope is matched on the folded key');
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
    [`*** Edit: docs/A.txt\n${block('a', 'b')}\n*** Edit: docs/a.txt\n${block('c', 'd')}`, /lặp lại/],
    [`*** Edit: docs/c\u00e1.md\n${block('a', 'b')}\n*** Edit: docs/ca\u0301.md\n${block('c', 'd')}`, /lặp lại/],
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
    [`*** Edit: Scripts/A.mjs\n${block('x', 'z')}`, /chữ hoa\/thường/],
    [`*** Edit: Scripts/OK.mjs\n${block('y', 'z')}`, /lặp lại/],
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

// Codex r1 on #955, P2: a failure part way must leave no file half written.
const failingIo = ({ renameAt = -1, restoreFails = false, changeAfterStage = null } = {}) => {
  let renames = 0;
  let staged = false;
  return {
    ...fsIo,
    writeFileSync(p, data, opts) {
      if (restoreFails && String(p).endsWith('.back')) throw new Error('disk full');
      fsIo.writeFileSync(p, data, opts);
      if (changeAfterStage && !staged && String(p).endsWith('.tmp')) { staged = true; fsIo.writeFileSync(changeAfterStage, 'đổi bởi người khác\n'); }
    },
    renameSync(a, b) {
      if (!String(a).endsWith('.back') && renames++ === renameAt) throw new Error('rename failed');
      fsIo.renameSync(a, b);
    },
  };
};
const noTemps = root => readdirSync(join(root, 'scripts')).filter(n => n.startsWith('.anti-'));

test('anti fixture: a rename failing part way puts every file back', () => {
  const root = fixture({ 'scripts/a.mjs': 'a\n', 'scripts/b.mjs': 'b\n', 'scripts/c.mjs': 'c\n' });
  const patch = ['a', 'b', 'c'].map(x => `*** Edit: scripts/${x}.mjs\n${block(x, `${x}2`)}`).join('\n');
  const r = applyPatch({ root, patch, scope: ['scripts/'], io: failingIo({ renameAt: 1 }) });
  assert.equal(r.ok, false);
  assert.equal(r.rolledBack, true);
  assert.deepEqual(['a', 'b', 'c'].map(x => read(root, `scripts/${x}.mjs`)), ['a\n', 'b\n', 'c\n']);
  assert.deepEqual(noTemps(root), [], 'no staged or backup file is left');
});

test('anti fixture: a failed restore marks the checkout invalid', () => {
  const root = fixture({ 'scripts/a.mjs': 'a\n', 'scripts/b.mjs': 'b\n' });
  const patch = ['a', 'b'].map(x => `*** Edit: scripts/${x}.mjs\n${block(x, `${x}2`)}`).join('\n');
  const r = applyPatch({ root, patch, scope: ['scripts/'], io: failingIo({ renameAt: 1, restoreFails: true }) });
  assert.equal(r.ok, false);
  assert.equal(r.invalid, true);
  assert.match(r.reasons.join(' '), /không được dùng nữa/);
});

test('anti fixture: a file changed after the check is not overwritten', () => {
  const root = fixture({ 'scripts/a.mjs': 'a\n', 'scripts/b.mjs': 'b\n' });
  const patch = ['a', 'b'].map(x => `*** Edit: scripts/${x}.mjs\n${block(x, `${x}2`)}`).join('\n');
  const r = applyPatch({ root, patch, scope: ['scripts/'], io: failingIo({ changeAfterStage: join(root, 'scripts/b.mjs') }) });
  assert.equal(r.ok, false);
  assert.match(r.reasons.join(' '), /đổi trong lúc áp/);
  assert.equal(read(root, 'scripts/a.mjs'), 'a\n');
  assert.equal(read(root, 'scripts/b.mjs'), 'đổi bởi người khác\n');
  assert.deepEqual(noTemps(root), []);
});

test('anti fixture: a file with invalid UTF-8 is refused', () => {
  const root = fixture({ 'scripts/ok.mjs': 'y\n' });
  writeFileSync(join(root, 'scripts/bin.mjs'), Buffer.from([0x79, 0xff, 0x0a]));
  const r = applyPatch({ root, patch: `*** Edit: scripts/bin.mjs\n${block('y', 'z')}`, scope: ['scripts/'] });
  assert.equal(r.ok, false);
  assert.match(r.reasons.join(' '), /UTF-8/);
});

// A synthetic repo whose own config tries to run code: fsmonitor and hooks write a marker file.
const plainGit = (cwd, args, env = {}) => execFileSync('/usr/bin/git', args, { cwd, env: { PATH: '/usr/bin:/bin', HOME: cwd, GIT_CONFIG_NOSYSTEM: '1', ...env }, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
const synthRepo = files => {
  const root = mkdtempSync(join(tmpdir(), 'anti-repo-'));
  const g = args => plainGit(root, ['-c', 'user.name=t', '-c', 'user.email=t@example.com', '-c', 'commit.gpgsign=false', ...args]);
  g(['init', '-q', '-b', 'main']);
  for (const [p, text] of Object.entries(files)) { mkdirSync(join(root, p, '..'), { recursive: true }); writeFileSync(join(root, p), text); }
  g(['add', '-A']);
  g(['commit', '-q', '-m', 'base']);
  return root;
};

test('anti: trusted git never runs a repo fsmonitor or hook, and ignores an inherited GIT_DIR', () => {
  const root = synthRepo({ 'docs/a.md': 'a\n' });
  const marker = join(root, '..', `${root.split('/').pop()}-ran`);
  const hook = join(root, 'evil.sh');
  writeFileSync(hook, `#!/bin/sh\necho ran >> "${marker}"\nexit 1\n`, { mode: 0o755 });
  mkdirSync(join(root, 'hooks'));
  writeFileSync(join(root, 'hooks', 'pre-commit'), `#!/bin/sh\necho ran >> "${marker}"\nexit 1\n`, { mode: 0o755 });
  plainGit(root, ['config', 'core.fsmonitor', hook]);
  plainGit(root, ['config', 'core.hooksPath', join(root, 'hooks')]);
  // Control: plain git does run the repo fsmonitor.
  try { plainGit(root, ['status', '--porcelain']); } catch { /* the hook exits 1 */ }
  assert.ok(existsSync(marker), 'control: the repo fsmonitor runs under plain git');
  fsIo.unlinkSync(marker);
  const other = synthRepo({ 'x.md': 'x\n' });
  const saved = process.env.GIT_DIR;
  process.env.GIT_DIR = join(other, '.git');
  try {
    trustedGit(['status', '--porcelain'], { cwd: root });
    assert.deepEqual([...trackedFiles(root)], ['docs/a.md'], 'the index of this repo, not GIT_DIR');
    trustedGit(['-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '--allow-empty', '-m', 'x'], { cwd: root });
  } finally { if (saved === undefined) delete process.env.GIT_DIR; else process.env.GIT_DIR = saved; }
  assert.equal(existsSync(marker), false, 'no fsmonitor or hook ran under trusted git');
});

test('anti: the host builds the snapshot from its own index; anything odd refuses all', () => {
  const root = synthRepo({ 'docs/a.md': 'xin chào\n', 'docs/b.md': 'b\n', 'apps/web/x.ts': 'export {};\n', 'docs/operations/r.md': 'r\n' });
  const ok = buildSnapshot({ root, allow: ['docs/a.md', 'apps/'] });
  assert.equal(ok.ok, true, ok.reasons.join(' | '));
  assert.deepEqual(ok.items.map(i => i.path).sort(), ['apps/web/x.ts', 'docs/a.md']);
  const g = args => plainGit(root, ['-c', 'user.name=t', '-c', 'user.email=t@example.com', ...args]);
  const cases = [
    [() => writeFileSync(join(root, 'docs/b.md'), 'sửa chưa add\n'), ['docs/b.md'], /khác bản trong git index/],
    [() => { writeFileSync(join(root, 'docs/c.md'), 'liên hệ ai.do@gmail.com\n'); g(['add', 'docs/c.md']); }, ['docs/c.md'], /email/],
    [() => { writeFileSync(join(root, 'docs/n.md'), Buffer.from('a\0b\n')); g(['add', 'docs/n.md']); }, ['docs/n.md'], /nhị phân/],
    [() => { writeFileSync(join(root, 'docs/u.md'), Buffer.from([0x61, 0xff, 0x0a])); g(['add', 'docs/u.md']); }, ['docs/u.md'], /UTF-8/],
    [() => { writeFileSync(join(root, 'docs/big.md'), 'x'.repeat(70000)); g(['add', 'docs/big.md']); }, ['docs/big.md'], /quá 60000 byte/],
    [() => { symlinkSync('a.md', join(root, 'docs/l.md')); g(['add', 'docs/l.md']); }, ['docs/l.md'], /symlink/],
    [() => {}, ['docs/operations/'], /luật và quy trình/],
    [() => {}, ['nothing/'], /không có file đã track/],
    [() => {}, [], /chưa có phạm vi/],
  ];
  for (const [setup, allow, why] of cases) {
    setup();
    const r = buildSnapshot({ root, allow });
    assert.equal(r.ok, false, String(allow));
    assert.deepEqual(r.items, []);
    assert.match(r.reasons.join(' | '), why);
    assert.doesNotMatch(r.reasons.join(' '), /gmail/, 'a refusal never echoes the match');
  }
  assert.equal(buildSnapshot({ root: join(root, 'docs'), allow: ['docs/'] }).ok, false, 'only the checkout root');
});

test('anti: names from Object.prototype are unknown, never a crash (Anti r1 on #955)', () => {
  for (const name of ['constructor', 'toString', '__proto__', 'hasOwnProperty']) {
    const a = parseEvents(JSON.stringify({ type: name, text: 'x' }));
    assert.equal(a.ok, false); assert.match(a.reasons.join(' '), /loại sự kiện lạ/);
    const b = parseEvents(JSON.stringify({ type: 'tool_call', name, args: { path: 'a.txt' } }));
    assert.equal(b.ok, false); assert.match(b.reasons.join(' '), /công cụ lạ/);
  }
  assert.equal(parseEvents(JSON.stringify({ type: 'tool_call', name: 7, args: {} })).ok, false);
  assert.deepEqual(publicPayload([]), { ok: false, reasons: ['không có gì để gửi'] }, 'no options object is fine');
});

test('anti: applyPatch takes only patch text, so an empty FIND can never spin (Anti r1 on #955)', () => {
  const root = fixture({ 'scripts/a.mjs': 'old\n' });
  const t0 = Date.now();
  const r = applyPatch({ root, patch: { ok: true, files: [{ path: 'scripts/a.mjs', edits: [{ find: '', replace: 'x' }] }], reasons: [] }, scope: ['scripts/'] });
  assert.equal(r.ok, false); assert.deepEqual(r.reasons, ['patch phải là văn bản']);
  assert.ok(Date.now() - t0 < 500, 'returns at once');
  assert.equal(readFileSync(join(root, 'scripts/a.mjs'), 'utf8'), 'old\n');
  const empty = parsePatch(`*** Edit: scripts/a.mjs\n${block('', 'x')}`);
  assert.equal(empty.ok, false); assert.match(empty.reasons.join(' '), /FIND rỗng/);
});

test('anti: more private markers stay on the machine (Anti r1 on #955)', () => {
  const tracked = new Set(['a.txt']);
  const cases = [
    ['/home/someone/notes', /đường dẫn máy riêng/],
    ['C:\\Users\\someone\\notes', /đường dẫn máy riêng/],
    ['~/.codex/auth.json', /file riêng của agent/],
    ['~/.gemini/settings', /file riêng của agent/],
    [`AIza${'A'.repeat(35)}`, /chuỗi giống secret/],
    [`gho_${'a'.repeat(30)}`, /chuỗi giống secret/],
    ['https://user:secret@example.org/x', /URL có mật khẩu/],
  ];
  for (const [text, why] of cases) {
    const r = publicPayload([{ path: 'a.txt', text }], { tracked });
    assert.equal(r.ok, false, text.slice(0, 12)); assert.match(r.reasons.join(' '), why);
    assert.ok(!r.reasons.join(' ').includes(text), 'never echoes the match');
  }
  assert.equal(publicPayload([{ path: 'a.txt', text: 'https://example.org/x and /usr/bin/git' }], { tracked }).ok, true);
});
