import {
  clearActiveDailyReading,
  OWNER_SESSION_EPOCH_KEY,
  SESSION_EPOCH_KEY,
} from "../api/client";
import { clearMatchingIntroExposure } from "./matchingIntroExposure";
import { clearCachedDailyNote } from "./noteCache";
import { clearLocalSavedNotes } from "./savedNoteCache";
import { clearSavedNoteMutationQueue } from "./savedNoteMutationQueue";
import { RADAR_PENDING_REQUEST_KEY } from "../../features/radar/radarOptions";

export const PERSONAL_DATA_CLEARED_EVENT = "la-lanh-personal-data-cleared";

const PERSONAL_LOCAL_KEYS = [
  "la-lanh-pending-mood-v1",
  "la-lanh-birth-supplement-snooze-until",
  "la-lanh-native-csrf-v1",
] as const;

const PERSONAL_LOCAL_KEY_PREFIXES = [
  "la-lanh-aura-transition-ack-v1:",
] as const;

// CacheStorage currently contains only public app-shell resources. Add an
// exact cache name here if a future feature persists personal responses.
const PERSONAL_CACHE_NAMES: readonly string[] = [];

export async function clearPersonalDataOnDevice(): Promise<void> {
  const failures: unknown[] = [];
  const attempt = (operation: () => void) => {
    try {
      operation();
    } catch (error) {
      failures.push(error);
    }
  };

  attempt(clearActiveDailyReading);
  attempt(clearCachedDailyNote);
  attempt(clearLocalSavedNotes);
  attempt(clearSavedNoteMutationQueue);
  attempt(() => {
    if (!clearMatchingIntroExposure()) {
      throw new Error("Matching intro storage could not be cleared");
    }
  });
  for (const key of PERSONAL_LOCAL_KEYS) {
    attempt(() => localStorage.removeItem(key));
  }
  attempt(() => {
    for (let index = localStorage.length - 1; index >= 0; index -= 1) {
      const key = localStorage.key(index);
      if (key && PERSONAL_LOCAL_KEY_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        localStorage.removeItem(key);
      }
    }
  });
  attempt(() => sessionStorage.removeItem("la-lanh-guest-create-key"));
  attempt(() => sessionStorage.removeItem(SESSION_EPOCH_KEY));
  attempt(() => sessionStorage.removeItem(OWNER_SESSION_EPOCH_KEY));
  attempt(() => sessionStorage.removeItem("la-lanh-radar-pending"));
  attempt(() => sessionStorage.removeItem(RADAR_PENDING_REQUEST_KEY));
  attempt(() => sessionStorage.removeItem("la-lanh-radar-owner-start"));

  if ("caches" in window) {
    const results = await Promise.allSettled(
      PERSONAL_CACHE_NAMES.map((name) => window.caches.delete(name)),
    );
    for (const result of results) {
      if (result.status === "rejected") failures.push(result.reason);
    }
  }

  window.dispatchEvent(new Event(PERSONAL_DATA_CLEARED_EVENT));
  if (failures.length > 0) {
    const first = failures[0];
    throw first instanceof Error ? first : new Error("Some personal data could not be cleared");
  }
}
