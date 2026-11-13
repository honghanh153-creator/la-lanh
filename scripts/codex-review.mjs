// Run one Codex review of a PR head, apply the owner's P2 policy, and post the verdict.
// Usage: node scripts/codex-review.mjs --pr N [--auto]
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { acquireLock } from './collab-lock.mjs';
import { DeadlineError, agentMarker, bindReceipt, boundedTimeout, blockingP2, clean, isOwnPr, dayStatePath, integration, isSha, makeGh, readJson, repo, reviewState, signReceipt, stateDir, trustedComments, verdictSeal, vnNow, writeJson } from './collab-trust.mjs';
import { codexDailyCap, prTurn } from './collab-turn.mjs';
import { groupExec } from './collab-heal.mjs';

const here = dirname(fileURLToPath(import.meta.url));
export const promptPath = join(here, '..', 'docs', 'operations', 'codex-review-prompt.md');
export const schemaPath = join(here, 'codex-review-schema.json');
export const codexBin = process.env.CODEX_BIN || '/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex';
export const codexModel = 'gpt-6.1-sol';
export const maxAutoRequestChanges = 2;
const severities = ['P0', 'P1', 'P2', 'P3'];
const categories = ['privacy', 'security', 'user_copy', 'correctness', 'test', 'docs', 'other'];

export const isBlocking = f => f.severity === 'P0' || f.severity === 'P1' || (f.severity === 'P2' && blockingP2.has(f.category));

export function validateOutput(out, head) {
  const bad = message => { throw new Error(`Codex output rejected: ${message}`); };
  if (!out || typeof out !== 'object') bad('not an object');
  if (!['APPROVE', 'REQUEST_CHANGES'].includes(out.verdict)) bad('verdict');
  if (out.sha !== head) bad(`sha ${clean(out.sha, 60)} is not head ${head}`);
  if (typeof out.complete !== 'boolean' || typeof out.summary !== 'string' || !Array.isArray(out.findings)) bad('shape');
  for (const f of out.findings) {
    if (!severities.includes(f?.severity) || !categories.includes(f?.category) || typeof f.file !== 'string' || typeof f.title !== 'string') bad('finding shape');
  }
  return out;
}

// The script may only make a verdict stricter, never more lenient.
export function applyPolicy(out) {
  const blocking = out.findings.filter(isBlocking);
  const verdict = out.verdict === 'REQUEST_CHANGES' || blocking.length || !out.complete ? 'REQUEST_CHANGES' : 'APPROVE';
  const fixForward = verdict === 'APPROVE' ? out.findings.filter(f => f.severity === 'P2') : [];
  return { verdict, blocking, fixForward, escalated: verdict !== out.verdict };
}

export function fillPrompt(template, values) {
  // Single pass, so a placeholder inside PR text is never expanded.
  return template.replace(/\{\{([A-Z_]+)\}\}/g, (_, key) => values[key] ?? '');
}

// #208: the S/M/L and gate-evidence check starts with PRs created on 01.11.2026 (Vietnam time). The
// reviewer has no network, so the script states the trusted creation time and the rule that applies.
export const gateCutoff = Date.parse('2026-11-01T00:00:00+07:00');
export function gateRule(createdAt) {
  const at = Date.parse(createdAt ?? '');
  if (!Number.isFinite(at)) return 'The PR creation time is unknown: apply the S/M/L and gate-evidence check.';
  const when = `This PR was created at ${new Date(at).toISOString()} (from GitHub, trusted).`;
  return at < gateCutoff
    ? `${when} It was created before 2026-11-01 (Vietnam time), so it is exempt from the S/M/L and gate-evidence check; review it against the AGENTS.md gates as before.`
    : `${when} It was created on or after 2026-11-01 (Vietnam time), so the S/M/L and gate-evidence check applies.`;
}

const cell = (text, limit = 900) => clean(text, limit).replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/\n/g, ' ');
// A detail may list every occurrence of one class (prompt rule S2); keep the whole list (fix-forward #238).
const detailCell = text => cell(text, 6000);

