// Claude Code hook that keeps every Lá Lành session on the owner's current rules (owner 16.11.2026:
// "you forget a lot and don't learn"). Two causes it removes:
// - a long session never re-read the rules another session wrote later: on SessionStart and on every
//   UserPromptSubmit the hook compares the rules sheet version (docs/operations/luat-dang-hieu-luc.md
//   in the ops clone, i.e. reviewed collab/integration code) with the version this session last
//   received, and only when it differs adds the sheet, with the ids that changed, to the context;
// - rule R3 ("never ask the owner in chat; put it in the decisions file") lived only in memory and a
//   long session still asked: PreToolUse denies AskUserQuestion, and a wrap_up that carries a
//   question, with the way to do it instead. The deny never depends on the sheet being readable.
// Every delivery and every denied attempt is logged (no prompt text, no tool input) so the 07:00
// report can show how fast a new rule reaches all sessions and how often a corrected mistake returns.
// Scope: only sessions whose cwd is a la-lanh checkout or the loop's state dir; elsewhere it is a no-op.
// Fail-open for the re-load (a missing sheet must not stop work; the context says so instead),
// fail-closed for R3 (the deny is a constant, the log write may fail without changing it).
// Usage (from ~/.claude/settings.json):  node scripts/collab-rules-hook.mjs   (hook JSON on stdin)
//        node scripts/collab-rules-hook.mjs --install | --verify | --metrics [since] | --selftest | --repeat Rn [session]
import { execFileSync, spawnSync } from 'node:child_process';
import { appendFileSync, copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import { parseRules, rulesVersion, sheetRel } from './collab-rules.mjs';
import { stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const rulesDir = (home = stateDir) => join(home, 'rules');
export const sheetFile = (home = stateDir) => process.env.LA_LANH_RULES_SHEET || join(home, 'ops', sheetRel);
export const hookScript = (home = stateDir) => join(home, 'ops', 'scripts', 'collab-rules-hook.mjs');
export const decisionsFile = '/Users/phamhanh/Documents/New project/la-lanh/docs/reviews/viec-cho-chi-duyet.md';

// A la-lanh checkout (la-lanh, la-lanh-claude, la-lanh-codex, their worktrees) or the loop state dir,
// judged on the real path (a symlink into a checkout counts, a symlink named la-lanh elsewhere does
// not). Limit: by folder name, not by Git remote; a session started outside these folders is not reached.
const pattern = /\/la-lanh(?:[-/]|$)/;
export function inScope(cwd) {
  if (!cwd) return false;
  try { return pattern.test(realpathSync(String(cwd))); } catch { return pattern.test(String(cwd)); }
}
const safeId = id => (/^[A-Za-z0-9_-]{1,128}$/.test(String(id ?? '')) ? String(id) : null);

// Logs hold session ids, times, versions and rule ids only (no prompt or tool input); one old
// generation is kept when a file passes maxLog bytes, so they stay small.
export const maxLog = 512 * 1024;
function log(home, file, entry) {
  try {
    mkdirSync(rulesDir(home), { recursive: true });
    const path = join(rulesDir(home), file);
    try { if (statSync(path).size > maxLog) renameSync(path, `${path}.1`); } catch {}
    appendFileSync(path, `${JSON.stringify(entry)}\n`);
  } catch {}
}

function readSheetText(home) {
  try { return readFileSync(sheetFile(home), 'utf8'); } catch { return null; }
}

// Ids whose row text differs between two sheet versions (added, removed or edited rows).
export function changedIds(oldText, newText) {
  if (!oldText) return [];
  const rows = t => new Map(parseRules(t).rows.map(r => [r.id, r.line]));
  const a = rows(oldText);
  const b = rows(newText);
  return [...new Set([...a.keys(), ...b.keys()])].filter(id => a.get(id) !== b.get(id));
}

// SessionStart (any source: startup, resume, clear, compact — a compacted context may have lost the
// sheet) always delivers. UserPromptSubmit and PostToolUse deliver only when the version moved:
// PostToolUse reaches a long turn that gets no new prompt (Codex r1 on the plan).
export function reload(input, { home = stateDir, now = () => new Date() } = {}) {
  const session = safeId(input.session_id);
  const event = input.hook_event_name;
  const text = readSheetText(home);
  if (text === null) {
    log(home, 'deliveries.jsonl', { at: now().toISOString(), session, event, version: null, error: 'sheet unreadable' });
    return `Luật owner đang hiệu lực: không đọc được ${sheetFile(home)}. Đọc docs/operations/luat-dang-hieu-luc.md trên origin/collab/integration trước khi làm tiếp.`;
  }
  const version = rulesVersion(text);
  const seenPath = session ? join(rulesDir(home), 'seen', session) : null;
  let seen = null;
  if (seenPath) try { seen = readFileSync(seenPath, 'utf8').trim(); } catch {}
  if (event !== 'SessionStart' && seen === version) return null;
  let oldText = null;
  if (seen && seen !== version) try { oldText = readFileSync(join(rulesDir(home), 'versions', `${seen}.md`), 'utf8'); } catch {}
  const changed = changedIds(oldText, text);
  try {
    mkdirSync(join(rulesDir(home), 'versions'), { recursive: true });
    const keep = join(rulesDir(home), 'versions', `${version}.md`);
    if (!existsSync(keep)) writeFileSync(keep, text);
    if (seenPath) {
      mkdirSync(join(rulesDir(home), 'seen'), { recursive: true });
      writeFileSync(`${seenPath}.tmp`, version);
      renameSync(`${seenPath}.tmp`, seenPath);
    }
  } catch {}
  const why = seen && seen !== version ? 'changed' : event === 'SessionStart' ? 'start' : 'first';
  log(home, 'deliveries.jsonl', { at: now().toISOString(), session, event, version, previous: seen, why, changed });
  const head = why === 'changed'
    ? `Luật owner vừa đổi (bản ${seen} → ${version}${changed.length ? `; dòng đổi: ${changed.join(', ')}` : ''}). Áp dụng bản dưới đây từ bây giờ, kể cả cho việc đang làm.`
    : `Luật owner đang hiệu lực (bản ${version}). Đọc trước khi làm; trước khi cần owner, xem R3.`;
  return `${head}\n\n${text}`;
}

export const r3Reason = `R3 (luật owner): không hỏi owner trong chat. Gửi việc cần owner cho phiên điều phối để ghi vào ${decisionsFile} theo 5 phần (chuyện gì / vì sao cần chị / các lựa chọn / mình khuyên / chị trả lời) kèm mặc định an toàn, rồi làm tiếp theo mặc định đó. Nếu không phải việc thuộc 4 loại của owner (R2) thì tự quyết theo docs/operations/decision-checklist.md.`;

// The bad behaviour itself: a question to the owner in chat. AskUserQuestion always; a wrap_up only
// when it carries a question (the recap alone is fine).
export function askingOwner(input) {
  if (input.tool_name === 'AskUserQuestion') return true;
  if (input.tool_name === 'mcp__ccd_turn__wrap_up') return String(input.tool_input?.ask ?? '').trim() !== '';
  return false;
}

export function handle(input, opts = {}) {
  const home = opts.home ?? stateDir;
  const now = opts.now ?? (() => new Date());
  if (!inScope(input.cwd)) return null;
  const event = input.hook_event_name;
  if (event === 'SessionStart' || event === 'UserPromptSubmit' || event === 'PostToolUse') {
    const context = reload(input, { home, now });
    return context ? { hookSpecificOutput: { hookEventName: event, additionalContext: context } } : null;
  }
  if (event === 'PreToolUse' && askingOwner(input)) {
    log(home, 'violations.jsonl', { at: now().toISOString(), session: safeId(input.session_id), rule: 'R3', tool: input.tool_name });
    return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: r3Reason } };
  }
  return null;
}

