import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawn, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { installWrapper, installedPath, reportConsumers, rulesHookHealth, rulesHookWatch, skillRuleFindings, skillRuleHealth, verifyReportPrompts, verifySkillRules, verifyWrapper, wrapperHealth } from './collab-ops-wrapper.mjs';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
// Scheduled-task prompts as the owner's machine has them since 15.11 (both call their snapshot step).
function prompts({ owner = 'Run `/x/ops-run.sh snapshot 14` or `/x/ops-run.sh snapshot 22` for the run time.', retro = 'First run `/x/ops-run.sh snapshot retro`.' } = {}) {
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'prompts-')));
  for (const [task, text] of [['la-lanh-owner-report', owner], ['la-lanh-retro-2026-11-02', retro]]) {
    if (text === null) continue;
    mkdirSync(join(dir, task));
    writeFileSync(join(dir, task, 'SKILL.md'), `${text}\n`);
  }
  return dir;
}
const git = (cwd, ...args) => execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();

// A home with a real ops clone of a fake origin, a fake `node` that records its argv and cwd, and
// a Claude clone whose path has a space.
function world() {
  const base = realpathSync(mkdtempSync(join(tmpdir(), 'ops wrapper ')));
  const origin = join(base, 'origin.git');
  const seed = join(base, 'seed');
  git(base, 'init', '-q', '--bare', origin);
  git(base, 'init', '-q', '-b', 'collab/integration', seed);
  mkdirSync(join(seed, 'scripts'));
  cpSync(join(repoRoot, 'scripts', 'ops-run.sh'), join(seed, 'scripts', 'ops-run.sh'));
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'seed');
  git(seed, 'push', '-q', origin, 'collab/integration');
  const home = join(base, 'collab home');
  mkdirSync(home);
  git(base, 'clone', '-q', '-b', 'collab/integration', origin, join(home, 'ops'));
  const clone = join(base, 'New project', 'la-lanh-claude');
  mkdirSync(clone, { recursive: true });
  const bin = join(base, 'bin');
  mkdirSync(bin);
  const log = join(base, 'node.log');
  writeFileSync(join(bin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$PWD" "$*" >> "${log}"\nexit "\${FAKE_NODE_EXIT:-0}"\n`);
  chmodSync(join(bin, 'node'), 0o755);
  return { base, origin, home, clone, bin, log };
}

const run = (w, args, env = {}) => spawnSync('/bin/bash', [join(repoRoot, 'scripts', 'ops-run.sh'), ...args], {
  cwd: tmpdir(), encoding: 'utf8',
  env: { HOME: w.base, PATH: `${w.bin}:/usr/bin:/bin`, LA_LANH_COLLAB_HOME: w.home, LA_LANH_CLAUDE_CLONE: w.clone, ...env },
});
const calls = w => { try { return readFileSync(w.log, 'utf8').trim().split('\n').filter(Boolean); } catch { return []; } };

test('ops wrapper runs from another cwd with spaced paths and preserves failures', () => {
  const w = world();
  const report = run(w, ['report']);
  assert.equal(report.status, 0, report.stderr);
  const [reported] = calls(w);
  const runDir = new RegExp(`^${w.clone.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\|${join(w.home, 'ops-runs').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/report-\\d{14}-\\d+/scripts/collab-turn\\.mjs --report$`);
  assert.match(reported, runDir, 'runs in the Claude clone with the script of its own pinned copy, both paths with spaces');
  assert.equal(run(w, ['busy'], { FAKE_NODE_EXIT: '1' }).status, 1, 'a failing step keeps its exit status');
  assert.equal(run(w, ['beat', 'la-lanh-autopilot', 'done']).status, 0);
  assert.match(calls(w).at(-1), /collab-watchdog\.mjs --beat la-lanh-autopilot done$/);
  assert.equal(run(w, ['preflight', '42']).status, 0);
  assert.match(calls(w).at(-1), /collab-preflight\.mjs --pr 42$/);
  const before = calls(w).length;
  for (const bad of [[], ['rm'], ['beat'], ['beat', 'other', 'done'], ['beat', 'la-lanh-x', 'later'], ['preflight'], ['preflight', '0'], ['preflight', '-3'], ['preflight', '4;id']]) {
    assert.equal(run(w, bad).status, 2, `refused: ${bad.join(' ')}`);
  }
  assert.equal(calls(w).length, before, 'a refused step runs nothing');
  git(w.base, '--git-dir', w.origin, 'update-ref', '-d', 'refs/heads/collab/integration');
  const failed = run(w, ['status']);
  assert.notEqual(failed.status, 0, 'a failed fetch stops the step');
  assert.equal(calls(w).length, before, 'and nothing runs after it');
});

test('Codex #487: install reads the reviewed integration revision; a local edit or another revision is refused', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const reviewed = readFileSync(join(ops, 'scripts', 'ops-run.sh'), 'utf8');
  // A local edit in the ops clone is never installed.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho unreviewed\n`);
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /thay đổi chưa commit/);
  git(ops, 'checkout', '-q', '--', 'scripts/ops-run.sh');
  // A local commit that is not the reviewed revision is refused too.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho task commit\n`);
  git(ops, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-am', 'local');
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /không phải bản collab\/integration đã review/);
  git(ops, 'reset', '-q', '--hard', 'origin/collab/integration');
  // At the reviewed revision the installed bytes are the reviewed ones.
  installWrapper({ root: ops, home: w.home });
  assert.equal(readFileSync(installedPath(w.home), 'utf8'), reviewed);
  // A working-tree edit after install is drift against the reviewed revision, not a match.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho later edit\n`);
  writeFileSync(installedPath(w.home), `${reviewed}\necho later edit\n`);
  assert.match(verifyWrapper({ root: ops, home: w.home }).join(), /khác bản đã review/);
  // A newer reviewed revision on origin that the clone has not checked out is refused.
  git(ops, 'checkout', '-q', '--', 'scripts/ops-run.sh');
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'ops-run.sh'), `${reviewed}\n# newer\n`);
  git(seed, 'commit', '-q', '-am', 'newer');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /không phải bản collab\/integration đã review/);
});