// `base`: the collab/integration tip when the review started (P1-A); `receipt`: the local receipt id (P1-B).
export function renderVerdict({ pr, out, policy, round, range, digest, fixIssue, base = null, receipt = null }) {
  const rows = out.findings.map(f => `| ${f.severity} | ${f.category} | \`${cell(f.file)}${f.line ? `:${f.line}` : ''}\` | ${cell(f.title)}: ${detailCell(f.detail)} | ${isBlocking(f) ? 'có' : 'không'} |`);
  return [
    `Review verdict: ${policy.verdict} @ ${pr.headRefOid}`,
    'Reviewer: Codex (auto, scripts/codex-review.mjs)',
    `Round: auto-${round} · range \`${cell(range)}\`${out.complete ? '' : ' · **review chưa đủ, chuyển owner**'}${policy.escalated ? ' · verdict được script nâng theo chính sách P2' : ''}`,
    '',
    clean(out.summary, 3000),
    '',
    ...(rows.length ? ['| Mức | Loại | Vị trí | Vấn đề | Chặn merge |', '|---|---|---|---|---|', ...rows, ''] : ['Không có phát hiện.', '']),
    ...(fixIssue ? [`Fix-forward: #${fixIssue}`, ''] : []),
    `Output SHA-256: \`${digest}\``,
    `Base lúc review: \`${integration}\` @ ${isSha(base) ? `\`${base.slice(0, 12)}\`` : 'không rõ'}`,
    verdictSeal({ head: pr.headRefOid, p2: policy.fixForward.length, base, receipt }),
  ].join('\n');
}

function git(args, cwd, run, left = () => Infinity) {
  return String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: boundedTimeout(300000, left), maxBuffer: 64 * 1024 * 1024 })).trim();
}

export function prepareClone(number, head, run = execFileSync, left = () => Infinity) {
  const dir = join(stateDir, 'review');
  if (!existsSync(join(dir, '.git'))) {
    mkdirSync(stateDir, { recursive: true });
    git(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir], stateDir, run, left);
  }
  git(['fetch', '--quiet', '--force', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`, `+refs/pull/${Number(number)}/head:refs/remotes/pr/${Number(number)}`], dir, run, left);
  git(['checkout', '--quiet', '--force', '--detach', head], dir, run, left);
  git(['clean', '-fdxq'], dir, run, left);
  const actual = git(['rev-parse', 'HEAD'], dir, run, left);
  if (actual !== head) throw new Error(`Review clone is at ${actual}, not ${head}.`);
  return dir;
}

const isLimit = text => /usage limit|rate limit|quota|too many requests|\b429\b/i.test(text);

export function runCodex({ dir, prompt, outPath, timeoutMs, run = execFileSync }) {
  // The real run is a process group: the timeout kills Codex and everything it started (05.11.2026).
  const exec = run === execFileSync ? groupExec : run;
  try {
    exec(codexBin, ['exec', '-s', 'read-only', '--ephemeral', '-m', codexModel, '-c', 'model_reasoning_effort="high"',
      '-C', dir, '--output-schema', schemaPath, '-o', outPath, '--color', 'never', '-'],
    { input: prompt, encoding: 'utf8', timeout: timeoutMs, maxBuffer: 64 * 1024 * 1024 });
  } catch (error) {
    const text = `${error.stdout ?? ''}\n${error.stderr ?? ''}\n${error.message ?? ''}`;
    return { status: isLimit(text) ? 'limit' : 'error', error: clean(text.trim().split('\n').slice(-5).join(' '), 400) };
  }
  return { status: 'ok' };
}

function ensureLabel(gh, name, color, description) {
  gh.raw(['label', 'create', name, '--repo', repo, '--color', color, '--description', description, '--force']);
}

// One review at a time: every review shares the clone, so a second caller waits for the next run.
export function runReview(number, options = {}) {
  mkdirSync(stateDir, { recursive: true });
  // Reclaim of a dead or 45-minute-old lock runs under the reclaim mutex (collab-lock.mjs, Codex #258).
  const release = acquireLock(join(stateDir, 'review.lock'), { staleMs: 45 * 60000 });
  if (!release) return { status: 'busy', reason: 'một review khác đang chạy' };
  try { return reviewOnce(number, options); }
  catch (error) { if (error instanceof DeadlineError) return { status: 'refused', reason: 'hết giờ (23:55) trong lúc review' }; throw error; }
  finally { release(); }
}

// Time kept after Codex for the git check and up to five gh calls (60 s each) that publish the result.
export const reviewFinalizeReserveMs = 5 * 60000;

