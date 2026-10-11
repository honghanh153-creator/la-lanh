// App "vibe" and companion choice: device-only presentation preferences.
// They change wording and visuals, never the meaning of a reading, and are
// not sent anywhere except as the reading voice the user picked.
export type AppVibe = "direct" | "roast";
export type CompanionStyle = "sky" | "aura";

export const VIBE_STORAGE_KEY = "la-lanh-vibe-v1";
export const COMPANION_STORAGE_KEY = "la-lanh-companion-style-v1";

export const VIBE_LABEL: Record<AppVibe, { title: string; hint: string; emoji: string }> = {
  direct: { title: "Thẳng & dễ hiểu", hint: "Nói rõ, nhẹ nhàng, dễ làm theo.", emoji: "🌿" },
  roast: { title: "Cà khịa", hint: "Cà khịa thân thiện, chọc đúng chỗ, vẫn có lối ra.", emoji: "🔥" },
};

export const COMPANION_LABEL: Record<CompanionStyle, { title: string; hint: string }> = {
  sky: { title: "Cửa sổ trời", hint: "Cây nhỏ sống trong một ô trời thật, đổi theo giờ." },
  aura: { title: "Mầm Aura", hint: "Mầm jelly có hào quang, nảy theo nhịp của bạn." },
};

function read<T extends string>(key: string, allowed: readonly T[]): T | null {
  try {
    const value = localStorage.getItem(key);
    return allowed.includes(value as T) ? (value as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* Preference still applies for this visit. */ }
}

export function readVibe(): AppVibe {
  return read(VIBE_STORAGE_KEY, ["direct", "roast"] as const) ?? "direct";
}

/** Null until the user has picked a companion, so Home can offer the choice once. */
export function readCompanionStyle(): CompanionStyle | null {
  return read(COMPANION_STORAGE_KEY, ["sky", "aura"] as const);
}

export function applyVibe(vibe: AppVibe): void {
  document.documentElement.dataset.vibe = vibe;
}

export function persistVibe(vibe: AppVibe): void {
  write(VIBE_STORAGE_KEY, vibe);
  applyVibe(vibe);
}

export function persistCompanionStyle(style: CompanionStyle): void {
  write(COMPANION_STORAGE_KEY, style);
}