test('L19: the wrapper exposes the shared slot snapshot step and refuses any other slot', () => {
  const w = world();
  for (const slot of ['08', '14', '22', 'retro']) {
    const res = run(w, ['snapshot', slot]);
    assert.equal(res.status, 0, res.stderr);
    const [cwd, cmd] = calls(w).at(-1).split('|');
    assert.equal(cwd, w.clone);
    assert.ok(cmd.startsWith(join(w.home, 'ops-runs', 'snapshot-')) && cmd.endsWith(`/scripts/collab-snapshot.mjs --slot ${slot}`), cmd);
  }
  const before = calls(w).length;
  for (const bad of [['snapshot'], ['snapshot', '12'], ['snapshot', '08;id'], ['snapshot', 'retro x']]) assert.equal(run(w, bad).status, 2, `refused: ${bad.join(' ')}`);
  assert.equal(calls(w).length, before, 'a refused slot runs nothing');
});

test('the wrapper installs only from the ops clone, atomically, and drift is reported', () => {
  const w = world();
  assert.throws(() => installWrapper({ root: repoRoot, home: w.home }), /chỉ cài từ clone ops/, 'an unreviewed checkout never installs');
  assert.match(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }).join(), /chưa cài/);
  assert.equal(installWrapper({ root: join(w.home, 'ops'), home: w.home }), installedPath(w.home));
  assert.deepEqual(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }), []);
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts() })[0], /✅/);
  writeFileSync(installedPath(w.home), '#!/bin/zsh\necho old\n');
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts() })[0], /⚠️.*khác bản đã review/);
});

