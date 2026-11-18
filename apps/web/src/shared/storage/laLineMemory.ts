// Which line Lá said last time, per Daily issue, kept on this device only (owner decision W1,
// 17.11.2026; #626). Phase 3 of the W1 plan, built to the contract Codex critiqued (run 47):
//
// - The cursor is the line's stable pair id (`la.issue.<issue>.<nn>`, or `authored` for the
//   issue's own first line), never a slot number: adding or withdrawing a pair cannot make the
//   next step land on the previous line (Codex 4, 7). Nothing here is compared numerically.
// - Each issue keeps `{ pair, day, appearance }`: the pair shown, the server's local date of that
//   Daily, and the revision it appeared in. A write for an older server day never replaces a newer
//   one, so competing tabs or a late response cannot move the memory backwards (Codex 3, 8).
// - The record is scoped to the session that wrote it; another session's record is ignored.
// - A write is owned by the call that captured `beginLaLineMemoryWrite()`. It is dropped when the
//   session changed (generation or epoch) or the memory was cleared since ("xoá lịch sử", delete
//   profile, sign-out), checked again under a Web Lock shared by all tabs, right before writing.
//
// Privacy: pair ids are catalog keys, the day is the Daily's date, the appearance is the revision
// id the app already caches with the note. No sentence text, birth data, mood or device id. It is
// never sent anywhere by this module. History clear removes it (ProfilePage); delete profile,
// sign-out and every session change remove it (clearPersonalData). A clear counter (a count
// only) stays so a late callback cannot write it back.
//
// Line selection does not read it yet: the API must first send pair ids (W1 phases 1–2).
import { currentSessionEpoch, sessionGeneration } from "../session/sessionIdentity";

export const LA_LINE_MEMORY_KEY = "la-lanh-la-line-memory-v2";
const CLEARS_KEY = "la-lanh-la-line-memory-clears-v1";
const LOCK = "la-lanh-la-line-memory-v2";
/** More issues than this are never kept; the issue seen longest ago is dropped first. */
export const MAX_LA_LINE_ISSUES = 64;
export const AUTHORED_PAIR = "authored";

const ISSUE = "[a-z][a-z0-9]*(?:-[a-z0-9]+)*";
const ISSUE_KEY = new RegExp(`^${ISSUE}$`);
const PAIR = new RegExp(`^la\\.issue\\.(${ISSUE})\\.[0-9]{2}$`);
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const APPEARANCE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const MAX_ISSUE_KEY_LENGTH = 64;

export type LaLineEntry = { pair: string; day: string; appearance: string };
type Stored = { v: 2; scope: string; issues: Record<string, LaLineEntry> };
/** Who may write, captured when the Daily request starts. */
export type LaLineWriteOwner = { sessionEpoch: string; generation: number; clears: number };

// Blocked storage (private mode, policy) must never break the screen: no epoch means no memory.
function epoch(): string | null {
  try {
    return currentSessionEpoch();
  } catch {
    return null;
  }
}

const validIssue = (value: unknown): value is string =>
  typeof value === "string" && value.length <= MAX_ISSUE_KEY_LENGTH && ISSUE_KEY.test(value);

function validEntry(issue: string, value: unknown): value is LaLineEntry {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const entry = value as Record<string, unknown>;
  if (Object.keys(entry).sort().join(",") !== "appearance,day,pair") return false;
  const pair = entry.pair;
  const pairOk = pair === AUTHORED_PAIR || (typeof pair === "string" && PAIR.exec(pair)?.[1] === issue);
  return pairOk
    && typeof entry.day === "string" && DAY.test(entry.day) && !Number.isNaN(Date.parse(`${entry.day}T00:00:00Z`))
    && typeof entry.appearance === "string" && APPEARANCE.test(entry.appearance);
}

function clearCount(): number {
  try {
    const count = Number(localStorage.getItem(CLEARS_KEY) ?? "0");
    return Number.isSafeInteger(count) && count >= 0 ? count : 0;
  } catch {
    return 0;
  }
}

/** The stored issues for `scope`, or none when storage is blocked, empty, foreign or malformed. */
function read(scope: string | null): Map<string, LaLineEntry> {
  if (!scope) return new Map();
  try {
    const raw = localStorage.getItem(LA_LINE_MEMORY_KEY);
    if (!raw) return new Map();
    const parsed = JSON.parse(raw) as Partial<Stored> | null;
    if (!parsed || parsed.v !== 2 || parsed.scope !== scope || !parsed.issues || typeof parsed.issues !== "object") {
      return new Map();
    }
    const entries = Object.entries(parsed.issues);
    if (entries.length > MAX_LA_LINE_ISSUES || !entries.every(([issue, entry]) => validIssue(issue) && validEntry(issue, entry))) {
      return new Map();
    }
    return new Map(entries);
  } catch {
    return new Map();
  }
}

function withLock(work: () => boolean): Promise<boolean> {
  if (typeof navigator !== "undefined" && typeof navigator.locks?.request === "function") {
    return navigator.locks.request(LOCK, () => work());
  }
  return Promise.resolve(work());
}

/** Capture the writer when the Daily request starts; `null` without a session. */
export function beginLaLineMemoryWrite(): LaLineWriteOwner | null {
  const sessionEpoch = epoch();
  return sessionEpoch ? { sessionEpoch, generation: sessionGeneration(), clears: clearCount() } : null;
}

const stillOwned = (owner: LaLineWriteOwner) =>
  sessionGeneration() === owner.generation
  && epoch() === owner.sessionEpoch
  && clearCount() === owner.clears;

/** The line Lá showed last for this issue in the current session, or `null`. */
export function lastLaLine(issue: string): LaLineEntry | null {
  if (!validIssue(issue)) return null;
  return read(epoch()).get(issue) ?? null;
}

/**
 * Remember the line shown for `issue`. Resolves `true` when stored; `false` when the entry is
 * malformed, the caller no longer owns the session, the memory was cleared since the call began,
 * a newer day is already stored, or storage refused. It never throws.
 */
export function rememberLaLine(owner: LaLineWriteOwner | null, issue: string, entry: LaLineEntry): Promise<boolean> {
  if (!owner || !validIssue(issue) || !validEntry(issue, entry)) return Promise.resolve(false);
  return withLock(() => {
    if (!stillOwned(owner)) return false;
    // Read-merge-write inside the lock: another tab may have written since.
    const issues = read(owner.sessionEpoch);
    const current = issues.get(issue);
    if (current && current.day > entry.day) return false;
    issues.delete(issue);
    while (issues.size >= MAX_LA_LINE_ISSUES) {
      const oldest = issues.keys().next();
      if (oldest.done) break;
      issues.delete(oldest.value);
    }
    issues.set(issue, { pair: entry.pair, day: entry.day, appearance: entry.appearance });
    try {
      const stored: Stored = { v: 2, scope: owner.sessionEpoch, issues: Object.fromEntries(issues) };
      localStorage.setItem(LA_LINE_MEMORY_KEY, JSON.stringify(stored));
      return true;
    } catch {
      return false;
    }
  }).catch(() => false);
}

/**
 * Forget every remembered line and fence writes that began before ("xoá lịch sử"). Returns
 * `false` when storage refused the removal.
 */
export function clearLaLineMemory(): boolean {
  try {
    localStorage.setItem(CLEARS_KEY, String(clearCount() + 1));
    localStorage.removeItem(LA_LINE_MEMORY_KEY);
    return true;
  } catch {
    return false;
  }
}
