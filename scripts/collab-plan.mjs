// Daily plan gate: plan at planOpensAt and it runs at once (owner 16.11.2026); the owner may reply Giữ or Bỏ #N at any time,
// nothing new after lastStartAt (hours in collab-trust.mjs; owner 14.11.2026: 06:50, 08:00, 23:35, end 23:59).
import { join } from 'node:path';
import { agentMarker, autoStartAt, clean, codexDailyCap, cutoffAt, hhmmOf, isTrusted, lastStartAt, makeGh, parseOwnerReply, planOpensAt, readJson, repo, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const planTitle = 'Kế hoạch chạy tự động hằng ngày';
const planMarker = date => `${agentMarker} daily-plan date=${date} -->`;
const minutes = now => now.hour * 60 + now.minute;
export { autoStartAt, lastStartAt, planOpensAt };
// Owner 12.11.2026: no PR quota. The plan picks 3–5 work items, each with its source (US/AC) and
// what the user sees; progress is items done / items picked. Claude works under WIP 1 + 1
// (collab-buffer.mjs), so the plan is a short list, not a count to reach.
export const planMin = 3;
export const planMax = 5;

// Fix C (04.11.2026): the owner approves new user-facing copy and clarity-ratchet rises together
// with the plan. Detected from the PR's files: content sources, and the clarity baseline or
// exceptions file (a change there means the ratchet expects more flagged sentences).
export const copyPatterns = [
  /^apps\/api\/app\/domains\/(content|content_rewrite)\//,
  // #229: reading content that lives outside content/: the modules fallback_approval.py hashes,
  // plus the relationship knowledge base.
  /^apps\/api\/app\/domains\/radar\/reading\.py$/,
  /^apps\/api\/app\/domains\/readings\/(companion|daily_psychology|gates|renderers|voice)\.py$/,
  /^apps\/api\/app\/domains\/tarot\/(action_copy|engine|examples|knowledge|meaning_brief|phrasing|question_frame|roles|stance|variants|voice)\.py$/,
  /^apps\/api\/app\/domains\/relationships\/knowledge\.py$/,
  /^apps\/api\/app\/.*\.(json|ya?ml|md)$/,
  /^apps\/web\/src\/.*(copy|strings|messages|i18n)[^/]*\.(ts|tsx|json)$/i,
];
export const ratchetFiles = ['apps/api/scripts/content_clarity_baseline.json', 'apps/api/scripts/content_clarity_exceptions.json'];
export function copyReview(files = []) {
  const copy = files.filter(f => !/(^|\/)tests?\//.test(f) && copyPatterns.some(p => p.test(f)));
  const ratchet = files.filter(f => ratchetFiles.includes(f));
  return copy.length || ratchet.length ? { copy, ratchet } : null;
}

export const committedTurns = turns => turns.filter(t => t.turn !== 'hold').slice(0, planMax);

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
  return { state, reason: action ?? (state === 'open' ? 'auto-start' : 'waiting-owner'), plan, dropped: [...dropped].sort((a, b) => a - b) };
}

function copyLines(committed) {
  const rows = committed.map(t => [t, copyReview(t.files ?? [])]).filter(([, r]) => r).map(([t, r]) => {
    const what = [r.copy.length ? `câu mới ở ${r.copy.slice(0, 3).map(f => `\`${f}\``).join(', ')}${r.copy.length > 3 ? ` (+${r.copy.length - 3})` : ''}` : null,
      r.ratchet.length ? `clarity ratchet có thể tăng (${r.ratchet.map(f => `\`${f.split('/').at(-1)}\``).join(', ')})` : null].filter(Boolean).join('; ');
    return `- #${t.number} **cần duyệt câu**: ${what}.`;
  });
  return rows.length ? ['', '**Câu chữ cần duyệt cùng plan** (`Duyệt` là duyệt luôn các câu này; `Bỏ #N` nếu chưa muốn):', ...rows, ''] : [];
}

// One unit of the day's list (collab-quota.mjs): its PRs, or the task issue Claude still has to open.
const unitLines = (u, i) => {
  const t = u.turns?.find(x => x.turn !== 'hold') ?? u.turns?.[0];
  const head = u.prs.length ? u.prs.map(n => `#${n}`).join(', ') : `việc #${u.item} (chưa có PR, Claude mở khi còn chỗ)`;
  return [
    `${i + 1}. ${head} ${clean(t?.title ?? u.title, 90)}${u.plan7w ? ' **[Kế hoạch 7 tuần]**' : ''}`,
    `   - Nguồn / AC: ${clean(t?.source ?? (u.item ? `issue #${u.item}` : 'chưa ghi'), 160)}`,
    `   - Người dùng thấy gì: ${clean(t?.userSees ?? 'chưa ghi', 160)}`,
  ].join('\n');
};

