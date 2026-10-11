import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { listSavedNotes, type SavedNote } from "../../shared/api/client";
import { ThemeContext } from "../../shared/theme/themeContext";
import { NightNudge, WeekRecap } from "./HomeRituals";

vi.mock("../../shared/api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shared/api/client")>()),
  listSavedNotes: vi.fn(),
}));

function wrap(node: React.ReactNode, theme: "light" | "dark" = "light", setTheme = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ThemeContext.Provider value={{ theme, setTheme }}>
        <MemoryRouter>{node}</MemoryRouter>
      </ThemeContext.Provider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.mocked(listSavedNotes).mockReset();
});

describe("NightNudge", () => {
  it("offers dark mode late at night and remembers a dismissal", async () => {
    const setTheme = vi.fn();
    const late = new Date(2026, 9, 11, 22, 30);
    const { unmount } = wrap(<NightNudge now={late} />, "light", setTheme);
    await userEvent.click(screen.getByRole("button", { name: "Bật nền tối" }));
    expect(setTheme).toHaveBeenCalledWith("dark");
    unmount();
    wrap(<NightNudge now={late} />);
    expect(screen.queryByRole("button", { name: "Bật nền tối" })).not.toBeInTheDocument();
  });

  it("stays quiet during the day or when dark mode is already on", () => {
    wrap(<NightNudge now={new Date(2026, 9, 11, 15)} />);
    expect(screen.queryByText(/Khuya rồi/)).not.toBeInTheDocument();
    wrap(<NightNudge now={new Date(2026, 9, 11, 23)} />, "dark");
    expect(screen.queryByText(/Khuya rồi/)).not.toBeInTheDocument();
  });
});

describe("WeekRecap", () => {
  const sunday = new Date(2026, 9, 11, 10);
  const note = (savedAt: string) => ({ id: savedAt, daily_note_id: "n", note_snapshot: {}, saved_at: savedAt }) as unknown as SavedNote;

  it("counts only this week's saved notes on Sunday", async () => {
    vi.mocked(listSavedNotes).mockResolvedValue([note("2026-10-09T08:00:00Z"), note("2026-10-10T08:00:00Z"), note("2026-09-01T08:00:00Z")]);
    wrap(<WeekRecap now={sunday} />);
    expect(await screen.findByRole("heading", { name: "Tuần này bạn giữ lại 2 note." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Mở note đã lưu/ })).toHaveAttribute("href", "/saved");
  });

  it("does not fetch on other days", () => {
    wrap(<WeekRecap now={new Date(2026, 9, 12, 10)} />);
    expect(listSavedNotes).not.toHaveBeenCalled();
  });
});