function reviewOnce(number, { auto = false, gh: ghIn = makeGh(), run = execFileSync, now = vnNow(), clock = vnNow, readOut, nowMs = Date.now } = {}) {
  // Scheduled runs: every gh and git call ends by 23:55 (minus 15 s cleanup); direct runs keep fixed caps.
  const cutoff = Date.parse(`${now.date}T23:55:00+07:00`) - 15000;
  const left = auto && Number.isFinite(cutoff) ? () => cutoff - nowMs() : () => Infinity;
  const gh = ghIn.withDeadline?.(left) ?? ghIn;
  const pr = gh.pr(number);
  const head = pr.headRefOid;
  if (!isSha(head)) throw new Error('PR head SHA unavailable.');
  // P1-A: the verdict records the integration tip it was reviewed against; without it the APPROVE
  // could never be compared with a later base, so no review starts.
  const reviewedBase = pr.baseTipOid;
  if (!isSha(reviewedBase)) return { status: 'refused', reason: `không đọc được SHA hiện tại của ${integration}` };
  // prTurn holds fork/outside PRs; checked here too so a direct call never reviews one.
  if (!isOwnPr(pr)) return { status: 'refused', reason: 'PR không phải của owner hoặc từ fork' };
  const turn = prTurn(pr);
  if (turn.turn !== 'codex-review') return { status: 'refused', reason: `lượt hiện tại là ${turn.turn}: ${turn.reason}` };
  const dayPath = dayStatePath(now.date);
  const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
  if (auto && day.codexRuns >= codexDailyCap) return { status: 'refused', reason: `hết ${codexDailyCap} lượt Codex tự động hôm nay` };

  const trusted = trustedComments(pr.comments);
  // Only a signed earlier review narrows the re-review to a delta: an unsigned one could be forged to
  // point Codex at a harmless range (P1-B).
  const priorAuto = reviewState(pr).sealed.filter(c => c.auto && c.verdict).at(-1);
  const dir = prepareClone(number, head, run, left);
  let deltaFrom = null;
  if (priorAuto && priorAuto.verdict.sha !== head) {
    try { git(['merge-base', '--is-ancestor', priorAuto.verdict.sha, head], dir, run, left); deltaFrom = priorAuto.verdict.sha; } catch {}
  }
  const mergeBase = git(['merge-base', `origin/${integration}`, head], dir, run, left);
  // A delta that merges collab/integration in carries every other PR's files; on 02.11 Codex marked the
  // #117 re-review incomplete over 230 such files (K25). Limit the delta to the PR's own files.
  const mergesBase = deltaFrom && git(['rev-list', '--merges', `${deltaFrom}..${head}`], dir, run, left).trim() !== '';
  // The script writes the scoped delta itself: NUL-separated names passed as literal paths keep
  // filenames with spaces or quoting intact, which a shell substitution in the prompt would not.
  const deltaPath = join(dir, '.git', 'la-lanh-review-delta.patch');
  if (mergesBase) {
    const own = String(run('/usr/bin/git', ['diff', '-z', '--name-only', `${mergeBase}..${head}`], { cwd: dir, encoding: 'utf8', timeout: boundedTimeout(300000, left), maxBuffer: 64 * 1024 * 1024 })).split('\0').filter(Boolean);
    const patch = own.length ? String(run('/usr/bin/git', ['diff', `${deltaFrom}..${head}`, '--', ...own.map(f => `:(literal)${f}`)], { cwd: dir, encoding: 'utf8', timeout: boundedTimeout(300000, left), maxBuffer: 64 * 1024 * 1024 })) : '';
    mkdirSync(dirname(deltaPath), { recursive: true });
    writeFileSync(deltaPath, patch);
  }
  const prompt = fillPrompt(readFileSync(promptPath, 'utf8'), {
    PR: String(pr.number), HEAD: head, BASE_REF: pr.baseRefName, MERGE_BASE: mergeBase, GATE_RULE: gateRule(pr.createdAt),
    DELTA_LINE: deltaFrom
      ? mergesBase
        ? `Re-review: the previous automatic review was at \`${deltaFrom}\`, and the delta merges \`${integration}\` in. Read \`.git/la-lanh-review-delta.patch\` closely: it is \`git diff ${deltaFrom}..${head}\` limited to this PR's own files, including conflict resolutions and confirm each earlier blocking finding is fixed. Files changed only by the merged \`${integration}\` were reviewed in their own PRs: do not read them and do not mark the review incomplete because of them.`
        : `Re-review: the previous automatic review was at \`${deltaFrom}\`. Read \`git diff ${deltaFrom}..${head}\` closely and confirm each earlier blocking finding is fixed; skim the rest.`
      : 'First automatic review of this PR: read the full change.',
    TITLE: clean(pr.title, 300), BODY: clean(pr.body, 12000), PRIOR: priorAuto ? clean(priorAuto.body, 8000) : 'None.',
  });

  const stamp = `${now.date}-pr${pr.number}-${head.slice(0, 12)}-${Date.now()}`;
  const outPath = join(stateDir, 'logs', `codex-${stamp}.json`);
  mkdirSync(dirname(outPath), { recursive: true });
  // Fetching can be slow, so read the clock again right before Codex starts (fix-forward #131).
  // Scheduled runs start nothing after 23:30 and stop by 23:55; direct runs get 30 minutes.
  const startAt = clock();
  const startMinute = startAt.hour * 60 + startAt.minute;
  if (auto && (startMinute < 8 * 60 + 50 || startMinute >= 23 * 60 + 30)) return { status: 'refused', reason: 'ngoài giờ chạy tự động (sau 23:30)' };
  // Codex must end early enough that the verdict, labels and fix-forward issue still fit before
  // the Git/GitHub cutoff (#243); without that room, it does not start.
  const untilCutoff = Math.min(((23 * 60 + 55) - startMinute) * 60000, left()) - reviewFinalizeReserveMs;
  if (auto && untilCutoff < 60000) return { status: 'refused', reason: 'không đủ thời gian để đăng kết quả trước 23:55' };
  const result = runCodex({ dir, prompt, outPath, timeoutMs: auto ? Math.min(30 * 60000, untilCutoff) : 30 * 60000, run });
  if (result.status === 'limit') return { status: 'limit', reason: result.error };
  writeJson(dayPath, { ...readJson(dayPath, day), codexRuns: (readJson(dayPath, day).codexRuns ?? 0) + 1 });
  if (result.status !== 'ok') return { status: 'error', reason: result.error };
  // The verdict must describe what Codex actually read.
  if (git(['rev-parse', 'HEAD'], dir, run, left) !== head) throw new Error('Review clone moved while Codex was reading; verdict not posted.');

  const rawOut = readOut ? readOut(outPath) : readFileSync(outPath, 'utf8');
  const out = validateOutput(JSON.parse(rawOut), head);
  const policy = applyPolicy(out);
  const digest = createHash('sha256').update(rawOut).digest('hex');

  // Head must not have moved while Codex was reading.
  if (gh.pr(number).headRefOid !== head) return { status: 'stale', reason: 'head đổi trong lúc review; lượt sau review lại' };

  let fixIssue = null;
  if (policy.fixForward.length) {
    ensureLabel(gh, 'fix-forward', 'FBCA04', 'P2 không chặn, sửa tiếp sau merge');
    const list = policy.fixForward.map(f => `- [ ] ${f.severity} ${f.category} \`${cell(f.file)}${f.line ? `:${f.line}` : ''}\`: ${cell(f.title)}. ${detailCell(f.detail)}`);
    const url = gh.raw(['issue', 'create', '--repo', repo, '--label', 'fix-forward', '--title', `[fix-forward] PR #${pr.number} @ ${head.slice(0, 7)}: ${policy.fixForward.length} P2`, '--body-file', '-'],
      [`Từ review tự động của PR #${pr.number} @ \`${head}\`. Theo chính sách P2 ngày 30.10.2026 những mục này không chặn merge.`, '', ...list, '', `${agentMarker} fix-forward pr=${pr.number} -->`].join('\n'));
    fixIssue = Number(/\/issues\/(\d+)/.exec(url)?.[1]) || null;
    if (!fixIssue) throw new Error('Fix-forward issue was not created; verdict not posted.');
  }

  const priorRequests = trusted.filter(c => c.auto && c.verdict?.verdict === 'REQUEST_CHANGES').length;
  const round = trusted.filter(c => c.auto && c.verdict).length + 1;
  // P1-B: the receipt is written before the comment, so every posted verdict has one.
  const receipt = signReceipt({ kind: 'verdict', pr: pr.number, head, base: reviewedBase, result: policy.verdict, p2: policy.fixForward.length });
  const body = renderVerdict({ pr, out, policy, round, range: deltaFrom ? `${deltaFrom.slice(0, 7)}..${head.slice(0, 7)}` : `${mergeBase.slice(0, 7)}..${head.slice(0, 7)}`, digest, fixIssue, base: reviewedBase, receipt });
  const posted = gh.comment('pr', pr.number, body);
  // Bound to the new comment's id: a later copy of this verdict never counts (replay, #456 auto-1).
  if (!bindReceipt({ kind: 'verdict', pr: pr.number, id: receipt, url: posted })) process.stderr.write(`codex-review: receipt ${receipt} not bound to a comment id; the verdict will not count\n`);
  const needsOwner = policy.verdict === 'REQUEST_CHANGES' && (!out.complete || priorRequests + 1 >= maxAutoRequestChanges);
  if (needsOwner) {
    ensureLabel(gh, 'needs-owner', 'D93F0B', 'Vòng tự động dừng, chờ owner');
    gh.raw(['pr', 'edit', String(pr.number), '--repo', repo, '--add-label', 'needs-owner']);
  }
  writeJson(join(stateDir, 'logs', `review-${stamp}.json`), { pr: pr.number, head, base: reviewedBase, verdict: policy.verdict, receipt, digest, fixIssue, needsOwner, at: new Date().toISOString() });
  return { status: 'posted', verdict: policy.verdict, blocking: policy.blocking.length, fixIssue, needsOwner };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/codex-review.mjs --pr N [--auto]\n'); process.exit(2);
  }
  try {
    const result = runReview(number, { auto: args.includes('--auto') });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'posted') process.exitCode = 3;
  } catch (error) { process.stderr.write(`codex-review failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
