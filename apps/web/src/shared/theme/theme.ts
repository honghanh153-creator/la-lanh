export type ThemePreference = "light" | "dark";

export const THEME_STORAGE_KEY = "la-lanh-theme-v1";

export function readThemePreference(): ThemePreference {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyThemePreference(theme: ThemePreference): void {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute(
    "content",
    theme === "dark" ? "#080b24" : "#f3eff9",
  );
}

export function persistThemePreference(theme: ThemePreference): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Theme is a progressive enhancement; the app still works without storage.
  }
  applyThemePreference(theme);
}
