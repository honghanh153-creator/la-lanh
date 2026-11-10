import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { listSavedNotes, listShareLinks, unsaveDailyNote, type SavedNote } from "../../shared/api/client";
import { SavedPage } from "./SavedPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, listSavedNotes: vi.fn(), listShareLinks: vi.fn(), unsaveDailyNote: vi.fn() };
});

// Synthetic note: invented id and prose, no real person's data.
const saved: SavedNote = {
  id: "33333333-3333-4333-8333-333333333333",
  daily_note_id: "44444444-4444-4444-8444-444444444444",
  revision_id: null,
  saved_at: "2026-11-01T08:00:00Z",
  note_snapshot: { title: "Ghi chú thử nghiệm đã lưu", body: "Đoạn văn thử nghiệm của note đã lưu." },
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter><SavedPage /></MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}

describe("SavedPage removal (PV-21)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(listShareLinks).mockResolvedValue({ items: [], next_cursor: null });
    vi.mocked(unsaveDailyNote).mockResolvedValue(undefined);
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("drops the removed note's text from the query cache even when the refetch fails", async () => {
    vi.mocked(listSavedNotes)
      .mockResolvedValueOnce([saved])
      .mockRejectedValue(new TypeError("offline"));
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const client = renderPage();

    expect(await screen.findByText("Ghi chú thử nghiệm đã lưu")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Bỏ lưu/ }));
    await act(() => vi.advanceTimersByTimeAsync(5000));

    await waitFor(() => expect(unsaveDailyNote).toHaveBeenCalledWith(saved.daily_note_id, null));
    expect(await screen.findByText("Đã bỏ lưu note.")).toBeInTheDocument();
    await waitFor(() => expect(listSavedNotes).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Ghi chú thử nghiệm đã lưu")).not.toBeInTheDocument();
    expect(JSON.stringify(client.getQueryData(["saved-notes"]) ?? [])).not.toContain("Đoạn văn thử nghiệm");
  });
});
