// Daily plan gate: 08:50 plan, owner replies Duyệt/Giữ/Bỏ #N between 9 and 10, 10:00 auto start, stop at 23:30.
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { agentMarker, clean, isTrusted, makeGh, parseOwnerReply, readJson, repo, stateDir, vnNow, writeJson } from './collab-trust.mjs';

export const planTitle = 'Kế hoạch chạy tự động hằng ngày';
const planMarker = date => `${agentMarker} daily-plan date=${date} -->`;
const minutes = now => now.hour * 60 + now.minute;
export const planOpensAt = 8 * 60 + 50;
export const autoStartAt = 10 * 60;
export const lastStartAt = 23 * 60 + 30;

export function planState(now, comments = []) {
  const at = minutes(now);
  const plan = comments.filter(c => isTrusted(c) && String(c.body ?? '').includes(planMarker(now.date))).at(-1);
  if (at < planOpensAt || at >= lastStartAt) return { state: 'closed', plan: plan ?? null, dropped: [] };
  if (!plan) return { state: 'not-made', plan: null, dropped: [] };
  let action = null;
  const dropped = new Set();
  for (const c of comments) {
    // Owner replies only: trusted, newer than today's plan, and not written by an agent script.
    if (!isTrusted(c) || String(c.createdAt) <= String(plan.createdAt) || String(c.body ?? '').includes(agentMarker)) continue;
    const reply = parseOwnerReply(c.body);
    if (!reply) continue;
    reply.dropped.forEach(n => dropped.add(n));
    if (reply.action !== 'drop') action = reply.action;
  }
  const state = action === 'hold' ? 'held' : action === 'approve' ? 'open' : at >= autoStartAt ? 'open' : 'waiting';
  return { state, reason: action ?? (state === 'open' ? 'auto-10h' : 'waiting-owner'), plan, dropped: [...dropped].sort((a, b) => a - b) };
}

export function renderPlan(now, turns, { codexLeft }) {
  const label = { 'claude-check': 'Claude chạy author check', 'codex-review': 'Codex review', 'claude-fix': 'Claude sửa', merge: 'Merge integration', hold: 'Giữ' };
  const rows = turns.map(t => `| #${t.number} | ${t.area} | ${label[t.turn] ?? t.turn} | ${clean(t.reason, 120).replace(/\|/g, '\\|')} | ${clean(t.title, 90).replace(/\|/g, '\\|')} |`);
  return [
    `## Plan ${now.date}`,
    '',
    'Thứ tự ưu tiên: quy trình (ops) → content → privacy → tính năng mới. Trong nhóm, PR cũ trước.',
    `Lượt Codex tự động còn hôm nay: ${codexLeft}/12. Chạy mỗi giờ tới 23:30, không merge vào main, không deploy.`,
    '',
    '| PR | Nhóm | Lượt kế tiếp | Lý do | Tiêu đề |',
    '|---|---|---|---|---|',
    ...(rows.length ? rows : ['| — | — | — | Không có PR mở | — |']),
    '',
    'Khi hàng đợi review trống, Claude làm tiếp việc `auto: yes` trong backlog theo cùng thứ tự ưu tiên.',
    '',
    'Trả lời bằng một comment mới trên issue này (trước 10:00 nếu muốn chặn):',
    '- chữ `Duyệt` để chạy ngay;',
    '- chữ `Giữ` để hôm nay không chạy tự động;',
    '- dòng `Bỏ #N` để bỏ PR N khỏi hôm nay.',
    'Không trả lời: 10:00 tự chạy.',
    '',
    planMarker(now.date),
  ].join('\n');
}

export function planIssue(gh) {
  const cache = join(stateDir, 'plan-issue.json');
  const cached = readJson(cache, null);
  if (cached?.number) return cached.number;
  const found = gh.json(['issue', 'list', '--repo', repo, '--state', 'open', '--label', 'daily-plan', '--limit', '5', '--json', 'number,title'])
    .find(i => i.title === planTitle);
  let number = found?.number;
  if (!number) {
    gh.raw(['label', 'create', 'daily-plan', '--repo', repo, '--color', '0E8A16', '--description', 'Plan chạy tự động hằng ngày', '--force']);
    const url = gh.raw(['issue', 'create', '--repo', repo, '--title', planTitle, '--label', 'daily-plan', '--body-file', '-'],
      `Plan hằng ngày của vòng tự động Claude ⇄ Codex. Thiết kế: docs/operations/collab-auto-loop-plan.md\n\n${agentMarker} daily-plan-hub -->`);
    number = Number(/\/issues\/(\d+)/.exec(url)?.[1]);
  }
  if (!number) throw new Error('Could not find or create the daily plan issue.');
  writeJson(cache, { number });
  return number;
}

export function readPlanStatus(gh, now = vnNow()) {
  const number = planIssue(gh);
  const issue = gh.json(['issue', 'view', String(number), '--repo', repo, '--json', 'comments']);
  return { issue: number, ...planState(now, issue.comments ?? []) };
}

export function makePlan(gh, now, turns, { codexLeft }) {
  const number = planIssue(gh);
  gh.comment('issue', number, renderPlan(now, turns, { codexLeft }));
  return number;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const status = readPlanStatus(makeGh());
    process.stdout.write(`${JSON.stringify({ issue: status.issue, state: status.state, reason: status.reason, dropped: status.dropped })}\n`);
  } catch (error) { process.stderr.write(`Plan status unavailable: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
