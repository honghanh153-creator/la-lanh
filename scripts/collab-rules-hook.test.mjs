import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { appendFileSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { changedIds, fitContext, handle, inScope, installRulesHook, metrics, r3Reason, recordRepeat, rulesHooks, verifyRulesHook } from './collab-rules-hook.mjs';
import { sheetPath } from './collab-rules.mjs';

const script = join(dirname(fileURLToPath(import.meta.url)), 'collab-rules-hook.mjs');
const sheet = readFileSync(sheetPath(), 'utf8');

// A fresh state home with the sheet where the ops clone keeps it, and a la-lanh checkout to work in.
function fixture() {
  const home = mkdtempSync(join(tmpdir(), 'rules-hook-'));
  mkdirSync(join(home, 'ops', 'docs', 'operations'), { recursive: true });
  writeFileSync(join(home, 'ops', 'docs', 'operations', 'luat-dang-hieu-luc.md'), sheet);
  const repo = join(home, 'Documents', 'la-lanh-claude');
  mkdirSync(repo, { recursive: true });
  return { home, repo, publish: text => writeFileSync(join(home, 'ops', 'docs', 'operations', 'luat-dang-hieu-luc.md'), text) };
}
// The hook as Claude Code runs it: a real process, JSON on stdin, JSON (or nothing) on stdout.
function run(home, input) {
  const env = { ...process.env, LA_LANH_COLLAB_HOME: home };
  delete env.LA_LANH_RULES_SHEET;
  const r = spawnSync(process.execPath, [script], { input: JSON.stringify(input), env, encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout ? JSON.parse(r.stdout) : null;
}
const ctx = out => out?.hookSpecificOutput?.additionalContext ?? null;
const R9 = sheet.split('\n').find(l => l.startsWith('| R9 |'));

test('rules hook: a long session gets a changed rule on its next prompt or tool call, and only once', () => {
  const { home, repo, publish } = fixture();
  const start = run(home, { hook_event_name: 'SessionStart', source: 'startup', session_id: 's1', cwd: repo });
  assert.match(ctx(start), /Luật owner đang hiệu lực/);
  assert.match(ctx(start), /\| R3 \|/);
  // Same version: silent on prompts and tool calls.
  assert.equal(run(home, { hook_event_name: 'UserPromptSubmit', session_id: 's1', cwd: repo, prompt: 'x' }), null);
  assert.equal(run(home, { hook_event_name: 'PostToolUse', session_id: 's1', cwd: repo, tool_name: 'Bash' }), null);
  // Another session lands a rule change: the next tool call of the long turn carries it, with the id.
  publish(sheet.replace(R9, R9.replace('Làm tới 23:59.', 'Làm tới 23:59, kể cả cuối tuần.')));
  const mid = run(home, { hook_event_name: 'PostToolUse', session_id: 's1', cwd: repo, tool_name: 'Bash' });
  assert.equal(mid.hookSpecificOutput.hookEventName, 'PostToolUse');
  assert.match(ctx(mid), /Luật owner vừa đổi .*dòng đổi: R9/);
  assert.match(ctx(mid), /kể cả cuối tuần/);
  assert.equal(run(home, { hook_event_name: 'UserPromptSubmit', session_id: 's1', cwd: repo, prompt: 'y' }), null);
  // A second session that never saw the old version gets the new one on its first prompt.
  assert.match(ctx(run(home, { hook_event_name: 'UserPromptSubmit', session_id: 's2', cwd: repo, prompt: 'z' })), /kể cả cuối tuần/);
});

test('rules hook: resume, clear and compact deliver again even when the version did not change', () => {
  const { home, repo } = fixture();
  run(home, { hook_event_name: 'SessionStart', source: 'startup', session_id: 's1', cwd: repo });
  for (const source of ['resume', 'clear', 'compact']) {
    assert.match(ctx(run(home, { hook_event_name: 'SessionStart', source, session_id: 's1', cwd: repo })), /\| R1 \|/, source);
  }
});

test('rules hook: missing or unsafe session ids never share one "seen" key', () => {
  const { home, repo } = fixture();
  for (const session_id of [undefined, '../../etc/passwd', 'a/b', '']) {
    run(home, { hook_event_name: 'UserPromptSubmit', session_id, cwd: repo, prompt: 'x' });
    assert.match(ctx(run(home, { hook_event_name: 'UserPromptSubmit', session_id, cwd: repo, prompt: 'x' })), /\| R1 \|/, String(session_id));
  }
});

test('rules hook: only la-lanh folders (real path), and a missing sheet says so without blocking', () => {
  const { home, repo } = fixture();
  const elsewhere = mkdtempSync(join(tmpdir(), 'other-project-'));
  assert.equal(run(home, { hook_event_name: 'UserPromptSubmit', session_id: 's1', cwd: elsewhere, prompt: 'x' }), null);
  assert.equal(run(home, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: elsewhere, tool_name: 'AskUserQuestion', tool_input: {} }), null);
  const link = join(mkdtempSync(join(tmpdir(), 'link-')), 'work');
  symlinkSync(repo, link);
  assert.equal(inScope(link), true);
  assert.equal(inScope(join(repo, '.claude', 'worktrees', 'w1')), true);
  const empty = mkdtempSync(join(tmpdir(), 'rules-hook-nosheet-'));
  assert.match(ctx(run(empty, { hook_event_name: 'UserPromptSubmit', session_id: 's1', cwd: repo, prompt: 'x' })), /không đọc được/);
});

test('L37 (R3): a question to the owner in chat is refused and points to the decisions file', () => {
  const { home, repo } = fixture();
  const ask = run(home, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: repo, tool_name: 'AskUserQuestion', tool_input: { questions: [] } });
  assert.equal(ask.hookSpecificOutput.permissionDecision, 'deny');
  assert.match(ask.hookSpecificOutput.permissionDecisionReason, /viec-cho-chi-duyet\.md/);
  assert.match(ask.hookSpecificOutput.permissionDecisionReason, /5 phần/);
  const box = run(home, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: repo, tool_name: 'mcp__ccd_turn__wrap_up', tool_input: { recap: 'xong', ask: 'Chị chọn A hay B?' } });
  assert.equal(box.hookSpecificOutput.permissionDecision, 'deny');
  // A recap without a question, and other tools, pass.
  assert.equal(run(home, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: repo, tool_name: 'mcp__ccd_turn__wrap_up', tool_input: { recap: 'xong' } }), null);
  assert.equal(run(home, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: repo, tool_name: 'Bash', tool_input: { command: 'ls' } }), null);
  // The deny does not depend on the sheet: with no sheet at all it still refuses.
  const empty = mkdtempSync(join(tmpdir(), 'rules-hook-nosheet-'));
  assert.equal(run(empty, { hook_event_name: 'PreToolUse', session_id: 's1', cwd: repo, tool_name: 'AskUserQuestion', tool_input: {} }).hookSpecificOutput.permissionDecision, 'deny');
  // Every attempt is counted for the repeat-error metric, without the question text.
  const log = readFileSync(join(home, 'rules', 'violations.jsonl'), 'utf8');
  assert.equal(log.trim().split('\n').length, 2);
  assert.doesNotMatch(log, /Chị chọn/);
  assert.deepEqual(metrics({ home }).attemptsBlocked, { R3: 2 });
});

