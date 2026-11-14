// One status board on the daily plan issue, edited in place by every tick, so the owner can see
// from a phone whether the loop is running and why it stopped (owner request 31.10.2026).
import { join } from 'node:path';
import { agentMarker, assertAgentBody, clean, codexDailyCap, isTrusted, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';

export const boardMarker = `${agentMarker} status-board -->`;

const STATES = {
  running: ['🟢 ĐANG CHẠY', ''],
  ran: ['🟢 ĐANG CHẠY', 'vừa xong một lượt, tick kế tiếp sau tối đa 10 phút'],
  'ran-with-errors': ['🟠 CHẠY CÓ LỖI', 'xem lỗi bên dưới'],
  'plan-made': ['🟡 CHỜ DUYỆT PLAN', 'plan hôm nay vừa đăng; trả lời Duyệt/Giữ, hoặc 10:00 tự chạy'],
  waiting: ['🟡 CHỜ DUYỆT PLAN', 'chưa có trả lời; 10:00 tự chạy'],
  held: ['⏸ DỪNG THEO OWNER', 'owner trả lời Giữ hôm nay'],
  closed: ['🌙 NGOÀI GIỜ', 'chạy từ 08:50 tới 23:30'],
  cap: ['⏸ HẾT LƯỢT CODEX HÔM NAY', 'còn PR chờ review; ngày mai chạy tiếp từ 08:50'],
  idle: ['⚪ HẾT VIỆC TRONG PLAN', 'Claude bổ sung việc kế tiếp từ backlog (§3.2 mục 7)'],
  error: ['🔴 LỖI', 'tick không chạy được, xem lỗi bên dưới'],
};

const cell = text => clean(text, 120).replace(/\\/g, '\\\\').replace(/\|/g, '\\|');
const hhmm = t => `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`;

const addMinutes = (t, minutes) => {
  const total = t.hour * 60 + t.minute + minutes;
  return { hour: Math.floor(total / 60) % 24, minute: total % 60 };
};

export function renderBoard({ now, status, doing = null, expectMinutes = null, area = null, turns = [], done = [], codexRuns = 0, cap = codexDailyCap, failures = 0, error = null, metrics = null }) {
  const [label, why] = STATES[status] ?? [status, ''];
  const waitingOwner = turns.filter(t => t.turn === 'hold' && /needs-owner|owner bỏ/.test(t.reason));
  const queue = turns.filter(t => t.turn !== 'hold').slice(0, 8);
  const lastDone = done.map(d => `#${d.pr} ${d.check ? `check ${d.check.status}` : d.review ? `review ${d.review.verdict ?? d.review.status}` : d.merge ? `merge ${d.merge.status}` : ''}`).join(' · ');
  return [
    '## Trạng thái vòng tự động',
    '',
    `**${label}**${doing ? ` — ${cell(doing)}` : why ? ` — ${why}` : ''}`,
    '',
    `Cập nhật lúc **${hhmm(now)} ${now.date}**. Tick chạy 10 phút một lần từ 08:50 tới 23:30.`,
    // A long check or review holds the tick, so the stale rule names its own deadline (#145 r1).
    status === 'running' && expectMinutes
      ? `Việc này có thể chạy tới khoảng **${hhmm(addMinutes(now, expectMinutes))}**. **Qua ${hhmm(addMinutes(now, expectMinutes + 10))} mà bảng chưa đổi: vòng bị kẹt hoặc Mac đang ngủ.**`
      : `**Trong giờ chạy, nếu giờ cập nhật cũ hơn 20 phút: Mac đang ngủ/tắt hoặc vòng bị kẹt.**`,
    '',
    `Nhóm đang làm: ${area ?? '—'} · Codex hôm nay: ${codexRuns}/${cap} · Lỗi liên tiếp: ${failures}`,
    ...(lastDone ? [`Lượt vừa rồi: ${cell(lastDone)}`] : []),
    ...(error ? ['', `Lỗi: \`${cell(error)}\``] : []),
    '',
    '| PR | Nhóm | Lượt kế tiếp | Lý do |',
    '|---|---|---|---|',
    ...(queue.length ? queue.map(t => `| #${t.number} | ${t.area} | ${t.turn} | ${cell(t.reason)} |`) : ['| — | — | — | Không có PR tới lượt |']),
    '',
    `Chờ owner: ${waitingOwner.length ? waitingOwner.map(t => `#${t.number}`).join(', ') : 'không có'}.`,
    // Owner 12.11.2026: outcome numbers from real sources (collab-metrics.mjs), one line each.
    ...(metrics?.length ? ['', '**Số đo**', ...metrics.map(l => `- ${l}`)] : []),
    '',
    boardMarker,
  ].join('\n');
}

// Edit the board comment in place; create it once. The comment id is cached locally.
export function upsertBoard(gh, issue, body) {
  assertAgentBody(body);
  const cache = join(stateDir, 'status-comment.json');
  let id = readJson(cache, null)?.id;
  if (!id) {
    // --slurp returns one array of pages; plain --paginate prints one JSON array per page (#145 r1).
    const comments = gh.json(['api', `repos/${repo}/issues/${Number(issue)}/comments`, '--paginate', '--slurp']).flat();
    id = comments.find(c => c.author_association === 'OWNER' && String(c.body ?? '').includes(boardMarker))?.id;
  }
  if (id) {
    try {
      gh.raw(['api', '-X', 'PATCH', `repos/${repo}/issues/comments/${Number(id)}`, '--input', '-'], JSON.stringify({ body }));
      writeJson(cache, { id });
      return id;
    } catch { /* deleted: create a new one below */ }
  }
  const created = JSON.parse(gh.raw(['api', '-X', 'POST', `repos/${repo}/issues/${Number(issue)}/comments`, '--input', '-'], JSON.stringify({ body })));
  writeJson(cache, { id: created.id });
  return created.id;
}

// Owner notes (owner 12.11.2026). Editing the board sends no notification, so the owner heard
// nothing. A NEW comment on the plan issue is posted only for: PRs merged into integration
// (one line each, batched per tick), the loop failing two ticks in a row, a PR newly labelled
// needs-owner, and a digest at about 12:00 and 22:00. Each event has a key; the keys ride in the
// comment's agent marker and in a local cache, so a re-run of a tick never posts twice.
export const notePrefix = `${agentMarker} owner-note keys=`;
export const digestHours = [12, 22];
const digestWindow = 60;

export function sentNoteKeys(comments = []) {
  const keys = new Set();
  for (const c of comments) {
    if (!isTrusted(c)) continue;
    for (const m of String(c.body ?? '').matchAll(/<!-- la-lanh-agent owner-note keys=([^\s>]+) -->/g)) m[1].split(',').forEach(k => keys.add(k));
  }
  return keys;
}

// Plain titles: no "feat(x):" prefix, one line.
export const plainTitle = title => clean(String(title ?? ''), 90).replace(/^[a-z]+(\([^)]*\))?!?:\s*/i, '').replace(/\s+/g, ' ').trim();
const named = t => `${plainTitle(t.title)} (#${t.number})`;
const list = (items, none) => (items.length ? items.map(named).join('; ') : none);

