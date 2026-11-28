// Shared progress board on the owner's Mac (owner plan 22.11 "cắt tự chạy và nhắn qua lại", item 4;
// L75). Sessions write where their item stands here instead of messaging the coordinator; the
// scheduled reports read it (`collab-turn.mjs --report`, which ops-run.sh `report` runs). An
// immediate message is only for a blocked item or a decision (`needsMessage`).
// One file per item: state/progress/<key>.json = {key, status, note, next, pr, session, at}.
// Local only: notes are short technical text (no personal data, no amounts: R14), never posted by
// this module.
import { existsSync, mkdirSync, readdirSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { clean, readJson, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const STATUS = { working: 'đang làm', waiting: 'đang chờ', blocked: 'bị kẹt', decision: 'cần quyết định', done: 'xong' };
export const staleMs = 3 * 3600 * 1000;
export const doneKeepMs = 24 * 3600 * 1000;
export const progressDir = (home = stateDir) => join(home, 'state', 'progress');
const keyPattern = /^[A-Za-z0-9][\w.-]{0,59}$/;
export const needsMessage = status => status === 'blocked' || status === 'decision';

export function setProgress({ key, status, note = '', next = '', pr = null, session = process.env.LA_LANH_SESSION ?? null, now = new Date(), home = stateDir }) {
  if (!keyPattern.test(String(key ?? ''))) throw new Error('key: chữ, số, . _ - (tối đa 60)');
  if (!STATUS[status]) throw new Error(`status: ${Object.keys(STATUS).join('|')}`);
  const n = pr === null || pr === undefined || pr === '' ? null : Number(pr);
  if (n !== null && !(Number.isInteger(n) && n > 0)) throw new Error('pr: số PR');
  const entry = { key, status, note: clean(String(note ?? '').replace(/\s+/g, ' ').trim(), 200), next: clean(String(next ?? '').replace(/\s+/g, ' ').trim(), 200), pr: n, session: session ? clean(session, 60) : null, at: now.toISOString() };
  const dir = progressDir(home);
  mkdirSync(dir, { recursive: true });
  const tmp = join(dir, `.${key}.${process.pid}.tmp`);
  writeFileSync(tmp, `${JSON.stringify(entry)}\n`);
  renameSync(tmp, join(dir, `${key}.json`)); // atomic: a reader never sees half a file
  return { entry, message: needsMessage(status) };
}

// Open items first (blocked, decision, working, waiting), then today's done; done older than a day
// and unreadable files are left out. An open item not updated for 3 hours is marked old.
export function readProgress({ home = stateDir, now = new Date() } = {}) {
  const dir = progressDir(home);
  if (!existsSync(dir)) return [];
  const order = ['blocked', 'decision', 'working', 'waiting', 'done'];
  return readdirSync(dir).filter(f => f.endsWith('.json') && !f.startsWith('.')).flatMap(f => {
    const e = readJson(join(dir, f), null);
    const at = Date.parse(e?.at ?? '');
    if (!e || !STATUS[e.status] || !Number.isFinite(at)) return [];
    const age = now.getTime() - at;
    if (e.status === 'done' && age > doneKeepMs) return [];
    return [{ ...e, old: e.status !== 'done' && age > staleMs }];
  }).sort((a, b) => order.indexOf(a.status) - order.indexOf(b.status) || String(b.at).localeCompare(String(a.at)));
}

const hhmm = iso => new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(iso));
export function progressLines(entries) {
  if (!entries.length) return ['Tiến độ các phiên: chưa phiên nào ghi'];
  return ['Tiến độ các phiên (bảng chung):', ...entries.map(e => `- ${e.key}${e.pr ? ` (#${e.pr})` : ''}: ${STATUS[e.status]}${needsMessage(e.status) ? ' ⚠️' : ''}${e.note ? ` — ${e.note}` : ''}${e.next ? `; tiếp: ${e.next}` : ''} (cập nhật ${hhmm(e.at)}${e.old ? ', cũ hơn 3 giờ' : ''})`)];
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const opt = name => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
  try {
    if (args.includes('--set')) {
      const { entry, message } = setProgress({ key: opt('--set'), status: opt('--status'), note: opt('--note'), next: opt('--next'), pr: opt('--pr') });
      process.stdout.write(`${JSON.stringify(entry)}\n${message ? 'Mục này bị kẹt hoặc cần quyết định: nhắn phiên điều phối ngay.\n' : 'Đã ghi; không cần nhắn ai.\n'}`);
    } else {
      const entries = readProgress();
      process.stdout.write(`${args.includes('--json') ? JSON.stringify(entries, null, 1) : progressLines(entries).join('\n')}\n`);
    }
  } catch (error) { process.stderr.write(`collab-progress: ${clean(error.message, 300)}\n`); process.exitCode = 2; }
}