test('L37 (R3): the installed hook keeps other hooks, routes the question tools to the deny and fails closed', () => {
  let { home } = fixture();
  const settings = join(mkdtempSync(join(tmpdir(), 'settings-')), 'settings.json');
  const other = { matcher: 'Bash', hooks: [{ type: 'command', command: 'node guard.mjs' }] };
  writeFileSync(settings, JSON.stringify({ model: 'x', hooks: { PreToolUse: [other] } }));
  assert.ok(verifyRulesHook({ home, settings }).length > 0, 'not installed yet');
  installRulesHook({ home, settings });
  installRulesHook({ home, settings });
  const data = JSON.parse(readFileSync(settings, 'utf8'));
  assert.equal(data.model, 'x');
  assert.deepEqual(data.hooks.PreToolUse[0], other);
  assert.equal(data.hooks.PreToolUse.length, 2, 'installing twice does not duplicate');
  const pre = rulesHooks(home).PreToolUse;
  assert.match(pre.matcher, /(^|\|)AskUserQuestion(\||$)/);
  assert.match(pre.matcher, /(^|\|)mcp__ccd_turn__wrap_up(\||$)/);
  assert.equal(pre.hooks[0].onFailure, 'block');
  for (const event of ['SessionStart', 'UserPromptSubmit', 'PostToolUse']) assert.ok(data.hooks[event]?.length === 1, event);
  // verify needs a script in the ops clone that really refuses a question: an empty file fails.
  mkdirSync(join(home, 'ops', 'scripts'), { recursive: true });
  writeFileSync(join(home, 'ops', 'scripts', 'collab-rules-hook.mjs'), '');
  assert.match(verifyRulesHook({ home, settings }).join('\n'), /selftest trượt/);
  const real = mkdtempSync(join(tmpdir(), 'ops-real-'));
  mkdirSync(join(real, 'ops'), { recursive: true });
  symlinkSync(dirname(script), join(real, 'ops', 'scripts'));
  installRulesHook({ home: real, settings });
  assert.deepEqual(verifyRulesHook({ home: real, settings }), []);
  data.hooks = JSON.parse(readFileSync(settings, 'utf8')).hooks;
  home = real;
  // Removing the R3 route, or switching hooks off, is detected.
  data.hooks.PreToolUse = data.hooks.PreToolUse.filter(e => e === other || JSON.stringify(e) === JSON.stringify(other));
  writeFileSync(settings, JSON.stringify(data));
  assert.match(verifyRulesHook({ home, settings }).join('\n'), /PreToolUse/);
  writeFileSync(settings, JSON.stringify({ ...data, disableAllHooks: true }));
  assert.match(verifyRulesHook({ home, settings }).join('\n'), /disableAllHooks/);
  assert.match(r3Reason, /R3/);
});

