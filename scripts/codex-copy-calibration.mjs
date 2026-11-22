// Calibrating the daily copy judge to the owner (research item 7, owner approved 21.11.2026; practice:
// Hamel Husain, "LLM-as-a-Judge": show the judge labelled examples from the person it stands in for,
// then measure how often they agree).
// 1. Examples. The judge prompt (codex-copy-review.mjs buildPrompt) gets a fixed, ordered set of the
//    owner's own decisions: the sentences the content standard marks as the approved voice and the
//    ones it rejects, with the reason the standard gives, plus registry entries the owner approved
//    herself (owner-only groups excluded; they never enter the batch). The standard's text is checked
//    by a test, so an edit there that drops an example fails CI instead of drifting.
// 2. A local judge log. Each Codex batch appends its decisions (date, id, digest, decision, reason) to
//    copy-judge-log.jsonl in the state folder. It never goes into git.
// 3. Agreement. --agreement compares the log with the owner's labels in the registry: an entry she
//    approved with the text Codex saw (agree if Codex approved, Codex too strict if it rejected), or an
//    entry Codex approved that she then approved with a different text (she disagreed). An edit by an
//    agent is not her label. Under minLabels labels it says
//    "chưa đủ nhãn", never a percentage.
// Usage: node scripts/codex-copy-calibration.mjs --agreement
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';
import { digest, ownerOnly, readLocalRegistry } from './codex-copy-review.mjs';

export const standardDoc = 'docs/foundation/la-lanh-plain-vietnamese-content-standard.md';
export const judgeLogPath = () => join(stateDir, 'copy-judge-log.jsonl');
export const maxExamples = 8;
export const minLabels = 20;

// From the standard (section "Giọng direct đã chốt ngày 2026-10-07"), verbatim.
export const standardExamples = [
  { text: 'Bạn gật đầu, nhưng vẫn chưa hiểu hết.', verdict: 'approve', why: 'ví dụ chuẩn của giọng direct: có chủ thể, nói rõ việc đang xảy ra' },
  { text: 'Khi cả nhóm chốt rất nhanh, bạn có thể đồng ý theo dù vẫn còn một chỗ muốn hỏi lại.', verdict: 'approve', why: 'ví dụ chuẩn: tình huống quan sát được, không ẩn dụ' },
  { text: 'Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?', verdict: 'approve', why: 'ví dụ chuẩn: việc nhỏ làm được ngay, có động từ' },
  { text: 'Ý kiến đông người dễ nghe giống ý kiến đúng', verdict: 'reject', why: 'chuẩn loại: không có chủ thể, người đọc phải tự giải mã' },
  { text: 'Sự tự tin của người nói có thể đang được nghe như bằng chứng', verdict: 'reject', why: 'chuẩn loại: trừu tượng, không nói ai làm gì' },
];

export function calibrationExamples(registry) {
  const owner = (registry?.entries ?? []).filter(e => e.status === 'approved' && e.approver === 'owner' && !ownerOnly.has(e.category))
    .sort((a, b) => String(a.id).localeCompare(String(b.id)))
    .map(e => ({ text: e.text, verdict: 'approve', why: 'chị duyệt câu này' }));
  return [...standardExamples, ...owner].slice(0, maxExamples);
}

export function renderExamples(examples) {
  if (!examples.length) return [];
  return [
    'Ví dụ người duyệt đã chấm (học cách chấm, không duyệt lại các câu này):',
    ...examples.map(x => `- ${x.verdict === 'approve' ? 'DUYỆT' : 'LOẠI'}: "${x.text}" — ${x.why}`),
  ];
}

export function recordJudgements(decisions, reviewed, date, path = judgeLogPath()) {
  mkdirSync(dirname(path), { recursive: true });
  const lines = decisions.filter(d => reviewed.has(d.id))
    .map(d => JSON.stringify({ date, id: d.id, digest: reviewed.get(d.id), decision: d.decision, reason: String(d.reason ?? '').slice(0, 300) }));
  if (lines.length) appendFileSync(path, `${lines.join('\n')}\n`);
  return lines.length;
}

const readLog = path => (existsSync(path) ? readFileSync(path, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean) : []);

export function agreement(log, registry) {
  const entries = new Map((registry?.entries ?? []).map(e => [e.id, e]));
  const last = new Map();
  for (const j of log) last.set(j.id, j);
  const rows = [];
  for (const j of last.values()) {
    const e = entries.get(j.id);
    if (!e) continue;
    const now = digest(e.text);
    if (e.status === 'approved' && e.approver === 'owner' && now === j.digest) rows.push({ id: j.id, agree: j.decision === 'approve', kind: j.decision === 'approve' ? 'cùng duyệt' : 'Codex chặt hơn chị' });
    // Only her own approval of a different text counts; an agent edit after Codex is not her label.
    else if (e.status === 'approved' && e.approver === 'owner' && j.decision === 'approve' && now !== j.digest) rows.push({ id: j.id, agree: false, kind: 'chị duyệt câu khác câu Codex đã duyệt' });
  }
  const labels = rows.length;
  const agreed = rows.filter(r => r.agree).length;
  const byKind = rows.reduce((m, r) => ({ ...m, [r.kind]: (m[r.kind] ?? 0) + 1 }), {});
  return { judged: last.size, labels, agreed, byKind, share: labels >= minLabels ? Math.round((agreed / labels) * 1000) / 10 : null };
}

export function renderAgreement(a) {
  const kinds = Object.entries(a.byKind).map(([k, n]) => `${k}: ${n}`).join('; ') || 'chưa có';
  return a.share === null
    ? `Giám khảo câu chữ so với chị: chưa đủ nhãn (${a.labels}/${minLabels} câu có quyết định của chị; Codex đã chấm ${a.judged} câu). ${kinds}.`
    : `Giám khảo câu chữ so với chị: khớp ${a.share}% trên ${a.labels} câu. ${kinds}.`;
}

if (isMain(import.meta.url)) {
  if (process.argv.includes('--agreement')) process.stdout.write(`${renderAgreement(agreement(readLog(judgeLogPath()), readLocalRegistry()))}\n`);
  else process.stdout.write('Usage: node scripts/codex-copy-calibration.mjs --agreement\n');
}
