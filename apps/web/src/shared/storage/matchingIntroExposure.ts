export const MATCHING_INTRO_STORAGE_KEY = "la-lanh-matching-intro-v1";
export const MATCHING_INTRO_SESSION_KEY = "la-lanh-matching-intro-session-v1";

export type MatchingIntroVisit = 1 | 2 | 3;

type MatchingIntroRecord = {
  converted: boolean;
  visit: number;
};

const EMPTY_RECORD: MatchingIntroRecord = { converted: false, visit: 0 };

function readRecord(storage: Storage): MatchingIntroRecord {
  const raw = storage.getItem(MATCHING_INTRO_STORAGE_KEY);
  if (!raw) return EMPTY_RECORD;

  try {
    const value = JSON.parse(raw) as unknown;
    if (!value || typeof value !== "object") return EMPTY_RECORD;
    const candidate = value as Partial<MatchingIntroRecord>;
    if (
      typeof candidate.converted !== "boolean"
      || !Number.isInteger(candidate.visit)
      || candidate.visit === undefined
      || candidate.visit < 1
      || candidate.visit > 3
    ) {
      return EMPTY_RECORD;
    }
    return {
      converted: candidate.converted,
      visit: candidate.visit,
    };
  } catch {
    return EMPTY_RECORD;
  }
}

function visibleVisit(visit: number): MatchingIntroVisit {
  if (visit >= 3) return 3;
  if (visit >= 2) return 2;
  return 1;
}

export function registerMatchingIntroVisit(
  local?: Storage,
  session?: Storage,
): MatchingIntroVisit {
  try {
    const localStore = local ?? window.localStorage;
    const sessionStore = session ?? window.sessionStorage;
    const record = readRecord(localStore);
    const current = visibleVisit(record.visit);
    if (record.converted || sessionStore.getItem(MATCHING_INTRO_SESSION_KEY) === "1") {
      return current;
    }

    const next = visibleVisit(record.visit + 1);
    // Mark this session first. If session storage is unavailable, do not
    // increment persistent state repeatedly during rerenders or Strict Mode.
    sessionStore.setItem(MATCHING_INTRO_SESSION_KEY, "1");
    try {
      localStore.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({
        converted: false,
        visit: next,
      }));
    } catch {
      // Keep the session marker. A later render must stay on `current` rather
      // than retrying the write and changing copy inside the same session.
      return current;
    }
    return next;
  } catch {
    return 1;
  }
}

export function markMatchingIntroConverted(local?: Storage): void {
  try {
    const localStore = local ?? window.localStorage;
    const record = readRecord(localStore);
    localStore.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({
      converted: true,
      visit: visibleVisit(record.visit),
    }));
  } catch {
    // Conversion is a product hint, never a reason to fail profile saving.
  }
}

export function clearMatchingIntroExposure(
  local?: Storage,
  session?: Storage,
): boolean {
  let cleared = true;
  try {
    (local ?? window.localStorage).removeItem(MATCHING_INTRO_STORAGE_KEY);
  } catch {
    cleared = false;
  }
  try {
    (session ?? window.sessionStorage).removeItem(MATCHING_INTRO_SESSION_KEY);
  } catch {
    cleared = false;
  }
  return cleared;
}