// Codex auto-1 on #552: the consumers themselves are checked. A report prompt that stops calling the
// snapshot step (or is missing) turns the tick's health line into a warning.
test('L19: both scheduled reports must call their snapshot step; a disconnected one is reported', () => {
  assert.deepEqual(verifyReportPrompts({ dir: prompts() }), []);
  assert.deepEqual(reportConsumers.map(c => c.task), ['la-lanh-owner-report', 'la-lanh-retro-2026-11-02']);
  assert.match(verifyReportPrompts({ dir: prompts({ owner: 'Count merged PRs with gh pr list.' }) }).join(), /báo cáo owner 14\/22 không gọi bước bản chụp chung/);
  assert.match(verifyReportPrompts({ dir: prompts({ retro: 'Facts from tick logs.' }) }).join(), /retro 23:35 không gọi bước bản chụp chung/);
  assert.match(verifyReportPrompts({ dir: prompts({ retro: null }) }).join(), /không đọc được prompt retro/);
  // R5: the 08:00 slot is gone; a prompt that only takes the 08 snapshot no longer counts.
  assert.match(verifyReportPrompts({ dir: prompts({ owner: 'Run `/x/ops-run.sh snapshot 08`.' }) }).join(), /báo cáo owner 14\/22/);
  const w = world();
  installWrapper({ root: join(w.home, 'ops'), home: w.home });
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts({ owner: 'no snapshot' }) })[0], /⚠️.*báo cáo owner/);
});

// Owner 16.11.2026 (5-fix package item 3c, Codex C2): a report, status or snapshot never re-checks-out
// the shared ops tree a tick may be running from; each run uses its own pinned copy and removes it.
test('E: each ops run uses its own pinned copy of the reviewed commit and never moves the shared ops tree', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const first = git(ops, 'rev-parse', 'HEAD');
  // origin moves on after the ops tree was checked out
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'new.txt'), 'x\n');
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'next');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  const latest = git(seed, 'rev-parse', 'HEAD');
  // the fake node records which commit its script came from
  writeFileSync(join(w.bin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$(/usr/bin/git -C "$(dirname "$(dirname "$1")")" rev-parse HEAD)" "$1" >> "${w.log}"\n`);
  chmodSync(join(w.bin, 'node'), 0o755);
  // a leftover copy whose run is gone is swept; a copy whose run is alive is kept
  const runs = join(w.home, 'ops-runs');
  mkdirSync(runs, { recursive: true });
  for (const [name, pid] of [['report-dead-1', '999999999'], ['report-live-2', String(process.pid)], ['tick-orphan-3', '999999998']]) {
    git(ops, 'worktree', 'add', '-q', '--detach', join(runs, name), first);
    writeFileSync(join(runs, `.${name}.pid`), `${pid}\n`);
  }
  // Codex r1 on #603: the wrapper of tick-orphan-3 was killed, but its node still runs from the tree.
  const child = spawn(process.execPath, ['-e', 'setTimeout(() => {}, 60000)', join(runs, 'tick-orphan-3', 'scripts', 'collab-tick.mjs')], { stdio: 'ignore' });
  for (const step of [['report'], ['status'], ['snapshot', '14']]) {
    const out = run(w, step);
    assert.equal(out.status, 0, out.stderr);
  }
  const lines = calls(w);
  assert.equal(lines.length, 3);
  for (const line of lines) assert.match(line, new RegExp(`^${latest}\\|${runs.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/(report|status|snapshot)-\\d{14}-\\d+/scripts/`), 'the run used a fresh copy at the latest reviewed commit');
  assert.equal(git(ops, 'rev-parse', 'HEAD'), first, 'the shared ops tree was not moved');
  assert.deepEqual(readdirSync(runs).filter(n => !n.startsWith('.')).sort(), ['report-live-2', 'tick-orphan-3'], 'each run removed its copy; the dead leftover was swept; a live run and a tree a live process still uses were kept');
  assert.ok(!existsSync(join(runs, '.report-dead-1.pid')));
  child.kill('SIGKILL');
  for (let i = 0; i < 50 && child.exitCode === null && child.signalCode === null; i++) execFileSync('/bin/sleep', ['0.1']);
  assert.equal(run(w, ['status']).status, 0);
  assert.deepEqual(readdirSync(runs).filter(n => !n.startsWith('.')), ['report-live-2'], 'once nothing uses the orphaned tree it is swept');
});