// Installed next to the agent gate in ~/.claude/settings.json, from the ops clone, with the bundled node.
const nodePath = '$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin';
export const settingsPath = (user = homedir()) => join(user, '.claude', 'settings.json');
export const rulesHooks = (home = stateDir) => {
  const command = `PATH="${nodePath}:/usr/bin:/bin:/usr/sbin" node "${hookScript(home)}"`;
  return {
    SessionStart: { hooks: [{ type: 'command', command, timeout: 30 }] },
    UserPromptSubmit: { hooks: [{ type: 'command', command, timeout: 30 }] },
    PostToolUse: { matcher: '*', hooks: [{ type: 'command', command, timeout: 30 }] },
    // The R3 deny fails closed: a hook that crashes or times out blocks the question too.
    PreToolUse: { matcher: 'AskUserQuestion|mcp__ccd_turn__wrap_up', hooks: [{ type: 'command', command, timeout: 30, onFailure: 'block' }] },
  };
};
const isRulesHook = (entry, home) => (entry?.hooks ?? []).some(h => String(h?.command ?? '').includes(hookScript(home)));

export function installRulesHook({ home = stateDir, settings = settingsPath(), now = () => new Date() } = {}) {
  let data = {};
  if (existsSync(settings)) {
    data = JSON.parse(readFileSync(settings, 'utf8'));
    copyFileSync(settings, `${settings}.bak-${now().toISOString().replace(/[:.]/g, '-')}`);
  }
  const hooks = { ...(data.hooks ?? {}) };
  for (const [event, entry] of Object.entries(rulesHooks(home))) hooks[event] = [...(hooks[event] ?? []).filter(e => !isRulesHook(e, home)), entry];
  const tmp = `${settings}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify({ ...data, hooks }, null, 2)}\n`);
  renameSync(tmp, settings);
  return settings;
}

