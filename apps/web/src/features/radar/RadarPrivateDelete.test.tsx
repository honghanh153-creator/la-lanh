import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, MemoryRouter, Route, RouterProvider, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SessionBoundary } from "../../app/SessionBoundary";
import {
  claimOwner,
  deleteRadarResult,
  getRadarResult,
  getSession,
  listRadarInvites,
  OWNER_SESSION_EPOCH_KEY,
  searchBirthPlaces,
  SESSION_EPOCH_KEY,
  type GuestSession,
  type RadarResult,
} from "../../shared/api/client";
import { testLocks } from "../../shared/session/testLocks";
import { RadarResultView } from "./RadarContinuePage";
import { RadarOwnerResultPage } from "./RadarOwnerResultPage";
import { RadarPrivateStartPage } from "./RadarPrivateStartPage";

vi.mock("../../shared/api/client", async (loadOriginal) => {
  const actual = await loadOriginal<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    claimOwner: vi.fn(),
    deleteRadarResult: vi.fn(),
    getRadarResult: vi.fn(),
    getSession: vi.fn(),
    listRadarInvites: vi.fn(),
    searchBirthPlaces: vi.fn(),
  };
});

function session(epoch: string): GuestSession {
  return {
    csrf_token: "csrf", expires_at: "2100-01-01T00:00:00Z", onboarding_status: "complete",
    resumed: true, session_epoch: epoch, state: "active",
  };
}

const privateCheck = {
  id: "check-1", recipient_label: "QA tổng hợp", context: "crush", voice: "straight_warm", mode: "private_check",
  status: "completed", created_at: "2026-10-01T00:00:00Z", expires_at: "2026-10-31T00:00:00Z",
} as const;

function useOwner(epoch: string) {
  sessionStorage.setItem(SESSION_EPOCH_KEY, epoch);
  sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, epoch);
  vi.mocked(getSession).mockResolvedValue(session(epoch));
}

function renderPrivate() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><RadarPrivateStartPage /></MemoryRouter></QueryClientProvider>);
  return client;
}

describe("Radar private delete needs an in-app confirmation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    sessionStorage.setItem("la-lanh-owner-session-until-v1", "2100-01-01T00:00:00Z");
    useOwner("session-a");
    vi.mocked(claimOwner).mockResolvedValue({
      expires_at: "2100-01-01T00:00:00Z", principal_id: "00000000-0000-4000-8000-000000000001", resumed: true,
    });
    vi.mocked(listRadarInvites).mockResolvedValue([privateCheck]);
    vi.mocked(searchBirthPlaces).mockResolvedValue([]);
    vi.mocked(deleteRadarResult).mockResolvedValue(undefined);
    Object.defineProperty(Element.prototype, "scrollIntoView", { configurable: true, value: vi.fn() });
  });

  it("does not delete on the trash tap; Giữ lại keeps it, Xoá deletes it", async () => {
    const user = userEvent.setup();
    renderPrivate();

    await user.click(await screen.findByRole("button", { name: "Xóa kết quả QA tổng hợp" }));
    expect(deleteRadarResult).not.toHaveBeenCalled();
    const sheet = screen.getByRole("dialog", { name: "Xoá kết quả với QA tổng hợp?" });
    await user.click(within(sheet).getByRole("button", { name: "Giữ lại" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(deleteRadarResult).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Xóa kết quả QA tổng hợp" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Xoá" }));
    await waitFor(() => expect(deleteRadarResult).toHaveBeenCalledWith("check-1", expect.anything()));
    expect(deleteRadarResult).toHaveBeenCalledTimes(1);
  });

  it("shows when each private check deletes itself, in Vietnam time", async () => {
    renderPrivate();
    expect(await screen.findByText("Tự xoá lúc 07:00, 31/10")).toBeInTheDocument();
    expect(screen.getByText(/chỉ giữ 24 giờ để bạn mở lại; sau đó tự xoá/)).toBeInTheDocument();
    expect(screen.queryByText(/30 ngày/)).not.toBeInTheDocument();
  });

  it("closes the sheet without deleting when the owner changes", async () => {
    const user = userEvent.setup();
    const client = renderPrivate();

    await user.click(await screen.findByRole("button", { name: "Xóa kết quả QA tổng hợp" }));
    expect(screen.getByRole("dialog", { name: "Xoá kết quả với QA tổng hợp?" })).toBeInTheDocument();

    useOwner("session-b");
    vi.mocked(listRadarInvites).mockResolvedValue([]);
    await act(async () => { await client.invalidateQueries({ queryKey: ["radar-owner-session"] }); });

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByText(/QA tổng hợp/)).not.toBeInTheDocument();
    expect(deleteRadarResult).not.toHaveBeenCalled();
  });

  it("hides the sheet while the same owner is re-verified, then restores focus and Escape", async () => {
    vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const router = createMemoryRouter([
      { path: "/radar/start", element: <SessionBoundary><RadarPrivateStartPage /></SessionBoundary> },
      { path: "/welcome", element: <p>Welcome</p> },
    ], { initialEntries: ["/radar/start"] });
    render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: "Xóa kết quả QA tổng hợp" }));
    const keep = within(screen.getByRole("dialog")).getByRole("button", { name: "Giữ lại" });
    act(() => { keep.focus(); });

    let release: (value: GuestSession) => void = () => {};
    vi.mocked(getSession).mockImplementation(() => new Promise((resolve) => { release = resolve; }));
    act(() => { window.dispatchEvent(new Event("focus")); });
    expect(keep).not.toBeVisible();
    act(() => { keep.blur(); });
    expect(document.activeElement).toBe(document.body);

    await act(async () => { release(session("session-a")); await Promise.resolve(); });
    vi.mocked(getSession).mockResolvedValue(session("session-a"));
    await waitFor(() => expect(keep).toBeVisible());
    expect(document.activeElement).toBe(keep);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(deleteRadarResult).not.toHaveBeenCalled();
  });
});