test('rules hook: metrics give the delay from commit to each session, blocked attempts and owner repeats', () => {
  const { home, repo, publish } = fixture();
  const clock = iso => () => new Date(iso);
  handle({ hook_event_name: 'UserPromptSubmit', session_id: 'old', cwd: repo }, { home, now: clock('2026-11-16T15:00:00Z') });
  publish(sheet.replace(R9, `${R9} `));
  handle({ hook_event_name: 'UserPromptSubmit', session_id: 'a', cwd: repo }, { home, now: clock('2026-11-16T16:02:00Z') });
  handle({ hook_event_name: 'PostToolUse', session_id: 'b', cwd: repo }, { home, now: clock('2026-11-16T16:10:00Z') });
  // A broken line is skipped alone; the rotated generation still counts.
  appendFileSync(join(home, 'rules', 'deliveries.jsonl'), '{broken\n');
  writeFileSync(join(home, 'rules', 'violations.jsonl.1'), `${JSON.stringify({ at: '2026-11-16T10:00:00Z', session: 'x', rule: 'R3' })}\n`);
  const m = metrics({ home, committedAt: '2026-11-16T16:00:00Z' });
  assert.equal(m.sessionsReached, 2);
  assert.equal(m.firstSeenAt, '2026-11-16T16:02:00.000Z');
  assert.deepEqual(m.lagMinutes, { median: 10, max: 10 });
  assert.deepEqual(m.attemptsBlocked, { R3: 1 });
  // The owner repeats R3: counted once per session and hour, unknown ids refused, no words stored.
  assert.equal(recordRepeat({ home, rule: 'R3', session: 'a', now: clock('2026-11-16T17:00:00Z') }), true);
  assert.equal(recordRepeat({ home, rule: 'R3', session: 'a', now: clock('2026-11-16T17:20:00Z') }), false);
  assert.equal(recordRepeat({ home, rule: 'R3', session: 'a', now: clock('2026-11-16T18:30:00Z') }), true);
  assert.throws(() => recordRepeat({ home, rule: 'R99', session: 'a' }), /không có luật R99/);
  assert.deepEqual(metrics({ home }).ownerRepeats, { R3: 2 });
  // No hook, no log: "not measurable", never zero.
  assert.deepEqual(metrics({ home, hookOk: false }), { measurable: false, reason: 'hook luật chưa cài hoặc hỏng' });
  assert.deepEqual(changedIds(sheet, sheet.replace(R9, `${R9} `)), ['R9']);
});

test('rules hook: the context stays under the 10,000-character hook limit as the sheet grows', () => {
  const { home, repo, publish } = fixture();
  const filler = Array.from({ length: 40 }, (_, i) => `| R${18 + i} | Mọi phiên | Luật thử số ${18 + i} ${'rất dài '.repeat(20)} | owner, nguồn rất dài ${'x'.repeat(200)} | 17.11.2026 | — | chạy |`).join('\n');
  const big = sheet.replace(/(\| R17 \|.*\n)/, `$1${filler}\n`);
  assert.ok(big.length > 20000);
  publish(big);
  const out = ctx(run(home, { hook_event_name: 'SessionStart', source: 'startup', session_id: 's1', cwd: repo }));
  assert.ok(out.length < 10000, String(out.length));
  assert.match(out, /Bản rút gọn/);
  assert.match(out, /- R3 \(Mọi phiên Claude\): Không hỏi owner trong chat/);
  assert.equal(fitContext(sheet), sheet, 'today\'s sheet goes whole');
});
