import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import * as lessons from './collab-lessons.mjs';
import { ciTestFiles, confirmClosed, lessonsLine, problems, readRegister, renderLessons, summarize, verify } from './collab-lessons.mjs';
import * as trust from './collab-trust.mjs';
import { asPosted } from './collab-test-post.mjs';

const sha = 'c'.repeat(40);
const N = 7;
// Since #456 a verdict counts only with a local receipt bound to its comment, as the scripted
// review path posts it.
const sealed = (verdict, createdAt) => asPosted(trust, { authorAssociation: 'OWNER', createdAt, body: `Review verdict: ${verdict} @ ${sha}\nReviewer: Codex\n${trust.verdictSeal({ head: sha, p2: 0, base: null, receipt: trust.signReceipt({ kind: 'verdict', pr: N, head: sha, base: null, result: verdict, p2: 0 }) })}` });
const approve = sealed('APPROVE', '2026-11-14T01:00:00Z');

function fixture() {
  const base = mkdtempSync(join(tmpdir(), 'lessons-test-'));
  mkdirSync(join(base, 'scripts'), { recursive: true });
  writeFileSync(join(base, 'scripts/x.test.mjs'), "test('retries a failed batch', () => {});\n// test('only a comment')\n");
  writeFileSync(join(base, 'scripts/x.mjs'), 'export const attempts = 3;\n');
  return base;
}
const done = extra => ({ id: 'L01', title: 'Thử lại lô lỗi', who: 'claude', due: '2026-11-15', status: 'done',
  test: { file: 'scripts/x.test.mjs', name: 'retries a failed batch' }, caller: { file: 'scripts/x.mjs', contains: 'attempts' }, closedBy: { pr: 7 }, ...extra });
const ci = new Set(['scripts/x.test.mjs']);

test('the real register is valid and every done lesson has its evidence in this checkout', () => {
  const reg = readRegister();
  assert.deepEqual(problems(reg), []);
  assert.ok(reg.lessons.length >= 12, 'the 12.11 agreement is carried over');
});

test('a lesson cannot be closed by editing the register', () => {
  const base = fixture();
  assert.deepEqual(problems({ lessons: [done()] }, { base, ciFiles: ci }), []);
  const cases = [
    [done({ test: undefined }), /without a regression test/],
    [done({ test: { file: 'scripts/missing.test.mjs', name: 'x' } }), /does not exist/],
    [done({ test: { file: 'scripts/x.test.mjs', name: 'only a comment' } }), /no test named/],
    [done({ caller: { file: 'scripts/x.mjs', contains: 'nowhere' } }), /does not contain/],
    [done({ caller: undefined }), /without a caller/],
    [done({ closedBy: undefined }), /without the PR/],
    [done({ due: undefined, status: 'open' }), /due date/],
    [done({ status: 'finished' }), /status must be/],
  ];
  for (const [lesson, pattern] of cases) assert.match(problems({ lessons: [lesson] }, { base, ciFiles: ci }).join('\n'), pattern);
  assert.match(problems({ lessons: [done()] }, { base, ciFiles: new Set() }).join('\n'), /not in pnpm collab:test/, 'a test CI never runs does not count');
  assert.match(problems({ lessons: [done(), done()] }, { base, ciFiles: ci }).join('\n'), /duplicate/);
});

test('only a PR merged into integration with a trusted Codex APPROVE confirms a lesson', () => {
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }), true);
  assert.equal(confirmClosed({ number: N, state: 'OPEN', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }), false, 'not merged');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'main', headRefOid: sha, comments: [approve] }), false, 'other base');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [{ ...approve, authorAssociation: 'NONE' }] }), false, 'untrusted commenter');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [{ ...approve, body: `Review verdict: APPROVE @ ${sha}` }] }), false, 'a hand-written verdict is not the Codex review');
  const unsigned = { ...approve, body: `Review verdict: APPROVE @ ${sha}\nReviewer: Codex\n<!-- la-lanh-agent codex-auto-review sha=${sha} -->` };
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [unsigned] }), false, 'an APPROVE without a receipt does not confirm');
  // Codex 13.11: an APPROVE of an older head, or one followed by REQUEST_CHANGES, does not close.
  const other = 'd'.repeat(40);
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: other, comments: [approve] }), false, 'APPROVE of another head');
  const later = sealed('REQUEST_CHANGES', '2026-11-14T02:00:00Z');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve, later] }), false, 'the last verdict counts');
});