test('E: the scheduled tick runs from its own pinned copy and keeps the shared tree current for the hooks', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'next.txt'), 'y\n');
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'next');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  const latest = git(seed, 'rev-parse', 'HEAD');
  const localBin = join(w.base, '.local', 'bin');
  mkdirSync(localBin, { recursive: true });
  writeFileSync(join(localBin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$(/usr/bin/git -C "$(dirname "$(dirname "$1")")" rev-parse HEAD)" "$1" >> "${w.log}"\n`);
  chmodSync(join(localBin, 'node'), 0o755);
  const out = spawnSync('/bin/bash', [join(repoRoot, 'scripts', 'collab-cron.sh')], { cwd: tmpdir(), encoding: 'utf8', env: { HOME: w.base, LA_LANH_COLLAB_HOME: w.home, PATH: '/usr/bin:/bin' } });
  assert.equal(out.status, 0, out.stderr + readFileSync(join(w.home, 'logs', readdirSync(join(w.home, 'logs'))[0]), 'utf8'));
  const [line] = calls(w);
  assert.match(line, new RegExp(`^${latest}\\|${join(w.home, 'ops-runs').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/tick-\\d{14}-\\d+/scripts/collab-tick\\.mjs$`));
  assert.equal(git(ops, 'rev-parse', 'HEAD'), latest, 'the shared tree the hooks read is current');
  assert.deepEqual(readdirSync(join(w.home, 'ops-runs')).filter(n => !n.startsWith('.')), [], 'the tick removed its copy');
});

// Codex r2 on #603: when only the wrapper ends (its EXIT trap runs), a child it started may still run
// from the tree; the tree stays until nothing names it, then a later sweep removes it.
test('E: a run tree outlives its wrapper while a child still uses it, and is swept afterwards', () => {
  const w = world();
  const runs = join(w.home, 'ops-runs');
  const holderPid = join(w.base, 'holder.pid');
  // The fake node leaves a child that keeps naming its script inside the tree, then returns.
  // The child is fully started before the fake node returns: on Linux a process caught mid-exec shows an
  // empty command line for a moment, which is a test race, not the case under test (CI on #628).
  // #641 (17.11): the readiness wait now uses the script's own test (pgrep -f on the tree path) instead
  // of `ps | grep perl`, the holder is the real node binary, and a failure prints what pgrep and ps saw.
  const seen = join(w.base, 'holder.seen');
  // Same escaping as ops-run.sh, so the wait and the script look for the same thing.
  writeFileSync(join(w.bin, 'node'), [
    '#!/bin/bash',
    `"${process.execPath}" -e 'setTimeout(() => {}, 60000)' "$1" </dev/null >/dev/null 2>&1 &`,
    'h=$!',
    `echo $h > "${holderPid}"`,
    String.raw`pat="$(printf '%s' "$(dirname "$(dirname "$1")")" | sed 's/[][\\.^$*+?(){}|]/\\&/g')"`,
    String.raw`for i in $(seq 1 100); do /usr/bin/pgrep -f -- "$pat" | grep -qx "$h" && break; sleep 0.1; done`,
    String.raw`{ echo "pattern: $pat"; echo "pgrep: $(/usr/bin/pgrep -f -- "$pat" | tr '\n' ' ')"; ps -o pid=,args= -p $h; } > "SEEN" 2>&1`.replace('SEEN', seen),
    '',
  ].join('\n'));
  chmodSync(join(w.bin, 'node'), 0o755);
  assert.equal(run(w, ['report']).status, 0);
  const left = readdirSync(runs).filter(n => !n.startsWith('.'));
  const saw = () => { try { return readFileSync(seen, 'utf8'); } catch { return 'no holder record'; } };
  assert.equal(left.length, 1, `the wrapper exited but its child still uses the tree: it stays. Holder: ${saw()}`);
  assert.match(left[0], /^report-\d{14}-\d+$/);
  const pid = Number(readFileSync(holderPid, 'utf8'));
  process.kill(pid, 'SIGKILL');
  for (let i = 0; i < 50; i++) { try { process.kill(pid, 0); execFileSync('/bin/sleep', ['0.1']); } catch { break; } }
  writeFileSync(join(w.bin, 'node'), '#!/bin/bash\nexit 0\n');
  assert.equal(run(w, ['status']).status, 0);
  assert.deepEqual(readdirSync(runs).filter(n => !n.startsWith('.')), [], 'once nothing names it, the next run sweeps it');
});