export function ownerNotes({ now, merged = [], failures = 0, streakAt = null, turns = [], planned = [], dropped = [], metrics = [], digest = true, work = null }) {
  const notes = merged.map(m => ({ key: `merged-${m.number}`, lines: [`Đã gộp vào integration: ${named(m)}.`] }));
  if (failures >= 2 && streakAt) notes.push({ key: `stuck-${now.date}-${streakAt.replace(':', '')}`, lines: [`Vòng tự động bị lỗi ${failures} lượt liền từ ${streakAt}. Chi tiết ở bảng trạng thái.`] });
  const waiting = turns.filter(t => t.turn === 'hold' && t.reason === 'needs-owner');
  for (const t of waiting) notes.push({ key: `owner-${t.number}-${String(t.head ?? '').slice(0, 7)}`, lines: [`Cần bạn xem: ${named(t)}.`] });
  const at = now.hour * 60 + now.minute;
  const slot = digest ? digestHours.find(h => at >= h * 60 && at < h * 60 + digestWindow) : undefined;
  if (slot !== undefined) {
    const picked = planned.filter(n => !dropped.includes(n));
    const doneNums = new Set(merged.map(m => m.number));
    const finished = picked.filter(n => doneNums.has(n)).length;
    const active = turns.filter(t => t.turn !== 'hold');
    notes.push({ key: `digest-${now.date}-${slot}`, lines: [
      `**Tóm tắt ${slot}:00**`,
      // L11: progress is items whose criteria are met; merges are reported on their own line.
      ...(work ? [`- ${work() ?? 'Việc đạt tiêu chí: chưa đo được.'}`, `- Đã gộp ${merged.length} PR hôm nay (số PR, không phải số việc).`]
        : [picked.length ? `- Xong: ${finished}/${picked.length} việc đã chọn hôm nay; đã gộp ${merged.length} PR.` : `- Xong: đã gộp ${merged.length} PR hôm nay.`]),
      `- Đang làm: ${list(active.slice(0, 2), 'không có')}.`,
      `- Chờ bạn: ${list(waiting, 'không có')}.`,
      `- Tiếp theo: ${active[2] ? named(active[2]) : 'Claude chọn việc kế tiếp từ backlog khi có chỗ'}.`,
      ...metrics.map(l => `- ${l}`),
    ] });
  }
  return notes;
}

export const noteCachePath = () => join(stateDir, 'owner-notes.json');

// Posts the notes whose keys were never sent, in one comment. Returns the keys posted, or null.
export function postOwnerNotes(gh, issue, notes, comments = [], { cachePath = noteCachePath() } = {}) {
  const cached = readJson(cachePath, { keys: [] }).keys ?? [];
  const sent = new Set([...sentNoteKeys(comments), ...cached]);
  const fresh = notes.filter(n => !sent.has(n.key));
  if (!fresh.length) return null;
  const keys = fresh.map(n => n.key);
  const body = [...fresh.flatMap(n => n.lines), '', `${notePrefix}${keys.join(',')} -->`].join('\n');
  gh.comment('issue', issue, body);
  writeJson(cachePath, { keys: [...cached, ...keys].slice(-500) });
  return keys;
}
