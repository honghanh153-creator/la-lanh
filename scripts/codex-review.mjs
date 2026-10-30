// Run one Codex review of a PR head, apply the owner's P2 policy, and post the verdict.
// Usage: node scripts/codex-review.mjs --pr N [--auto]
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { agentMarker, blockingP2, clean, dayStatePath, integration, isSha, makeGh, readJson, repo, stateDir, trustedComments, vnNow, writeJson } from './collab-trust.mjs';
import { codexDailyCap, prTurn } from './collab-turn.mjs';

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

const cell = text => clean(text, 300).replace(/\|/g, '\\|').replace(/\n/g, ' ');

export function renderVerdict({ pr, out, policy, round, range, digest, fixIssue }) {
  const rows = out.findings.map(f => `| ${f.severity} | ${f.category} | \`${cell(f.file)}${f.line ? `:${f.line}` : ''}\` | ${cell(f.title)}: ${cell(f.detail)} | ${isBlocking(f) ? 'có' : 'không'} |`);
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
    `${agentMarker} codex-auto-review sha=${pr.headRefOid} p2=${policy.fixForward.length} -->`,
  ].join('\n');
}

function git(args, cwd, run) {
  return String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: 300000, maxBuffer: 64 * 1024 * 1024 })).trim();
}

export function prepareClone(number, head, run = execFileSync) {
  const dir = join(stateDir, 'review');
  if (!existsSync(join(dir, '.git'))) {
    mkdirSync(stateDir, { recursive: true });
    git(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir], stateDir, run);
  }
  git(['fetch', '--quiet', '--force', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`, `+refs/pull/${Number(number)}/head:refs/remotes/pr/${Number(number)}`], dir, run);
  git(['checkout', '--quiet', '--force', '--detach', head], dir, run);
  git(['clean', '-fdxq'], dir, run);
  const actual = git(['rev-parse', 'HEAD'], dir, run);
  if (actual !== head) throw new Error(`Review clone is at ${actual}, not ${head}.`);
  return dir;
}

const isLimit = text => /usage limit|rate limit|quota|too many requests|\b429\b/i.test(text);

export function runCodex({ dir, prompt, outPath, timeoutMs, run = execFileSync }) {
  try {
    run(codexBin, ['exec', '-s', 'read-only', '--ephemeral', '-m', codexModel, '-c', 'model_reasoning_effort="high"',
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

export function runReview(number, { auto = false, gh = makeGh(), run = execFileSync, now = vnNow(), readOut } = {}) {
  const pr = gh.pr(number);
  const head = pr.headRefOid;
  if (!isSha(head)) throw new Error('PR head SHA unavailable.');
  const turn = prTurn(pr);
  if (turn.turn !== 'codex-review') return { status: 'refused', reason: `lượt hiện tại là ${turn.turn}: ${turn.reason}` };
  const dayPath = dayStatePath(now.date);
  const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
  if (auto && day.codexRuns >= codexDailyCap) return { status: 'refused', reason: 'hết 12 lượt Codex tự động hôm nay' };

  const trusted = trustedComments(pr.comments);
  const priorAuto = trusted.filter(c => c.auto && c.verdict).at(-1);
  const dir = prepareClone(number, head, run);
  let deltaFrom = null;
  if (priorAuto && priorAuto.verdict.sha !== head) {
    try { git(['merge-base', '--is-ancestor', priorAuto.verdict.sha, head], dir, run); deltaFrom = priorAuto.verdict.sha; } catch {}
  }
  const mergeBase = git(['merge-base', `origin/${integration}`, head], dir, run);
  const prompt = fillPrompt(readFileSync(promptPath, 'utf8'), {
    PR: String(pr.number), HEAD: head, BASE_REF: pr.baseRefName, MERGE_BASE: mergeBase,
    DELTA_LINE: deltaFrom
      ? `Re-review: the previous automatic review was at \`${deltaFrom}\`. Read \`git diff ${deltaFrom}..${head}\` closely and confirm each earlier blocking finding is fixed; skim the rest.`
      : 'First automatic review of this PR: read the full change.',
    TITLE: clean(pr.title, 300), BODY: clean(pr.body, 12000), PRIOR: priorAuto ? clean(priorAuto.body, 8000) : 'None.',
  });

  const stamp = `${now.date}-pr${pr.number}-${head.slice(0, 12)}-${Date.now()}`;
  const outPath = join(stateDir, 'logs', `codex-${stamp}.json`);
  mkdirSync(dirname(outPath), { recursive: true });
  // Stop before midnight on scheduled runs; 30 minutes otherwise.
  const untilCutoff = ((23 * 60 + 55) - (now.hour * 60 + now.minute)) * 60000;
  const result = runCodex({ dir, prompt, outPath, timeoutMs: auto ? Math.max(60000, Math.min(30 * 60000, untilCutoff)) : 30 * 60000, run });
  if (result.status === 'limit') return { status: 'limit', reason: result.error };
  writeJson(dayPath, { ...readJson(dayPath, day), codexRuns: (readJson(dayPath, day).codexRuns ?? 0) + 1 });
  if (result.status !== 'ok') return { status: 'error', reason: result.error };

  const rawOut = readOut ? readOut(outPath) : readFileSync(outPath, 'utf8');
  const out = validateOutput(JSON.parse(rawOut), head);
  const policy = applyPolicy(out);
  const digest = createHash('sha256').update(rawOut).digest('hex');

  // Head must not have moved while Codex was reading.
  if (gh.pr(number).headRefOid !== head) return { status: 'stale', reason: 'head đổi trong lúc review; lượt sau review lại' };

  let fixIssue = null;
  if (policy.fixForward.length) {
    ensureLabel(gh, 'fix-forward', 'FBCA04', 'P2 không chặn, sửa tiếp sau merge');
    const list = policy.fixForward.map(f => `- [ ] ${f.severity} ${f.category} \`${cell(f.file)}${f.line ? `:${f.line}` : ''}\`: ${cell(f.title)}. ${cell(f.detail)}`);
    const url = gh.raw(['issue', 'create', '--repo', repo, '--label', 'fix-forward', '--title', `[fix-forward] PR #${pr.number} @ ${head.slice(0, 7)}: ${policy.fixForward.length} P2`, '--body-file', '-'],
      [`Từ review tự động của PR #${pr.number} @ \`${head}\`. Theo chính sách P2 ngày 30.10.2026 những mục này không chặn merge.`, '', ...list, '', `${agentMarker} fix-forward pr=${pr.number} -->`].join('\n'));
    fixIssue = Number(/\/issues\/(\d+)/.exec(url)?.[1]) || null;
    if (!fixIssue) throw new Error('Fix-forward issue was not created; verdict not posted.');
  }

  const priorRequests = trusted.filter(c => c.auto && c.verdict?.verdict === 'REQUEST_CHANGES').length;
  const round = trusted.filter(c => c.auto && c.verdict).length + 1;
  const body = renderVerdict({ pr, out, policy, round, range: deltaFrom ? `${deltaFrom.slice(0, 7)}..${head.slice(0, 7)}` : `${mergeBase.slice(0, 7)}..${head.slice(0, 7)}`, digest, fixIssue });
  gh.comment('pr', pr.number, body);
  const needsOwner = policy.verdict === 'REQUEST_CHANGES' && (!out.complete || priorRequests + 1 >= maxAutoRequestChanges);
  if (needsOwner) {
    ensureLabel(gh, 'needs-owner', 'D93F0B', 'Vòng tự động dừng, chờ owner');
    gh.raw(['pr', 'edit', String(pr.number), '--repo', repo, '--add-label', 'needs-owner']);
  }
  writeJson(join(stateDir, 'logs', `review-${stamp}.json`), { pr: pr.number, head, verdict: policy.verdict, digest, fixIssue, needsOwner, at: new Date().toISOString() });
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
