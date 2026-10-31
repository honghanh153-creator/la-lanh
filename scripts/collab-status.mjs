// One status board on the daily plan issue, edited in place by every tick, so the owner can see
// from a phone whether the loop is running and why it stopped (owner request 31.10.2026).
import { join } from 'node:path';
import { agentMarker, assertAgentBody, clean, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';

export const boardMarker = `${agentMarker} status-board -->`;

const STATES = {
  running: ['🟢 ĐANG CHẠY', ''],
  ran: ['🟢 ĐANG CHẠY', 'vừa xong một lượt, tick kế tiếp sau tối đa 10 phút'],
  'ran-with-errors': ['🟠 CHẠY CÓ LỖI', 'xem lỗi bên dưới'],
  'plan-made': ['🟡 CHỜ DUYỆT PLAN', 'plan hôm nay vừa đăng; trả lời Duyệt/Giữ, hoặc 10:00 tự chạy'],
  waiting: ['🟡 CHỜ DUYỆT PLAN', 'chưa có trả lời; 10:00 tự chạy'],
  held: ['⏸ DỪNG THEO OWNER', 'owner trả lời Giữ hôm nay'],
  closed: ['🌙 NGOÀI GIỜ', 'chạy từ 08:50 tới 23:30'],
  idle: ['⚪ KHÔNG CÓ VIỆC', 'không PR nào đang tới lượt máy làm'],
  error: ['🔴 LỖI', 'tick không chạy được, xem lỗi bên dưới'],
};

const cell = text => clean(text, 120).replace(/\|/g, '\\|');
const hhmm = t => `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`;

export function renderBoard({ now, status, doing = null, area = null, turns = [], done = [], codexRuns = 0, cap = 12, failures = 0, error = null }) {
  const [label, why] = STATES[status] ?? [status, ''];
  const waitingOwner = turns.filter(t => t.turn === 'hold' && /needs-owner|owner bỏ/.test(t.reason));
  const queue = turns.filter(t => t.turn !== 'hold').slice(0, 8);
  const lastDone = done.map(d => `#${d.pr} ${d.check ? `check ${d.check.status}` : d.review ? `review ${d.review.verdict ?? d.review.status}` : d.merge ? `merge ${d.merge.status}` : ''}`).join(' · ');
  return [
    '## Trạng thái vòng tự động',
    '',
    `**${label}**${doing ? ` — ${cell(doing)}` : why ? ` — ${why}` : ''}`,
    '',
    `Cập nhật lúc **${hhmm(now)} ${now.date}**. Tick chạy 10 phút một lần từ 08:50 tới 23:30. **Nếu giờ cập nhật cũ hơn 20 phút trong giờ chạy: Mac đang ngủ/tắt hoặc vòng bị kẹt.**`,
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
    const comments = gh.json(['api', `repos/${repo}/issues/${Number(issue)}/comments`, '--paginate']);
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
