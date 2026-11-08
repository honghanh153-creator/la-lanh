// Per-PR numbers instead of feelings (owner 08.11.2026; METR 2025: developers felt 20% faster while
// measuring 19% slower). For each PR merged into collab/integration it reports open→merge hours,
// Codex review runs and minutes (cost proxy from review-runs.jsonl), change-request rounds, and rework
// (a later fix-forward issue or revert that names the PR).
// Usage: node scripts/collab-pr-metrics.mjs [--days 7] [--json]
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { integration, makeGh, repo, stateDir } from './collab-trust.mjs';

const verdicts = body => [...String(body ?? '').matchAll(/Review verdict:\s*(APPROVE|REQUEST_CHANGES)/g)].map(m => m[1]);

export function prMetrics(pr, runs = [], rework = new Set()) {
  const mine = runs.filter(r => r.pr === pr.number);
  const v = (pr.comments ?? []).flatMap(c => verdicts(c.body));
  return {
    pr: pr.number,
    title: pr.title,
    hours: pr.mergedAt ? Math.round((Date.parse(pr.mergedAt) - Date.parse(pr.createdAt)) / 36e5 * 10) / 10 : null,
    codexRuns: mine.length,
    codexMinutes: Math.round(mine.reduce((n, r) => n + (Number(r.ms) || 0), 0) / 6e4),
    changeRequests: v.filter(x => x === 'REQUEST_CHANGES').length,
    rework: rework.has(pr.number),
  };
}

export function summary(rows) {
  const n = rows.length || 1;
  const avg = k => Math.round(rows.reduce((s, r) => s + (r[k] ?? 0), 0) / n * 10) / 10;
  return { prs: rows.length, avgHours: avg('hours'), avgCodexRuns: avg('codexRuns'), avgChangeRequests: avg('changeRequests'),
    firstPassRate: Math.round(rows.filter(r => !r.changeRequests).length / n * 100), reworkRate: Math.round(rows.filter(r => r.rework).length / n * 100) };
}

export const reworkRefs = items => new Set(items
  .filter(i => /fix-forward|^revert/i.test(`${(i.labels ?? []).map(l => l.name ?? l).join(' ')} ${i.title}`))
  .flatMap(i => [...`${i.title} ${i.body ?? ''}`.matchAll(/#(\d+)/g)].map(m => Number(m[1]))));

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  const days = Number(process.argv[process.argv.indexOf('--days') + 1]) || 7;
  const since = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  const gh = makeGh();
  const prs = gh.json(['pr', 'list', '--repo', repo, '--state', 'merged', '--base', integration, '--search', `merged:>=${since}`, '--limit', '200', '--json', 'number,title,createdAt,mergedAt,comments']);
  const later = gh.json(['issue', 'list', '--repo', repo, '--state', 'all', '--search', `created:>=${since}`, '--limit', '300', '--json', 'number,title,body,labels'])
    .concat(gh.json(['pr', 'list', '--repo', repo, '--state', 'all', '--search', `created:>=${since} revert in:title`, '--limit', '100', '--json', 'number,title,body,labels']));
  const log = join(stateDir, 'review-runs.jsonl');
  const runs = existsSync(log) ? readFileSync(log, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean) : [];
  const rows = prs.map(pr => prMetrics(pr, runs, reworkRefs(later)));
  if (process.argv.includes('--json')) console.log(JSON.stringify({ since, summary: summary(rows), rows }, null, 2));
  else {
    const s = summary(rows);
    console.log(`Từ ${since}: ${s.prs} PR merge · TB ${s.avgHours} giờ/PR · ${s.avgCodexRuns} lượt Codex/PR · ${s.firstPassRate}% qua review lần đầu · ${s.reworkRate}% có việc sửa tiếp (fix-forward hoặc revert)`);
    for (const r of rows) console.log(`#${r.pr}\t${r.hours}h\tCodex ${r.codexRuns}× ${r.codexMinutes}p\tRC ${r.changeRequests}\t${r.rework ? 'sửa tiếp' : ''}\t${r.title}`);
    if (!runs.length) console.log('(Chưa có review-runs.jsonl: số lượt Codex bắt đầu được ghi từ 08.11.2026.)');
  }
}
