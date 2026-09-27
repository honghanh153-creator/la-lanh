import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  claimOwner,
  getSession,
  listRadarInvites,
  OWNER_SESSION_EPOCH_KEY,
  searchBirthPlaces,
  SESSION_EPOCH_KEY,
} from "../../shared/api/client";
import { RadarPrivateStartPage } from "./RadarPrivateStartPage";

vi.mock("../../shared/api/client", async (loadOriginal) => {
  const actual = await loadOriginal<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    claimOwner: vi.fn(),
    getSession: vi.fn(),
    createPrivateRadarCheck: vi.fn(),
    deleteRadarResult: vi.fn(),
    listRadarInvites: vi.fn(),
    searchBirthPlaces: vi.fn(),
  };
});

describe("RadarPrivateStartPage", () => {
  const scrollIntoView = vi.fn();
  const originalScrollIntoView = Object.getOwnPropertyDescriptor(Element.prototype, "scrollIntoView");

  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "session-a");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "session-a");
    vi.mocked(getSession).mockResolvedValue({
      csrf_token: "csrf",
      expires_at: "2026-10-01T00:00:00Z",
      onboarding_status: "complete",
      resumed: true,
      session_epoch: "session-a",
      state: "active",
    });
    vi.mocked(claimOwner).mockResolvedValue({
      expires_at: "2026-10-01T00:00:00Z",
      principal_id: "00000000-0000-4000-8000-000000000001",
      resumed: true,
    });
    vi.mocked(listRadarInvites).mockResolvedValue([]);
    vi.mocked(searchBirthPlaces).mockResolvedValue([]);
    scrollIntoView.mockReset();
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });
  });

  afterEach(() => {
    if (originalScrollIntoView) {
      Object.defineProperty(Element.prototype, "scrollIntoView", originalScrollIntoView);
    } else {
      Reflect.deleteProperty(Element.prototype, "scrollIntoView");
    }
  });

  it("makes direct private input the primary flow and keeps invitation secondary", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><RadarPrivateStartPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Check kín một người bạn đã biết." })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /Check kín ngay/ })).toBeDisabled();
    expect(screen.getByText(/Ngày, giờ và nơi sinh không được lưu/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mời họ tự nhập" })).toHaveAttribute("href", "/radar/invite");
    expect(screen.getByRole("navigation", { name: "Tiến độ Radar" })).toBeInTheDocument();
    expect(screen.getByText("Thông tin").closest('[aria-current="step"]')).toBeInTheDocument();
    expect(document.querySelector("#radar-history")).toBeInTheDocument();
  });

  it("moves returning users to their Radar history from the result CTA", async () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/radar/start#radar-history"]}><RadarPrivateStartPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
  });

  it("opens all 34 current birthplace units without calling an external geocoder", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter><RadarPrivateStartPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    await user.click(await screen.findByRole("button", { name: "Xem đủ 34 tỉnh/thành" }));

    await waitFor(() => expect(searchBirthPlaces).toHaveBeenCalledWith("", expect.any(AbortSignal)));
    expect(screen.getByRole("button", { name: "Thu gọn danh mục" })).toBeVisible();
  });

  it("never renders cached Radar history while binding a different guest session", () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "new-session");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "old-session");
    vi.mocked(claimOwner).mockImplementation(() => new Promise(() => undefined));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(["radar-invites"], [{
      id: "old-private-result",
      recipient_label: "Old private result",
      context: "crush",
      mode: "private_check",
      status: "completed",
    }]);

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><RadarPrivateStartPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.queryByText("Old private result")).not.toBeInTheDocument();
    expect(screen.getByText("Đang nối Radar với phiên chart hiện tại…")).toBeInTheDocument();
  });
});
