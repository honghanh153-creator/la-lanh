import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { listLaChungInvites, revokeLaChungInvite } from "../../shared/api/client";
import { InviteHistoryPage } from "./InviteHistoryPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, listLaChungInvites: vi.fn(), revokeLaChungInvite: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><InviteHistoryPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("InviteHistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listLaChungInvites).mockResolvedValue([
      {
        id: "00000000-0000-4000-8000-000000000001",
        recipient_label: "Bạn A",
        context: "friend",
        status: "pending",
        created_at: "2026-09-01T00:00:00Z",
        expires_at: "2026-10-01T00:00:00Z",
        share_url: null,
      },
      {
        id: "00000000-0000-4000-8000-000000000002",
        recipient_label: "Bạn B",
        context: "bff",
        status: "completed",
        created_at: "2026-09-01T00:00:00Z",
        expires_at: "2026-10-01T00:00:00Z",
        share_url: null,
      },
    ]);
    vi.mocked(revokeLaChungInvite).mockResolvedValue(undefined);
  });

  it("keeps only data-management actions for legacy invites", async () => {
    const user = userEvent.setup();
    renderPage();

    await screen.findByRole("heading", { name: "Bạn A" });
    expect(screen.getByRole("button", { name: /Thu hồi lời mời/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Xem Lá Chứng" })).toHaveAttribute(
      "href",
      "/la-chung/result/00000000-0000-4000-8000-000000000002",
    );
    expect(screen.queryByRole("button", { name: /gửi lại|thay link|tạo link/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /gửi lại|thay link|tạo link/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Thu hồi lời mời/ }));
    await waitFor(() => expect(vi.mocked(revokeLaChungInvite).mock.calls[0]?.[0]).toBe(
      "00000000-0000-4000-8000-000000000001",
    ));
  });
});