// One rule set for every scheduled task (owner 15–16.11; review of 16.11).
test('scheduled-task prompts are checked against the code: no PR quota, the 80 cap, 06:50 start, 23:35 stop', () => {
  const stale = [
    '1. **Plan at least 20 PRs.** Each must be small.',
    '2. **Before 08:00 (auto-start since 14.11.2026), open the first 8 or more planned PRs**.',
    '- Stay within 60 Codex runs a day.',
    '- Do not start new work after 23:00.',
    'description: open only what fits WIP 1+1; loop auto-starts 08:00',
  ].join('\n');
  const found = skillRuleFindings(stale);
  assert.ok(found.some(f => /chỉ tiêu số PR \(dòng 1\)/.test(f)), found.join(' | '));
  assert.ok(found.some(f => /chỉ tiêu số PR \(dòng 2\)/.test(f)));
  assert.ok(found.some(f => /trần Codex 60, code là 80 \(dòng 3\)/.test(f)));
  assert.ok(found.some(f => /dừng nhận việc lúc 23:00, code là 23:35 \(dòng 4\)/.test(f)));
  assert.ok(found.some(f => /giờ tự chạy 08:00, code là 06:50 \(dòng 2\)/.test(f)));
  assert.ok(found.some(f => /giờ tự chạy 08:00, code là 06:50 \(dòng 5\)/.test(f)));
  const clean = [
    'You are preparing the day. (Old rule, superseded 12.11: "by 10:00 the plan must cover at least 20 PRs".)',
    '- The "20 PR/ngày" target is retired.',
    '1. **Plan 3–5 work items**; open only what fits WIP 1+1.',
    '- Stay within 80 Codex runs a day.',
    '- Do not start new work from 23:35.',
    'the loop runs as soon as the 06:50 plan is posted; auto-start 06:50.',
    '- Owner rules: docs/operations/luat-dang-hieu-luc.md (R1…).',
    'description: 2 lần/ngày (14:00, 22:00); owner 16.11 bỏ bản 08:00',
  ].join('\n');
  assert.deepEqual(skillRuleFindings(clean), [], 'retired mentions and current rules pass');
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'skills-')));
  for (const [task, text] of [['la-lanh-morning-prep', stale], ['la-lanh-autopilot', clean], ['other-task', stale]]) { mkdirSync(join(dir, task)); writeFileSync(join(dir, task, 'SKILL.md'), `${text}\n`); }
  const bad = verifySkillRules({ dir });
  assert.ok(bad.length >= 6 && bad.every(b => b.startsWith('la-lanh-morning-prep: ')), 'only the la-lanh tasks are read, and each finding names its task');
  assert.match(skillRuleHealth({ prompts: dir })[0], /^- ⚠️ prompt tác vụ hẹn giờ khác luật trong code: la-lanh-morning-prep: /);
  const ok = realpathSync(mkdtempSync(join(tmpdir(), 'skills-ok-')));
  mkdirSync(join(ok, 'la-lanh-autopilot')); writeFileSync(join(ok, 'la-lanh-autopilot', 'SKILL.md'), `${clean}\n`);
  assert.match(skillRuleHealth({ prompts: ok })[0], /^- ✅ /);
});

