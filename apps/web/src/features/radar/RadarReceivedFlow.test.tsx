import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  getPublicRadarInvite,
  getReceivedRadarResult,
  getSession,
  listReceivedRadar,
  withdrawRadarByInvite,
  withdrawReceivedRadar,
  type RadarResult,
} from "../../shared/api/client";
import { PublicRadarPage } from "./PublicRadarPage";
import { RadarReceivedPage, RadarReceivedResultPage } from "./RadarReceivedPage";

vi.mock("../../shared/api/client", async (loadOriginal) => {
  const actual = await loadOriginal<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    currentSessionEpoch: vi.fn(() => "recipient-session"),
    getPublicRadarInvite: vi.fn(),
    getReceivedRadarResult: vi.fn(),
    getSession: vi.fn(),
    listReceivedRadar: vi.fn(),
    withdrawRadarByInvite: vi.fn(),
    withdrawReceivedRadar: vi.fn(),
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

function item(id: string, context: "crush" | "friend" | "partner" | "someone") {
  return { request_id: id, context, voice: "straight_warm" as const, completed_at: "2026-10-20T03:00:00Z", expires_at: "2026-11-19T03:00:00Z" };
}

function renderAt(initialEntry: string) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={<RadarReceivedPage />} path="/radar/received" />
        <Route element={<RadarReceivedResultPage />} path="/radar/received/:requestId" />
        <Route element={<PublicRadarPage />} path="/radar/i/:token" />
        <Route element={<p>Radar landing</p>} path="/radar" />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>);
}

