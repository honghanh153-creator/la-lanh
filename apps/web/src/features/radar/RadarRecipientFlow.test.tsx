import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  acceptRadarInvite,
  getCurrentRadarInvite,
  getRadarReceipt,
  getSession,
  withdrawRadarResult,
  type RadarResult,
} from "../../shared/api/client";
import { RadarContinuePage } from "./RadarContinuePage";
import { RADAR_PENDING_REQUEST_KEY } from "./radarOptions";
import { RadarReceiptPage } from "./RadarReceiptPage";

vi.mock("../../shared/api/client", async (loadOriginal) => {
  const actual = await loadOriginal<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    acceptRadarInvite: vi.fn(),
    getCurrentRadarInvite: vi.fn(),
    getRadarReceipt: vi.fn(),
    getSession: vi.fn(),
    withdrawRadarResult: vi.fn(),
  };
});

const result: RadarResult = {
  request_id: "request-a",
  mode: "consented_invite",
  version: "radar-result-v1",
  headline: "Hai bạn bắt sóng theo hai nhịp khác nhau.",
  summary: "Có lực hút và cũng có điểm cần nói rõ.",
  dimensions: [{
    key: "communication",
    label: "Giao tiếp",
    signal: "Có tín hiệu",
    body: "Hỏi thẳng sẽ dễ hiểu nhau hơn đoán ý.",
    evidence_ids: ["evidence-1"],
  }],
  strongest_contacts: [],
  disclaimer: "Dùng để soi lại trải nghiệm thật, không thay cho quyết định của bạn.",
};

function renderFlow(initialEntry: string) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<RadarContinuePage />} path="/radar/continue" />
        <Route element={<RadarReceiptPage />} path="/radar/receipt" />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>);
}

describe("Radar recipient flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.mocked(getSession).mockResolvedValue({
      csrf_token: "csrf",
      expires_at: "2026-10-01T00:00:00Z",
      onboarding_status: "complete",
      resumed: true,
      session_epoch: "recipient-session",
      state: "active",
    });
    vi.mocked(acceptRadarInvite).mockResolvedValue(result);
    vi.mocked(getRadarReceipt).mockResolvedValue(result);
    vi.mocked(withdrawRadarResult).mockResolvedValue(undefined);
  });

  it("blocks consent when another tab has rebound the invitation cookie", async () => {
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "request-a");
    vi.mocked(getCurrentRadarInvite).mockResolvedValue({
      request_id: "request-b",
      recipient_label: "Lời mời B",
      context: "friend",
      voice: "straight_warm",
      expires_at: "2026-09-30T00:00:00Z",
      consent_version: "radar-pair-v1",
      requires_exact_birth_profile: true,
      privacy_note: "private",
    });
    renderFlow("/radar/continue");

    expect(await screen.findByRole("heading", { name: "Đây là một lời mời khác." })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /bật Radar/i })).not.toBeInTheDocument();
  });

  it("accepts only the bound invitation and opens the durable receipt page", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "request-a");
    vi.mocked(getCurrentRadarInvite).mockResolvedValue({
      request_id: "request-a",
      recipient_label: "Mèo",
      context: "crush",
      voice: "straight_warm",
      expires_at: "2026-09-30T00:00:00Z",
      consent_version: "radar-pair-v1",
      requires_exact_birth_profile: true,
      privacy_note: "private",
    });
    renderFlow("/radar/continue");

    await user.click(await screen.findByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Đồng ý & bật Radar" }));
    expect(await screen.findByRole("heading", { name: result.headline })).toBeInTheDocument();
    expect(acceptRadarInvite).toHaveBeenCalledWith("request-a");
    expect(getRadarReceipt).toHaveBeenCalled();
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBeNull();
  });

  it("lets the recipient reopen and withdraw the result", async () => {
    const user = userEvent.setup();
    renderFlow("/radar/receipt");

    expect(await screen.findByRole("heading", { name: result.headline })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    expect(await screen.findByRole("heading", { name: "Chart của bạn đã được rút." })).toBeInTheDocument();
    expect(withdrawRadarResult).toHaveBeenCalledWith("request-a");
  });
});