test('overdue and unconfirmed lessons are reported, not hidden', () => {
  const dir = mkdtempSync(join(tmpdir(), 'lessons-cache-'));
  const reg = { lessons: [
    done(),
    { id: 'L02', title: 'a', who: 'claude', due: '2026-11-12', status: 'open' },
    { id: 'L03', title: 'b', who: 'claude', due: '2026-11-20', status: 'open' },
    { id: 'L04', title: 'c', who: 'owner', status: 'waiting-owner' },
  ] };
  let views = 0;
  const cachePath = join(dir, 'v.json');
  const notYet = verify(reg, { view: () => { views += 1; return { number: N, state: 'OPEN', baseRefName: 'collab/integration', headRefOid: sha, comments: [] }; }, cachePath });
  const s = summarize(reg, { today: '2026-11-14', verified: notYet });
  assert.deepEqual({ done: s.done, open: s.open, owner: s.owner, overdue: s.overdue, unconfirmed: s.unconfirmed }, { done: 0, open: 3, owner: 1, overdue: ['L02'], unconfirmed: ['L01'] });
  const line = renderLessons(s);
  assert.match(line, /0\/4 đã chạy thật/);
  assert.match(line, /\*\*1 quá hạn\*\* \(L02\)/);
  assert.match(line, /chưa có bằng chứng merge \+ Codex duyệt: L01/);
  const ok = verify(reg, { view: () => { views += 1; return { number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }; }, cachePath });
  assert.equal(summarize(reg, { today: '2026-11-14', verified: ok }).done, 1);
  verify(reg, { view: () => { views += 1; throw new Error('no network'); }, cachePath });
  assert.equal(views, 2, 'a confirmed PR is read from GitHub once');
});

test('the board line never throws and says when the register is broken', () => {
  assert.match(lessonsLine({ register: () => { throw new Error('bad json'); } }), /chưa đo được \(bad json\)/);
  assert.match(lessonsLine({ register: () => ({ lessons: [{ id: 'X' }] }), online: false }), /sổ đang sai 1 chỗ/);
  assert.match(lessonsLine({ online: false }), /^Lời hứa sửa quy trình: /);
});

test('owner 14.11: a lesson the owner declined is neither done nor open, and keeps its risk in view', () => {
  const declined = extra => ({ id: 'L05', title: 'Người gác cổng riêng', who: 'owner', status: 'declined-owner', declined: { on: '2026-11-14', reason: 'owner không cài', risk: 'Claude vẫn tự merge được' }, ...extra });
  assert.deepEqual(problems({ lessons: [declined()] }, { base: fixture(), ciFiles: ci }), []);
  assert.deepEqual(problems({ lessons: [declined({ declined: { on: '2026-11-14', reason: 'owner không cài' } })] }, { base: fixture(), ciFiles: ci }), ['lesson L05: declined-owner needs the risk that stays']);
  assert.equal(problems({ lessons: [declined({ declined: undefined })] }, { base: fixture(), ciFiles: ci }).length, 3);
  const reg = { lessons: [declined(), { id: 'L06', title: 'b', who: 'claude', due: '2026-11-20', status: 'open' }] };
  const s = summarize(reg, { today: '2026-11-21', verified: {} });
  assert.deepEqual({ open: s.open, done: s.done, declined: s.declined, overdue: s.overdue }, { open: 1, done: 0, declined: ['L05'], overdue: ['L06'] });
  assert.match(renderLessons(s), /1 owner quyết không làm, rủi ro vẫn còn \(L05\)/);
});