describe("Radar results B received (P09 D2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getSession).mockResolvedValue({
      csrf_token: "csrf",
      expires_at: "2026-12-01T00:00:00Z",
      onboarding_status: "complete",
      resumed: true,
      session_epoch: "recipient-session",
      state: "active",
    });
    vi.mocked(getReceivedRadarResult).mockResolvedValue(result);
    vi.mocked(withdrawReceivedRadar).mockResolvedValue(undefined);
  });

  it("lists received results by relationship and expiry, and pages with next_before", async () => {
    vi.mocked(listReceivedRadar)
      .mockResolvedValueOnce({ items: [item("request-a", "friend")], next_before: "request-a" })
      .mockResolvedValueOnce({ items: [item("request-b", "crush")], next_before: null });
    renderAt("/radar/received");

    expect(await screen.findByRole("heading", { name: "Kết quả bạn đã nhận" })).toBeInTheDocument();
    expect(screen.getByText("Hợp gu · Bạn thân")).toBeInTheDocument();
    expect(screen.getByText(/Còn mở đến 10:00, 19\/11/)).toBeInTheDocument();
    expect(screen.getByText(/Bạn không cần nhập lại ngày sinh/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Xem thêm" }));
    expect(await screen.findByText("Hợp gu · Crush")).toBeInTheDocument();
    expect(listReceivedRadar).toHaveBeenLastCalledWith(expect.anything(), "request-a");
    expect(screen.queryByRole("button", { name: "Xem thêm" })).not.toBeInTheDocument();
  });

  it("tells B what is held about them without asking for birth data again", async () => {
    vi.mocked(listReceivedRadar).mockResolvedValueOnce({ items: [item("request-a", "friend")], next_before: null });
    renderAt("/radar/received");
    await userEvent.click(await screen.findByText("Lá đang giữ gì về bạn ở đây?"));
    expect(screen.getByText(/người mời không thấy ngày, giờ hay nơi sinh của bạn/)).toBeVisible();
    expect(screen.getByText(/giữ trong 30 ngày kể từ lúc bạn đồng ý/)).toBeVisible();
    expect(screen.queryByLabelText(/ngày sinh/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("shows the empty and error states", async () => {
    vi.mocked(listReceivedRadar).mockResolvedValueOnce({ items: [], next_before: null });
    const view = renderAt("/radar/received");
    expect(await screen.findByText("Chưa có kết quả nào bạn đã đồng ý trong 30 ngày qua.")).toBeInTheDocument();
    view.unmount();

    vi.mocked(listReceivedRadar).mockRejectedValueOnce(new Error("offline"));
    renderAt("/radar/received");
    expect(await screen.findByRole("heading", { name: "Chưa tải được danh sách." })).toBeInTheDocument();
  });

  it("opens one result and withdraws only after confirmation", async () => {
    renderAt("/radar/received/request-a");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    const sheet = await screen.findByRole("dialog");
    expect(within(sheet).getByText(/không hoàn tác được/)).toBeInTheDocument();
    await userEvent.click(within(sheet).getByRole("button", { name: "Giữ lại" }));
    expect(withdrawReceivedRadar).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("heading", { name: "Chart của bạn đã được rút." })).toBeInTheDocument();
    expect(withdrawReceivedRadar).toHaveBeenCalledWith("request-a");
  });

  it("reconciles an unconfirmed withdrawal with the server before promising anything", async () => {
    // A lost response: the server still has the reading, so the page says so only after re-reading it.
    vi.mocked(withdrawReceivedRadar).mockRejectedValueOnce(new Error("timeout"));
    renderAt("/radar/received/request-a");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa rút được chart: bản đọc vẫn còn trên máy chủ.");
    expect(screen.getByRole("button", { name: "Thử rút chart lại" })).toBeInTheDocument();
    expect(getReceivedRadarResult).toHaveBeenCalledTimes(2);
  });

  it("treats an unconfirmed withdrawal as done when the server no longer has the reading", async () => {
    vi.mocked(withdrawReceivedRadar).mockRejectedValueOnce(new Error("timeout"));
    renderAt("/radar/received/request-a");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    vi.mocked(getReceivedRadarResult).mockRejectedValue(new ApiProblem(404, "RADAR_UNAVAILABLE", "Unavailable"));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("heading", { name: "Bản đọc này không còn mở được." })).toBeInTheDocument();
    expect(screen.queryByText(result.headline)).not.toBeInTheDocument();
  });

  it("keeps a retry when both the withdrawal outcome and the re-read are inconclusive", async () => {
    // Codex r32 (P3): a POST timeout plus a transient GET failure is not a definitive denial.
    vi.mocked(withdrawReceivedRadar).mockRejectedValueOnce(new Error("timeout"));
    renderAt("/radar/received/request-a");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    vi.mocked(getReceivedRadarResult).mockRejectedValueOnce(new Error("offline"));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("heading", { name: "Chưa mở được bản đọc." })).toBeInTheDocument();
    expect(screen.queryByText(result.headline)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Thử lại/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa rút được chart: bản đọc vẫn còn trên máy chủ.");
    expect(screen.getByRole("button", { name: "Thử rút chart lại" })).toBeInTheDocument();
  });

  it("treats a definitive denial of the withdrawal as terminal even if the re-read is inconclusive", async () => {
    vi.mocked(withdrawReceivedRadar).mockRejectedValueOnce(new ApiProblem(404, "RADAR_UNAVAILABLE", "Unavailable"));
    renderAt("/radar/received/request-a");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart của tôi khỏi kết quả này" }));
    vi.mocked(getReceivedRadarResult).mockRejectedValueOnce(new Error("offline"));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("heading", { name: "Bản đọc này không còn mở được." })).toBeInTheDocument();
  });

  it("lets the holder of a used invite link withdraw without opening the reading", async () => {
    vi.mocked(getPublicRadarInvite).mockRejectedValue(new Error("not found"));
    vi.mocked(withdrawRadarByInvite).mockResolvedValueOnce(undefined);
    renderAt("/radar/i/token-123");

    expect(await screen.findByText(/Trang này không mở lại bản đọc/)).toBeInTheDocument();
    expect(screen.queryByText(result.headline)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Rút chart khỏi kết quả" }));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));

    expect(await screen.findByRole("heading", { name: "Chart của bạn đã được rút." })).toBeInTheDocument();
    expect(withdrawRadarByInvite).toHaveBeenCalledWith("token-123");
    expect(getReceivedRadarResult).not.toHaveBeenCalled();
  });

  it("says the link can no longer withdraw only on a definitive 404", async () => {
    vi.mocked(getPublicRadarInvite).mockRejectedValue(new Error("not found"));
    vi.mocked(withdrawRadarByInvite).mockRejectedValueOnce(new ApiProblem(404, "RADAR_UNAVAILABLE", "Unavailable"));
    renderAt("/radar/i/token-123");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart khỏi kết quả" }));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Link này không còn dùng được.");
  });

  it("does not claim the link failed when the withdrawal outcome is unknown", async () => {
    vi.mocked(getPublicRadarInvite).mockRejectedValue(new Error("not found"));
    vi.mocked(withdrawRadarByInvite).mockRejectedValueOnce(new Error("timeout"));
    renderAt("/radar/i/token-123");

    await userEvent.click(await screen.findByRole("button", { name: "Rút chart khỏi kết quả" }));
    await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Rút chart" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác nhận được việc rút chart.");
  });
});
