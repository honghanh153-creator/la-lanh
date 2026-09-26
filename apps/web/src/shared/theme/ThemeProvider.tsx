import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  applyThemePreference,
  persistThemePreference,
  readThemePreference,
  type ThemePreference,
} from "./theme";
import { ThemeContext, type ThemeContextValue } from "./themeContext";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePreference>(readThemePreference);

  useEffect(() => applyThemePreference(theme), [theme]);

  const value = useMemo<ThemeContextValue>(() => ({
    theme,
    setTheme: (nextTheme) => {
      persistThemePreference(nextTheme);
      setThemeState(nextTheme);
    },
  }), [theme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