test('the lessons test itself runs in CI', () => {
  assert.ok(ciTestFiles().has('scripts/collab-lessons.test.mjs'));
});

// L08 (Codex 14.11): a Playwright spec counts only through the chain CI runs, and only unskipped.
test('#661: an API pytest is accepted as a lesson test only when CI runs it, by its exact function name', () => {
  const pkg = JSON.parse(readFileSync(join(lessons.root, 'package.json'), 'utf8'));
  assert.ok(lessons.ciTestFiles(pkg).has('apps/api/tests/scripts/test_persona_runs.py'), 'the real chain: check -> api:test -> pytest -> tests');
  assert.deepEqual(lessons.pytestCiFiles({ scripts: { ...pkg.scripts, check: 'pnpm collab:test' } }), [], 'not run by pnpm check: not counted');
  assert.deepEqual(lessons.pytestCiFiles({ scripts: { ...pkg.scripts, 'api:test': 'uv run --directory apps/api pytest tests/daily' } }), [], 'a filtered api:test proves nothing');
  const base = mkdtempSync(join(tmpdir(), 'lessons-py-'));
  mkdirSync(join(base, 'apps/api/tests/scripts'), { recursive: true });
  writeFileSync(join(base, 'apps/api/pyproject.toml'), '[tool.pytest.ini_options]\naddopts = "-q --strict-markers"\ntestpaths = ["tests"]\n');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), 'def test_sim_uses_production_rotation() -> None:\n    assert True\n');
  writeFileSync(join(base, 'apps/api/caller.py'), 'daily_variety_from=PRODUCTION\n');
  assert.deepEqual(lessons.pytestCiFiles(pkg, { base }), ['apps/api/tests/scripts/test_runs.py']);
  const lesson = name => ({ lessons: [{ id: 'L99', title: 't', who: 'claude', due: '2026-11-20', status: 'done',
    test: { file: 'apps/api/tests/scripts/test_runs.py', name }, caller: { file: 'apps/api/caller.py', contains: 'daily_variety_from' }, closedBy: { pr: 1 } }] });
  const ciFiles = lessons.ciTestFiles(pkg, { base });
  assert.deepEqual(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles }), []);
  assert.match(lessons.problems(lesson('test_sim_uses'), { base, ciFiles })[0], /no test named/, 'a prefix of a name is not the test');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), '# def test_sim_uses_production_rotation():\n');
  assert.match(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles })[0], /no test named/, 'a commented-out test does not count');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), '@pytest.mark.skip(reason="x")\ndef test_sim_uses_production_rotation() -> None:\n    pass\n');
  assert.match(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles })[0], /skipped or xfail/);
  writeFileSync(join(base, 'apps/api/pyproject.toml'), '[tool.pytest.ini_options]\naddopts = "-q --deselect tests/x"\ntestpaths = ["tests"]\n');
  assert.deepEqual(lessons.pytestCiFiles(pkg, { base }), [], 'a config that can drop tests proves nothing');
  // #667: a filter as the first option, and markers that span lines.
  for (const opts of ['"-k other_test"', '"-m slow"', '"-q -m=slow"', '["-k", "x"]']) {
    writeFileSync(join(base, 'apps/api/pyproject.toml'), `[tool.pytest.ini_options]\naddopts = ${opts}\ntestpaths = ["tests"]\n`);
    assert.deepEqual(lessons.pytestCiFiles(pkg, { base }), [], `addopts ${opts} can drop tests`);
  }
  writeFileSync(join(base, 'apps/api/pyproject.toml'), '[tool.pytest.ini_options]\naddopts = "-q --strict-markers"\ntestpaths = ["tests"]\n');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), '@pytest.mark.skipif(\n    not ENABLED,\n    reason="opt-in",\n)\ndef test_sim_uses_production_rotation() -> None:\n    pass\n');
  assert.match(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles })[0], /skipped or xfail/, 'a multiline skip decorator');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), 'pytestmark = [\n    pytest.mark.skipif(not ENABLED, reason="x"),\n]\n\n\ndef test_sim_uses_production_rotation() -> None:\n    pass\n');
  assert.match(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles })[0], /skipped or xfail/, 'a multiline module marker');
  writeFileSync(join(base, 'apps/api/tests/scripts/test_runs.py'), '@pytest.mark.parametrize(\n    "x", [1, 2],\n)\ndef test_sim_uses_production_rotation(x: int) -> None:\n    pass\n');
  assert.deepEqual(lessons.problems(lesson('test_sim_uses_production_rotation'), { base, ciFiles }), [], 'other multiline decorators are fine');
});