export function renderPlan(now, turns, { codexLeft, cap = codexDailyCap, gap = null, health = [], list = null }) {
  const label = { 'claude-check': 'Claude chạy author check', 'codex-review': 'Codex review', 'claude-fix': 'Claude sửa', merge: 'Merge integration', hold: 'Giữ' };
  const committed = list ? list.items.flatMap(u => u.turns) : committedTurns(turns);
  const short = planMin - (list ? list.items.length : committed.length);
  const items = list ? list.items.map(unitLines) : committed.map((t, i) => [
    `${i + 1}. #${t.number} ${clean(t.title, 90)}`,
    `   - Nguồn / AC: ${clean(t.source ?? 'chưa ghi', 160)}`,
    `   - Người dùng thấy gì: ${clean(t.userSees ?? 'chưa ghi', 160)}`,
  ].join('\n'));
  const have7w = list ? list.items.filter(u => u.plan7w).length : 0;
  // BT1 step 0: while the open queue drains, the plan says so and never asks for new backlog work.
  const drain = list?.drain?.on ? list.drain : null;
  const quota = !list ? [] : [
    list.note,
    list.unknown ? '**Kế hoạch 7 tuần:** chưa xác định được (không đọc được nhãn), cần xem lại.'
      : `**Kế hoạch 7 tuần:** ${have7w} việc trong plan (giữ tối thiểu ${list.want}; đang sẵn sàng ${list.available7w}).${list.short7w ? ` Thiếu ${list.short7w} chỗ vì không đủ việc sẵn sàng.` : ''}`,
    ...(list.incidents?.length ? ['', '**Sự cố nghiêm trọng chen trước** (ngoài 3–5 việc, không chiếm chỗ của kế hoạch 7 tuần):', ...list.incidents.map((u, i) => unitLines(u, i))] : []),
    ...(list.incidents?.length && list.incidents.length + list.items.length > planMax ? [`Quá tải: ${list.incidents.length} sự cố cộng ${list.items.length} việc vượt ${planMax}. Owner xem có cần bỏ bớt việc không.`] : []),
    '',
  ];
  const rows = turns.map(t => `| #${t.number} | ${t.area} | ${label[t.turn] ?? t.turn} | ${clean(t.reason, 120).replace(/\\/g, '\\\\').replace(/\|/g, '\\|')} | ${clean(t.title, 90).replace(/\\/g, '\\\\').replace(/\|/g, '\\|')} |`);
  return [
    `## Plan ${now.date}`,
    '',
    'Thứ tự ưu tiên: quy trình (ops) → content → privacy → tính năng mới. Trong nhóm, PR cũ trước.',
    `Lượt Codex tự động còn hôm nay: ${codexLeft}/${cap}. Chạy tới ${hhmmOf(cutoffAt)} (không bắt đầu lượt mới sau ${hhmmOf(lastStartAt)}), không merge vào main, không deploy.`,
    // A long pause before the plan means the Mac slept or was off (retro D3, 31.10.2026).
    ...(gap ? [`**Máy không chạy tick từ ${gap.from} tới ${gap.to}** (Mac ngủ hoặc tắt), nên plan có thể trễ.`] : []),
    // Health of the unattended Claude runs (watchdog, owner 03.11.2026): a stall shows every morning.
    ...(health.length ? ['', '**Tác vụ hẹn giờ:**', ...health] : []),
    '',
    ...quota,
    ...(drain ? [`**Đang dọn PR mở:** ${drain.open} PR (từ ${drain.at} trở lên). Hôm nay không mở việc mới; chỉ làm việc đang dở, sự cố và an toàn.`, ''] : []),
    `**Việc chọn hôm nay (${planMin}–${planMax} việc):**`,
    ...(items.length ? items : ['Chưa có việc nào sẵn sàng.']),
    ...(short > 0 && !drain ? [`Còn thiếu ${short} việc so với mức ${planMin}: Claude chọn tiếp từ backlog \`auto: yes\` khi có chỗ (mỗi lúc 1 việc đang làm + 1 việc đang review), và ghi nguồn / AC cùng dòng "Người dùng thấy gì" vào issue này.`] : []),
    ...copyLines(committed),
    'Tiến độ hôm nay = việc xong / việc đã chọn (xong là đã merge vào integration). PR khác trong bảng làm nếu kịp.',
    '',
    '| PR | Nhóm | Lượt kế tiếp | Lý do | Tiêu đề |',
    '|---|---|---|---|---|',
    ...(rows.length ? rows : ['| — | — | — | Không có PR mở | — |']),
    '',
    drain ? 'Khi hàng đợi review trống, Claude sửa tiếp PR đang mở, không mở việc mới cho tới khi còn dưới ' + drain.at + ' PR.'
      : 'Khi hàng đợi review trống, Claude làm tiếp việc `auto: yes` trong backlog theo cùng thứ tự ưu tiên.',
    '',
    'Plan này chạy ngay khi đăng, không cần chị duyệt. Muốn dừng hay bỏ việc thì trả lời bằng một comment mới, bất cứ lúc nào trong ngày:',
    '- chữ `Giữ` để dừng chạy tự động hôm nay;',
    '- dòng `Bỏ #N` để bỏ PR hoặc việc N khỏi hôm nay;',
    '- chữ `Duyệt` để chạy lại sau khi đã `Giữ`.',
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
  return { issue: number, comments: issue.comments ?? [], ...planState(now, issue.comments ?? []) };
}

export function makePlan(gh, now, turns, { codexLeft, cap = codexDailyCap, gap = null, health = [], list = null }) {
  const number = planIssue(gh);
  gh.comment('issue', number, renderPlan(now, turns, { codexLeft, cap, gap, health, list }));
  return number;
}

if (isMain(import.meta.url)) {
  try {
    const status = readPlanStatus(makeGh());
    process.stdout.write(`${JSON.stringify({ issue: status.issue, state: status.state, reason: status.reason, dropped: status.dropped })}\n`);
  } catch (error) { process.stderr.write(`Plan status unavailable: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
