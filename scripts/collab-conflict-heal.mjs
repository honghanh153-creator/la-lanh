// Rule-based conflicts are merged by the machine (owner plan 22.11 "cắt tự chạy và nhắn qua lại",
// item 2; L74). Before this, a PR GitHub marked CONFLICTING went straight to a Claude fix turn, and
// the auto-sync gave up on any conflict, so every lesson merged into integration woke Claude (and
// the app's Autofix) on every other open PR that also added a lesson: both PRs only appended an
// entry to scripts/collab-lessons.json. Now:
// - resolveRuleConflicts: after a failed merge, when every unmerged file has a rule here, the rule
//   writes the merged file; anything else (or a rule that finds a real clash) leaves the merge to
//   be aborted as before. The lessons rule is a union by id: an entry changed on one side only takes
//   that side; changed on both sides differently is a real clash.
// - healConflicts (tick): at most one CONFLICTING own PR per tick whose conflicting change can be a
//   rule file is merged with integration in the author clone (no install, nothing of the PR runs)
//   and pushed normally. A claimed PR is left to its session; Autofix stays on as the fallback.
import { writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { isOwnPr } from './collab-trust.mjs';
import { syncableBranch, syncWithIntegration } from './collab-heal.mjs';

export const lessonsFile = 'scripts/collab-lessons.json';
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// base/ours/theirs are the file texts at the three merge stages (null when a side has no file).
export function unionLessons(base, ours, theirs) {
  const parse = t => { if (t === null || t === undefined) return { lessons: [] }; try { const d = JSON.parse(t); return Array.isArray(d?.lessons) ? d : null; } catch { return null; } };
  const [b, o, t] = [parse(base), parse(ours), parse(theirs)];
  if (!b || !o || !t) return null;
  const { lessons: _o, ...oRest } = o;
  const { lessons: _t, ...tRest } = t;
  const { lessons: _b, ...bRest } = b;
  let rest = oRest;
  if (!same(oRest, tRest)) { if (same(oRest, bRest)) rest = tRest; else if (!same(tRest, bRest)) return null; }
  const byId = list => { const m = new Map(); for (const l of list) { if (!l || typeof l.id !== 'string' || m.has(l.id)) return null; m.set(l.id, l); } return m; };
  const [bm, om, tm] = [byId(b.lessons), byId(o.lessons), byId(t.lessons)];
  if (!bm || !om || !tm) return null;
  const out = [];
  // Integration's order first, then the branch's own new entries in its order.
  for (const id of [...tm.keys(), ...[...om.keys()].filter(id => !tm.has(id))]) {
    const [x, y, z] = [om.get(id), tm.get(id), bm.get(id)];
    if (x && y) {
      if (same(x, y) || same(z, y)) out.push(x);
      else if (same(z, x)) out.push(y);
      else return null;
    } else {
      const kept = x ?? y;
      // Present on one side only: new there (keep), or removed on the other side (drop only when
      // the kept side did not change it).
      if (!z) out.push(kept);
      else if (!same(z, kept)) return null;
    }
  }
  return `${JSON.stringify({ ...rest, lessons: out }, null, 1)}\n`;
}

export const rules = { [lessonsFile]: unionLessons };

// git(args, ms) runs in the clone; write(path, text) writes a file there. Returns the resolved files,
// or null when a conflict needs judgment (the caller aborts the merge).
export function resolveRuleConflicts({ git, write }) {
  let files;
  try { files = git(['diff', '--name-only', '--diff-filter=U'], 60000).split('\n').map(s => s.trim()).filter(Boolean); } catch { return null; }
  if (!files.length || files.some(f => !rules[f])) return null;
  const stage = (n, f) => { try { return git(['show', `:${n}:${f}`], 60000); } catch { return null; } };
  const merged = files.map(f => [f, rules[f](stage(1, f), stage(2, f), stage(3, f))]);
  if (merged.some(([, text]) => text === null)) return null;
  for (const [f, text] of merged) { write(f, text); git(['add', '--', f], 60000); }
  git(['-c', 'user.name=la-lanh-agent', '-c', 'user.email=la-lanh-agent@users.noreply.github.com', 'commit', '--no-edit', '--no-verify'], 60000);
  return files;
}

// The tick step: up to `max` CONFLICTING own PRs per tick whose files include a rule file, each in
// the author clone under the check lock (shared clone) and the PR lock (one writer per PR).
// deps: prepare(number, head) -> clone dir; mayTouch(n) -> {ok}; lock(fn); prLock(n, fn).
export const healMax = 3;
export function healCandidates(prs = []) {
  return (prs ?? []).filter(p => p?.mergeable === 'CONFLICTING' && isOwnPr(p) && syncableBranch(p.headRefName) && (p.files ?? []).some(f => rules[f.path]));
}
export function healConflicts({ gh, prs, log = () => {}, prepare, mayTouch, lock, prLock, run = execFileSync, max = healMax }) {
  const out = [];
  for (const pr of healCandidates(prs).filter(p => mayTouch(p.number).ok).slice(0, max)) {
    let result;
    try {
      result = lock(() => {
        const dir = prepare(pr.number, pr.headRefOid);
        const git = (args, ms = 120000) => String(run('/usr/bin/git', args, { cwd: dir, encoding: 'utf8', timeout: ms, maxBuffer: 64 * 1024 * 1024 })).trim();
        const resolve = () => resolveRuleConflicts({ git, write: (f, t) => writeFileSync(join(dir, f), t) });
        return prLock(pr.number, () => (mayTouch(pr.number).ok ? syncWithIntegration(pr, { git, gh, resolve }) : { status: 'claimed' }));
      });
    } catch (error) { result = { status: 'failed', reason: String(error?.message ?? error).slice(0, 200) }; }
    const status = result?.status ?? (result?.ok === false ? result.reason : 'none');
    log(`conflict heal #${pr.number}: ${status}`);
    out.push({ pr: pr.number, status, ...(result?.resolved ? { resolved: result.resolved } : {}) });
    if (status === 'busy') break; // another author check holds the clone: try next tick
  }
  return out;
}
