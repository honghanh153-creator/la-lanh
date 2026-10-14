import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  claimOwner,
  deleteRadarResult,
  getSession,
  listRadarInvites,
  OWNER_SESSION_EPOCH_KEY,
  SESSION_EPOCH_KEY,
} from "../../shared/api/client";
import { RadarStartPage } from "./RadarStartPage";

vi.mock("../../shared/api/client", async (loadOriginal) => {
  const actual = await loadOriginal<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    claimOwner: vi.fn(),
    deleteRadarResult: vi.fn(),
    getSession: vi.fn(),
    listRadarInvites: vi.fn(),
  };
});

describe("RadarStartPage delete confirmation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "session-a");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "session-a");
    sessionStorage.setItem("la-lanh-owner-session-until-v1", "2100-01-01T00:00:00Z");
    vi.mocked(getSession).mockResolvedValue({
      csrf_token: "csrf", expires_at: "2026-10-01T00:00:00Z", onboarding_status: "complete",
      resumed: true, session_epoch: "session-a", state: "active",
    });
    vi.mocked(claimOwner).mockResolvedValue({
      expires_at: "2026-10-01T00:00:00Z", principal_id: "00000000-0000-4000-8000-000000000001", resumed: true,
    });
    vi.mocked(listRadarInvites).mockResolvedValue([{
      id: "invite-1", recipient_label: "Mèo", context: "crush", voice: "straight_warm", mode: "consented_invite",
      status: "completed", created_at: "2026-10-01T00:00:00Z", expires_at: "2026-10-08T00:00:00Z",
    }]);
    vi.mocked(deleteRadarResult).mockResolvedValue(undefined);
  });

  it("asks in an in-app sheet and deletes only after an explicit Xoá", async () => {
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><RadarStartPage /></MemoryRouter></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: "Xoá lần Radar với Mèo" }));
    const sheet = screen.getByRole("dialog", { name: "Xoá lần Radar với Mèo?" });
    await user.click(within(sheet).getByRole("button", { name: "Giữ lại" }));
    expect(deleteRadarResult).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Xoá lần Radar với Mèo" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Xoá" }));
    await waitFor(() => expect(deleteRadarResult).toHaveBeenCalledWith("invite-1", expect.anything()));
  });

  it("closes the sheet and never shows A's name once the session owner changes", async () => {
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><RadarStartPage /></MemoryRouter></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: "Xoá lần Radar với Mèo" }));
    expect(screen.getByRole("dialog", { name: "Xoá lần Radar với Mèo?" })).toBeInTheDocument();

    // Another tab signed in as B: the stored epoch and the server session both change.
    sessionStorage.setItem(SESSION_EPOCH_KEY, "session-b");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "session-b");
    vi.mocked(listRadarInvites).mockResolvedValue([]);
    vi.mocked(getSession).mockResolvedValue({
      csrf_token: "csrf", expires_at: "2026-10-01T00:00:00Z", onboarding_status: "complete",
      resumed: true, session_epoch: "session-b", state: "active",
    });
    await act(async () => { await client.invalidateQueries({ queryKey: ["radar-owner-session"] }); });

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByText(/Mèo/)).not.toBeInTheDocument();
    expect(deleteRadarResult).not.toHaveBeenCalled();
  });
});
