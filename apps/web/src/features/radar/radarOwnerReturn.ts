// Remembers which Radar mode sent the owner to finish their own chart, so the
// birth flow returns them to the same mode (Radar spec §2: no automatic mode
// switching). Session storage only; it holds a mode name, never personal data.
export const RADAR_OWNER_RETURN_KEY = "la-lanh-radar-owner-start";

export type RadarOwnerMode = "invite" | "private";

export function markRadarOwnerReturn(mode: RadarOwnerMode) {
  sessionStorage.setItem(RADAR_OWNER_RETURN_KEY, mode);
}

export function readRadarOwnerReturn(): RadarOwnerMode | null {
  const value = sessionStorage.getItem(RADAR_OWNER_RETURN_KEY);
  if (value === "invite") return "invite";
  // "1" is the value written before modes were stored; it always meant private.
  if (value === "private" || value === "1") return "private";
  return null;
}

export function radarOwnerReturnPath(mode: RadarOwnerMode) {
  return mode === "invite" ? "/radar/invite" : "/radar/start";
}

export function clearRadarOwnerReturn() {
  sessionStorage.removeItem(RADAR_OWNER_RETURN_KEY);
}