// Detects removal or change (same machine rights as the agent gate: it cannot prevent them).
export function verifyRulesHook({ home = stateDir, settings = settingsPath() } = {}) {
  let data;
  try { data = JSON.parse(readFileSync(settings, 'utf8')); } catch { return [`không đọc được ${settings}`]; }
  const bad = [];
  for (const [event, want] of Object.entries(rulesHooks(home))) {
    const got = (data.hooks?.[event] ?? []).filter(e => isRulesHook(e, home));
    if (got.length !== 1 || JSON.stringify(got[0]) !== JSON.stringify(want)) bad.push(`hook ${event} của luật owner thiếu hoặc khác bản chuẩn`);
  }
  for (const file of [settings, settings.replace(/settings\.json$/, 'settings.local.json')]) {
    try { if (JSON.parse(readFileSync(file, 'utf8')).disableAllHooks === true) bad.push(`disableAllHooks đang bật trong ${file}`); } catch {}
  }
  // The installed script must really refuse a question (Codex r2: an empty file passed "exists").
  if (!existsSync(hookScript(home))) bad.push('không thấy collab-rules-hook.mjs trong clone ops');
  else if (!selftestPasses(hookScript(home))) bad.push('collab-rules-hook.mjs trong clone ops không tự chặn được câu hỏi (selftest trượt)');
  return bad;
}

// Runs the R3 path on a throwaway state dir: a synthetic AskUserQuestion in a la-lanh folder must be denied.
export function selftest() {
  const home = mkdtempSync(join(tmpdir(), 'rules-hook-selftest-'));
  const out = handle({ hook_event_name: 'PreToolUse', tool_name: 'AskUserQuestion', tool_input: {}, session_id: 'selftest', cwd: '/selftest/la-lanh' }, { home });
  return out?.hookSpecificOutput?.permissionDecision === 'deny';
}
export function selftestPasses(script) {
  const r = spawnSync(process.execPath, [script, '--selftest'], { encoding: 'utf8', timeout: 20000 });
  return r.status === 0 && /^selftest ok$/m.test(r.stdout ?? '');
}

// Owner repeated a rule: the session that heard it records it (Codex r2: an explicit event, not a
// keyword scan of transcripts). No owner words are stored; the same rule from the same session within
// an hour counts once.
export function recordRepeat({ home = stateDir, rule, session, now = () => new Date() }) {
  const text = readSheetText(home);
  const ids = new Set(text ? parseRules(text).rows.map(r => r.id) : []);
  if (!ids.has(rule)) throw new Error(`không có luật ${rule} trong bảng`);
  const at = now();
  const id = safeId(session);
  const recent = readLines(join(rulesDir(home), 'repeats.jsonl')).some(r => r.rule === rule && r.session === id && at - Date.parse(r.at) < 3600000);
  if (recent) return false;
  log(home, 'repeats.jsonl', { at: at.toISOString(), rule, session: id, version: text ? rulesVersion(text) : null });
  return true;
}

