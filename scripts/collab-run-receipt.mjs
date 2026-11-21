// Run receipts (research item 3, owner approved 21.11.2026): "the code exists" and "it really ran"
// become one fact. Every real run of the loop's unattended jobs appends one receipt to
// run-receipts.jsonl on the owner's Mac: what ran, the exact commit of the code that ran (or, for
// the persona run, the integration commit it measured), when, the result and a few counts. No free
// text is kept: kinds and results come from fixed lists and counts are numbers, so a receipt can
// hold no private data. The board shows the last 24 hours, and a job with no receipt says
// "chưa chạy", never a number.
import { execFileSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { isSha, stateDir, vnNow } from './collab-trust.mjs';

export const receiptKinds = { tick: 'vòng tự động', 'night-audit': 'soát đêm', personas: 'người giả hằng đêm' };
export const receiptResults = ['ok', 'error', 'skipped'];
export const receiptsPath = () => join(stateDir, 'run-receipts.jsonl');

export function codeSha(dir = join(stateDir, 'ops'), run = execFileSync) {
  try {
    const sha = String(run('/usr/bin/git', ['-C', dir, 'rev-parse', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 10000 })).trim();
    return isSha(sha) ? sha : null;
  } catch { return null; }
}

export function writeRunReceipt({ kind, result, counts = {}, sha = codeSha(), at = new Date(), path = receiptsPath() }) {
  if (!receiptKinds[kind]) throw new Error(`unknown receipt kind: ${kind}`);
  if (!receiptResults.includes(result)) throw new Error(`unknown receipt result: ${result}`);
  const numbers = Object.fromEntries(Object.entries(counts).filter(([k, v]) => /^[a-z][a-zA-Z]{0,30}$/.test(k) && Number.isFinite(v)).slice(0, 10));
  const receipt = { at: at.toISOString(), kind, result, sha: isSha(sha) ? sha : null, counts: numbers };
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(receipt)}\n`);
  return receipt;
}

export function readReceipts(path = receiptsPath()) {
  if (!existsSync(path)) return [];
  return readFileSync(path, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
}

export function receiptSummary(receipts, { nowMs = Date.now(), hours = 24 } = {}) {
  const since = nowMs - hours * 3600000;
  const recent = receipts.filter(r => Date.parse(r.at) >= since && Date.parse(r.at) <= nowMs);
  return Object.fromEntries(Object.keys(receiptKinds).map(kind => {
    const mine = recent.filter(r => r.kind === kind);
    const ran = mine.filter(r => r.result !== 'skipped');
    const last = ran.at(-1) ?? null;
    return [kind, { runs: ran.length, errors: ran.filter(r => r.result === 'error').length, last: last ? { at: last.at, sha: last.sha } : null }];
  }));
}

const hhmm = iso => { const t = vnNow(new Date(iso)); return `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`; };
export function renderReceipts(summary, hours = 24) {
  const part = kind => {
    const s = summary[kind];
    if (!s?.runs) return `${receiptKinds[kind]}: chưa chạy`;
    const code = s.last.sha ? `, code ${s.last.sha.slice(0, 7)}` : ', không đọc được code';
    return `${receiptKinds[kind]} ${s.runs} lượt${s.errors ? ` (lỗi ${s.errors})` : ''}, lần cuối ${hhmm(s.last.at)}${code}`;
  };
  return `Đã chạy thật ${hours} giờ qua: ${Object.keys(receiptKinds).map(part).join('; ')}.`;
}