function Where() {
  const location = useLocation();
  return <p data-testid="where">{location.pathname + location.hash}</p>;
}

describe("Radar owner result delete uses the same sheet", () => {
  afterEach(() => vi.unstubAllGlobals());

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    sessionStorage.setItem("la-lanh-owner-session-until-v1", "2100-01-01T00:00:00Z");
    useOwner("session-a");
    vi.mocked(claimOwner).mockResolvedValue({
      expires_at: "2100-01-01T00:00:00Z", principal_id: "00000000-0000-4000-8000-000000000001", resumed: true,
    });
    vi.mocked(deleteRadarResult).mockResolvedValue(undefined);
    // The owner view's Tarot bridge may fetch on its own; keep it off the network.
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("{}", { status: 404 }))));
    vi.mocked(getRadarResult).mockResolvedValue({
      status: "completed", mode: "private_check", recipient_label: "QA tổng hợp", headline: "Hai nhịp khác nhau",
      summary: "Tóm tắt tổng hợp.", dimensions: [], disclaimer: "Chỉ để tự soi.",
    } as unknown as Awaited<ReturnType<typeof getRadarResult>>);
  });

  it("asks before deleting a private result and never deletes on the first tap", async () => {
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/radar/result/check-1"]}><Routes>
      <Route element={<RadarOwnerResultPage />} path="/radar/result/:requestId" />
      <Route element={<Where />} path="/radar/start" />
    </Routes></MemoryRouter></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: /Xóa kết quả này/ }));
    expect(deleteRadarResult).not.toHaveBeenCalled();
    const sheet = screen.getByRole("dialog", { name: "Xoá kết quả với QA tổng hợp?" });
    await user.click(within(sheet).getByRole("button", { name: "Giữ lại" }));
    expect(deleteRadarResult).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: /Xóa kết quả này/ }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Xoá" }));
    await waitFor(() => expect(deleteRadarResult).toHaveBeenCalledWith("check-1"));
    expect(await screen.findByTestId("where")).toHaveTextContent("/radar/start#radar-history");
  });

  it.each([
    ["new 24-hour", "2026-10-20T03:00:00Z", "Bản đọc này tự xoá lúc 10:00, 20/10."],
    ["legacy 30-day", "2026-11-18T03:00:00Z", "Bản đọc này tự xoá lúc 10:00, 18/11."],
  ])("states the %s result's own expiry on v1 and v2, never a fixed 24 hours", (_kind, expiresAt, expected) => {
    const base = { mode: "private_check", recipient_label: "QA tổng hợp", expires_at: expiresAt, disclaimer: "Chỉ để tự soi." } as const;
    const v1 = { ...base, version: "radar-result-v1", headline: "Hai nhịp khác nhau", summary: "Tóm tắt tổng hợp.", dimensions: [] };
    const v2 = {
      ...base, version: "radar-result-v2", headline: "Hai nhịp khác nhau", summary: "Tóm tắt tổng hợp.", dimensions: [],
      pair_signature: { kicker: "Tín hiệu", headline: "Hai nhịp khác nhau", summary: "Tóm tắt tổng hợp." },
      compatibility_map: [{ key: "resonance", label: "Bắt sóng", value: 60, meaning: "Nghĩa tổng hợp." }],
      sections: [{ key: "flow", label: "Dòng chảy", title: "Tiêu đề tổng hợp", body: "Thân bài tổng hợp.", evidence: [] }],
    };
    for (const result of [v1, v2]) {
      const view = render(<MemoryRouter><RadarResultView onWithdraw={() => {}} ownerView result={result as unknown as RadarResult} /></MemoryRouter>);
      const note = screen.getByText(expected).closest("section");
      expect(note).toHaveTextContent("không mở lại được nữa");
      expect(screen.queryByText(/24 giờ/)).not.toBeInTheDocument();
      view.unmount();
    }
  });

  it("shows no retention note on a consented invite result or the recipient view", () => {
    const result = {
      mode: "consented_invite", recipient_label: "QA tổng hợp", expires_at: "2026-11-18T03:00:00Z", version: "radar-result-v1",
      headline: "Hai nhịp khác nhau", summary: "Tóm tắt tổng hợp.", dimensions: [], disclaimer: "Chỉ để tự soi.",
    } as unknown as RadarResult;
    const owner = render(<MemoryRouter><RadarResultView ownerView result={result} /></MemoryRouter>);
    expect(screen.queryByText(/tự xoá lúc/)).not.toBeInTheDocument();
    owner.unmount();
    render(<MemoryRouter><RadarResultView result={{ ...result, mode: "private_check" }} /></MemoryRouter>);
    expect(screen.queryByText(/tự xoá lúc/)).not.toBeInTheDocument();
  });
});