test('an e2e spec is accepted as a lesson test only when CI runs it, and rejected otherwise', () => {
  const pkg = JSON.parse(readFileSync(join(lessons.root, 'package.json'), 'utf8'));
  const files = lessons.ciTestFiles(pkg);
  assert.ok(files.has('apps/web/tests/e2e/kham-pha-portrait.spec.ts'), 'the real chain: check -> web:e2e -> playwright test -> tests/e2e');
  assert.ok(files.has('scripts/collab-lessons.test.mjs'));
  assert.deepEqual(lessons.playwrightCiFiles({ scripts: { ...pkg.scripts, check: 'pnpm collab:test' } }), [], 'not run by pnpm check: not counted');
  const base = mkdtempSync(join(tmpdir(), 'lessons-pw-'));
  mkdirSync(join(base, 'apps/web/tests/e2e'), { recursive: true });
  writeFileSync(join(base, 'apps/web/package.json'), JSON.stringify({ scripts: { e2e: 'playwright test' } }));
  writeFileSync(join(base, 'apps/web/playwright.config.ts'), 'export default { testDir: "./tests/e2e" };');
  writeFileSync(join(base, 'apps/web/tests/e2e/a.spec.ts'), 'test("works at 360px", async () => {});\n');
  assert.deepEqual(lessons.playwrightCiFiles(pkg, { base }), ['apps/web/tests/e2e/a.spec.ts']);
  writeFileSync(join(base, 'apps/web/playwright.config.ts'), 'export default { testDir: "./tests/e2e", testIgnore: "a.spec.ts" };');
  assert.deepEqual(lessons.playwrightCiFiles(pkg, { base }), [], 'a config that can drop specs proves nothing');
  writeFileSync(join(base, 'apps/web/playwright.config.ts'), 'export default { testDir: "./tests/e2e" };');
  const done = { lessons: [{ id: 'L99', title: 't', who: 'claude', due: '2026-11-20', status: 'done',
    test: { file: 'apps/web/tests/e2e/a.spec.ts', name: 'works at 360px' }, caller: { file: 'apps/web/playwright.config.ts', contains: 'tests/e2e' }, closedBy: { pr: 1 } }] };
  assert.deepEqual(lessons.problems(done, { base, ciFiles: lessons.ciTestFiles(pkg, { base }) }), []);
  const noE2e = { scripts: { ...pkg.scripts, check: 'pnpm collab:test' } };
  assert.match(lessons.problems(done, { base, ciFiles: lessons.ciTestFiles(noE2e, { base }) })[0], /CI never runs it/, 'a spec CI does not run is rejected');
  writeFileSync(join(base, 'apps/web/tests/e2e/a.spec.ts'), 'test.skip("works at 360px", async () => {});\ntest("works at 360px", async () => {});\n');
  assert.match(lessons.problems(done, { base, ciFiles: lessons.ciTestFiles(pkg, { base }) })[0], /skips, marks fixme or focuses a test/);
});
