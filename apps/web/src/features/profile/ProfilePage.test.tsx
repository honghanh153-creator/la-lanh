import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearResonance,
  getBirthProfile,
  getBirthSupplement,
  getDailyNote,
  getResonanceStatus,
} from "../../shared/api/client";
import { ProfilePage } from "./ProfilePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    clearResonance: vi.fn(),
    getBirthProfile: vi.fn(),
    getBirthSupplement: vi.fn(),
    getDailyNote: vi.fn(),
    getResonanceStatus: vi.fn(),
  };
});

vi.mock("../../shared/theme/useTheme", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><ProfilePage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProfilePage resonance privacy controls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getBirthProfile).mockRejectedValue(new Error("not available"));
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not available"));
    vi.mocked(getDailyNote).mockRejectedValue(new Error("not available"));
    vi.mocked(getResonanceStatus).mockResolvedValue({
      consented: true,
      feedback_count: 2,
      last_choice: "hit",
    });
    vi.mocked(clearResonance).mockResolvedValue(undefined);
  });

  it("shows status and can reset feedback without revoking consent", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("Đang bật · 2 phản hồi trong 30 ngày gần nhất")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xóa phản hồi" }));

    await waitFor(() => expect(clearResonance).toHaveBeenCalledWith(false));
    expect(await screen.findByRole("status")).toHaveTextContent("Đã xóa phản hồi; quyền đồng ý vẫn được giữ");
  });

  it("requires confirmation before revoking consent and deleting feedback", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Tắt và xóa" }));

    await waitFor(() => expect(clearResonance).toHaveBeenCalledWith(true));
  });
});
