import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiProblem, getCurrentSky } from "../../shared/api/client";
import { CurrentSkyPage } from "./CurrentSkyPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getCurrentSky: vi.fn() };
});

function renderPage(fromHome = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[{
        pathname: "/insights/current-sky",
        search: "?tradition=western",
        state: fromHome ? { from: "home" } : null,
      }]}>
        <CurrentSkyPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CurrentSkyPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("returns Home visitors to Home", async () => {
    vi.mocked(getCurrentSky).mockResolvedValue({
      observed_at: "2026-09-28T00:00:00Z",
      tradition: "western",
      config_hash: "hash",
      bodies: [],
      note: "Ảnh chụp bầu trời, không phải lời phán.",
    });
    renderPage(true);

    expect(await screen.findByText("Ảnh chụp bầu trời, không phải lời phán.")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/home");
  });

  it("shows a retryable error instead of an endless loading state", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentSky)
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({
        observed_at: "2026-09-28T00:00:00Z",
        tradition: "western",
        config_hash: "hash",
        bodies: [],
        note: "Đã có dữ liệu mới.",
      });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Thử lại" }));

    expect(await screen.findByText("Đã có dữ liệu mới.")).toBeInTheDocument();
  });

  it("does not disguise a missing private session as a sky-data outage", async () => {
    vi.mocked(getCurrentSky).mockRejectedValue(
      new ApiProblem(401, "GUEST_SESSION_MISSING", "Guest session is missing"),
    );
    renderPage();

    expect(await screen.findByRole("heading", { name: "Phiên đọc đã khép lại." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mở lại Trạm Bắt Sóng" })).toHaveAttribute("href", "/welcome");
    expect(screen.queryByRole("button", { name: "Thử lại" })).not.toBeInTheDocument();
  });
});