// One rules source (owner 16.11, R5): a dropped report slot still scheduled is caught, and every
// la-lanh prompt must point to the rules sheet instead of restating rules.
test('scheduled-task prompts: a dropped report slot is caught and every prompt points to the rules sheet', () => {
  const found = skillRuleFindings(['- 08:00: "**Báo cáo đầu ngày DD.MM**"', 'Send the owner report at 08:00 every day.', '- 14:00: "**Báo cáo 14:00**"'].join('\n'), { retiredSlots: ['08:00'] });
  assert.deepEqual(found, ['còn giờ báo cáo 08:00 đã bỏ (R5) (dòng 1)', 'còn giờ báo cáo 08:00 đã bỏ (R5) (dòng 2)']);
  // The default list comes from the rules sheet of this checkout.
  assert.ok(skillRuleFindings('- 08:00: "**Báo cáo đầu ngày**"').some(f => /08:00 đã bỏ/.test(f)));
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'skills-ptr-')));
  mkdirSync(join(dir, 'la-lanh-autopilot'));
  writeFileSync(join(dir, 'la-lanh-autopilot', 'SKILL.md'), 'Plan 3–5 work items.\n');
  assert.deepEqual(verifySkillRules({ dir }), ['la-lanh-autopilot: thiếu dòng trỏ tới bảng luật (docs/operations/luat-dang-hieu-luc.md)']);
  writeFileSync(join(dir, 'la-lanh-autopilot', 'SKILL.md'), 'Rules: /x/ops/docs/operations/luat-dang-hieu-luc.md\nPlan 3–5 work items.\n');
  assert.deepEqual(verifySkillRules({ dir }), []);
});

test('L37: the tick opens one alert a day while the rules hook is broken and closes it when fixed', () => {
  const marker = join(realpathSync(mkdtempSync(join(tmpdir(), 'rules-watch-'))), 'm.json');
  const sent = [];
  const closed = [];
  const watch = (bad, today) => rulesHookWatch({ verify: () => bad, alert: t => sent.push(t), resolve: t => closed.push(t), marker, today });
  assert.equal(watch(['hook PreToolUse của luật owner thiếu hoặc khác bản chuẩn'], 'd1').status, 'alerted');
  assert.match(sent[0], /^Hook luật owner \(L37.*PreToolUse.*collab-rules-hook\.mjs --install$/);
  assert.equal(watch(['x'], 'd1').status, 'already-alerted');
  assert.equal(watch(['x'], 'd2').status, 'alerted');
  assert.equal(watch([], 'd2').status, 'resolved');
  assert.deepEqual(closed, ['hook luật owner đã khớp bản chuẩn']);
  assert.equal(watch([], 'd3').status, 'ok');
  assert.match(rulesHookHealth({ verify: () => ['selftest trượt'] })[0], /^- ⚠️ hook luật owner \(L37\): selftest trượt/);
  assert.match(rulesHookHealth({ verify: () => [] })[0], /^- ✅ hook luật owner/);
});

test('L37: the production tick watchdog calls the rules-hook watch with its ops-alert subject', async () => {
  const { runTick } = await import('./collab-tick.mjs');
  let seen = null;
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gateWatch: () => ({ status: 'ok' }), rulesWatch: args => { seen = args; return { status: 'ok' }; } });
  given.watchdog();
  assert.ok(seen && typeof seen.alert === 'function' && typeof seen.resolve === 'function' && /^\d{4}-\d{2}-\d{2}$/.test(seen.today));
});

// Fix-forward #620: mixed lines, Vietnamese quotas and unreadable prompts.
test('#620: a retired clause hides only itself; a Vietnamese quota is caught; an unreadable prompt is unchecked', () => {
  assert.deepEqual(skillRuleFindings('The old rule is retired; stay within 60 Codex runs a day.'), ['trần Codex 60, code là 80 (dòng 1)']);
  assert.deepEqual(skillRuleFindings('Lập kế hoạch ít nhất 20 PRs mỗi ngày.'), ['còn chỉ tiêu số PR (dòng 1)']);
  assert.deepEqual(skillRuleFindings('Luật cũ "ít nhất 20 PR" đã bỏ; nay 3–5 việc.'), []);
  assert.deepEqual(skillRuleFindings('3c. RETIRED: no PR count. The old text follows for history only — do NOT apply it: (at least 16 PRs a day, Codex cap 32).'), [], 'a quoted old rule is history');
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'skills-unread-')));
  mkdirSync(join(dir, 'la-lanh-autopilot'));
  mkdirSync(join(dir, 'la-lanh-autopilot', 'SKILL.md'));
  const bad = verifySkillRules({ dir });
  assert.equal(bad.length, 1);
  assert.match(bad[0], /^la-lanh-autopilot: không đọc được prompt \(EISDIR\), chưa kiểm$/);
  assert.match(skillRuleHealth({ prompts: dir })[0], /^- ⚠️ /);
});
