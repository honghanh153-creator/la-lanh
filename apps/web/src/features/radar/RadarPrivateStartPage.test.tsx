import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  claimOwner,
  createPrivateRadarCheck,
  getBirthSupplement,
  getRadarConsentOptions,
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
    getBirthSupplement: vi.fn(),
    getRadarConsentOptions: vi.fn(),
    listRadarInvites: vi.fn(),
    searchBirthPlaces: vi.fn(),
  };
});

function supplement(profileLevel: 1 | 2 | 3) {
  const full = profileLevel === 3;
  return {
    profile_id: "00000000-0000-4000-8000-0000000000aa",
    profile_level: profileLevel,
    time_precision: full ? "exact" : "unknown",
    birth_time_mode: full ? "exact" : "unknown",
    approx_window: null,
    place_display_name: full ? "Thành phố mẫu" : null,
    timezone_id: full ? "Asia/Ho_Chi_Minh" : null,
  } as Awaited<ReturnType<typeof getBirthSupplement>>;
}

const SWITCHED_OFF = { invite_first: false, sentences: {}, authorized_input_version: "radar-authorized-input-v1", date_consent_version: "radar-pair-date-v1" };
// Test stand-ins only: the real sentences are owner-only and served by the server once approved.
const APPROVED = {
  invite_first: true,
  sentences: {
    "owner-invite-heading": "Câu mời A.", "owner-invite-body": "Câu mời B.",
  },
  authorized_input_version: "radar-authorized-input-v2",
  date_consent_version: "radar-pair-date-v1",
};

function renderPage(queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><RadarPrivateStartPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RadarPrivateStartPage", () => {
  const scrollIntoView = vi.fn();
  const originalScrollIntoView = Object.getOwnPropertyDescriptor(Element.prototype, "scrollIntoView");

  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "session-a");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "session-a");
    sessionStorage.setItem("la-lanh-owner-session-until-v1", "2100-01-01T00:00:00Z");
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
    vi.mocked(getBirthSupplement).mockResolvedValue(supplement(3));
    vi.mocked(getRadarConsentOptions).mockResolvedValue(SWITCHED_OFF);
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

  // Owner AP2 (21.11.2026): no "this person agreed" tick on any path; a pair is read only when the
  // other person types their own birth date through the link.
  it("leads to the invite with the owner-approved sentences and asks nothing about the other person", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue(APPROVED);
    renderPage();

    expect(await screen.findByRole("heading", { name: "Câu mời A." })).toBeInTheDocument();
    expect(screen.getByText("Câu mời B.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Gửi link mời/ })).toHaveAttribute("href", "/radar/invite");
    expect(screen.getByRole("heading", { name: "Xem hợp gu với một người bạn đã biết." })).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Xem hợp gu$/ })).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/đã cho phép|xác nhận|không gửi thông báo/i);
    expect(createPrivateRadarCheck).not.toHaveBeenCalled();
  });

  it("keeps the plain invite link while the server serves no approved sentence", async () => {
    renderPage();
    expect(await screen.findByRole("link", { name: "Mời họ tự nhập" })).toHaveAttribute("href", "/radar/invite");
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("does not block a date-only owner", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue(APPROVED);
    vi.mocked(getBirthSupplement).mockResolvedValue(supplement(1));
    renderPage();
    expect(await screen.findByRole("link", { name: /Gửi link mời/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Thêm giờ & nơi sinh của mình" })).not.toBeInTheDocument();
  });

  it("moves returning users to their Radar history from the result CTA", async () => {
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={["/radar/start#radar-history"]}><RadarPrivateStartPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
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
    expect(screen.getByText("Đang mở hồ sơ của bạn…")).toBeInTheDocument();
  });
});