// Both generations of a log (the rotated .1 first); a broken line is skipped alone.
function readLines(path) {
  const out = [];
  for (const p of [`${path}.1`, path]) {
    let text = '';
    try { text = readFileSync(p, 'utf8'); } catch { continue; }
    for (const l of text.split('\n')) { if (!l.trim()) continue; try { out.push(JSON.parse(l)); } catch {} }
  }
  return out;
}

// How fast the current sheet reached sessions, how often the R3 route refused a question (an attempt
// that was blocked, not a proven breach), and how often the owner had to repeat a rule. When the hook
// is not installed nothing is logged, so the numbers are "not measurable", never "zero".
// committedAt: commit time of the sheet in the ops clone; firstSeenAt: the first delivery of this
// version to any session (when the clone really had it).
export function metrics({ home = stateDir, committedAt = null, since = null, hookOk = true } = {}) {
  if (!hookOk) return { measurable: false, reason: 'hook luật chưa cài hoặc hỏng' };
  const deliveries = readLines(join(rulesDir(home), 'deliveries.jsonl'));
  const recent = file => readLines(join(rulesDir(home), file)).filter(v => !since || v.at >= since);
  const text = readSheetText(home);
  const version = text ? rulesVersion(text) : null;
  const firstBySession = new Map();
  for (const d of deliveries) if (d.version === version && d.session && !firstBySession.has(d.session)) firstBySession.set(d.session, d.at);
  const firstSeenAt = [...firstBySession.values()].sort()[0] ?? null;
  const lags = committedAt ? [...firstBySession.values()].map(at => (Date.parse(at) - Date.parse(committedAt)) / 60000).filter(m => m >= 0).sort((a, b) => a - b) : [];
  const count = rows => rows.reduce((acc, v) => ({ ...acc, [v.rule]: (acc[v.rule] ?? 0) + 1 }), {});
  return {
    measurable: true, version, committedAt, firstSeenAt,
    sessionsReached: firstBySession.size,
    lagMinutes: lags.length ? { median: lags[Math.floor(lags.length / 2)], max: lags.at(-1) } : null,
    attemptsBlocked: count(recent('violations.jsonl')),
    ownerRepeats: count(recent('repeats.jsonl')),
  };
}

function sheetCommitTime(home) {
  try { return execFileSync('/usr/bin/git', ['-C', join(home, 'ops'), 'log', '-1', '--format=%cI', '--', sheetRel], { encoding: 'utf8' }).trim() || null; } catch { return null; }
}

if (isMain(import.meta.url)) {
  const arg = process.argv[2];
  if (arg === '--install') console.log(`đã cài hook luật owner vào ${installRulesHook()}`);
  else if (arg === '--verify') { const bad = verifyRulesHook(); for (const b of bad) console.log(`- ${b}`); process.exitCode = bad.length ? 1 : 0; }
  else if (arg === '--metrics') console.log(JSON.stringify(metrics({ committedAt: sheetCommitTime(stateDir), since: process.argv[3] ?? null, hookOk: verifyRulesHook().length === 0 }), null, 2));
  else if (arg === '--selftest') { const ok = selftest(); console.log(ok ? 'selftest ok' : 'selftest FAILED'); process.exitCode = ok ? 0 : 1; }
  else if (arg === '--repeat') {
    // node scripts/collab-rules-hook.mjs --repeat R3 [session id]: the owner had to say rule R3 again.
    const added = recordRepeat({ rule: process.argv[3], session: process.argv[4] ?? process.env.LA_LANH_SESSION ?? null });
    console.log(added ? `đã ghi: owner nhắc lại ${process.argv[3]}` : `đã có trong 1 giờ qua: ${process.argv[3]}`);
  }
  else {
    let raw = '';
    try { raw = readFileSync(0, 'utf8'); } catch {}
    let input = {};
    try { input = JSON.parse(raw || '{}'); } catch { input = {}; }
    const out = handle(input);
    if (out) process.stdout.write(JSON.stringify(out));
  }
}
