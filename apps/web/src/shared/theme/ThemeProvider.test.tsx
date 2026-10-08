import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "./ThemeProvider";
import { THEME_STORAGE_KEY } from "./theme";
import { useTheme } from "./useTheme";

function ThemeHarness() {
  const { theme, setTheme } = useTheme();
  return <button onClick={() => setTheme(theme === "light" ? "dark" : "light")} type="button">{theme}</button>;
}

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
  });

  it("starts in the selected cream and violet direction", () => {
    render(<ThemeProvider><ThemeHarness /></ThemeProvider>);
    expect(screen.getByRole("button", { name: "light" })).toBeVisible();
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("persists an explicit dark choice only on this device", async () => {
    const user = userEvent.setup();
    render(<ThemeProvider><ThemeHarness /></ThemeProvider>);
    await user.click(screen.getByRole("button", { name: "light" }));

    expect(screen.getByRole("button", { name: "dark" })).toBeVisible();
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
  });

  it("preserves an existing dark preference", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
    render(<ThemeProvider><ThemeHarness /></ThemeProvider>);
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
