import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  cancelHumanTarotRequest,
  createHumanTarotRequest,
  getHumanTarotAvailability,
  getHumanTarotRequest,
  getSession,
  type HumanTarotAvailability,
  type HumanTarotRequest,
} from "../../shared/api/client";
import { HumanTarotRequestPage } from "./HumanTarotRequestPage";
import { TarotPage } from "./TarotPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    cancelHumanTarotRequest: vi.fn(),
    createHumanTarotRequest: vi.fn(),
    createTarotGuest: vi.fn(),
    getHumanTarotAvailability: vi.fn(),
    getHumanTarotRequest: vi.fn(),
    getSession: vi.fn(),
  };
});

const QUESTION = "Mình cần nhìn rõ điều gì trước khi nhận thêm việc?";
const OPEN: HumanTarotAvailability = {
  enabled: true,
  accepting: true,
  reason: "open",
  local_date: "2026-10-30",
  closes_at: "2026-10-30T02:00:00Z",
  release_at: "2026-10-30T03:00:00Z",
  daily_limit: 10,
  remaining: 7,
  consent_version: "human-tarot-v1",
  current_request_id: null,
};
const WAITING: HumanTarotRequest = {
  id: "5d0f6f0e-9a0c-4a59-a8a1-0d6f2e1b7c11",
  status: "waiting",
  delivery: "pending",
  copy_cleared: null,
  local_date: "2026-10-30",
  release_at: "2026-10-30T03:00:00Z",
  context: "work",
  spread: "three_card",
  question: QUESTION,
  result: null,
  expires_at: "2026-11-29T03:00:00Z",
};
const CARD = {
  arcana: "major" as const,
  core: "hy vọng",
  tension: "chờ đợi",
  resource: "tin",
  source_concept_ids: [],
};

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/tarot" element={<TarotPage />} />
          <Route path="/tarot/nguoi-boc/:requestId" element={<HumanTarotRequestPage />} />
          <Route path="/welcome" element={<p>Start safely</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function typeQuestion() {
  const user = userEvent.setup();
  await user.type(screen.getByRole("textbox", { name: /Câu hỏi của bạn/ }), QUESTION);
  return user;
}

describe("human Tarot option on /tarot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();
    vi.mocked(getSession).mockResolvedValue({ session_epoch: null } as never);
  });

  it("stays hidden while the reader is switched off", async () => {
    vi.mocked(getHumanTarotAvailability).mockResolvedValue({ ...OPEN, enabled: false, accepting: false, reason: "disabled" });
    renderAt("/tarot");
    await waitFor(() => expect(getHumanTarotAvailability).toHaveBeenCalled());
    expect(screen.queryByRole("group", { name: "Cách bốc bài" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xòe 3 lá" })).toBeInTheDocument();
  });

  it("asks for its own consent and sends once per draft", async () => {
    vi.mocked(getHumanTarotAvailability).mockResolvedValue(OPEN);
    vi.mocked(createHumanTarotRequest)
      .mockRejectedValueOnce(new TypeError("network"))
      .mockResolvedValueOnce(WAITING);
    vi.mocked(getHumanTarotRequest).mockResolvedValue(WAITING);
    renderAt("/tarot");
    const user = await typeQuestion();
    await user.click(await screen.findByRole("button", { name: /Nhờ người bốc/ }));
    expect(screen.queryByRole("button", { name: /Xòe 3 lá/, hidden: true })).not.toBeInTheDocument();
    expect(screen.getByText(/Tối đa 10 lượt\/ngày · Trả bài lúc 10:00 hôm nay/)).toBeInTheDocument();
    expect(screen.getByText(/còn 7 lượt/)).toBeInTheDocument();
    const send = screen.getByRole("button", { name: "Gửi cho người bốc" });
    const consent = screen.getByRole("checkbox", { name: /đồng ý để người bốc/ });
    expect(consent).not.toBeChecked();
    expect(send).toBeDisabled();
    await user.click(consent);
    await user.click(send);
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa gửi được");
    await user.click(screen.getByRole("button", { name: "Gửi cho người bốc" }));
    expect(await screen.findByRole("heading", { name: /Đã nhận câu hỏi · Hẹn bạn lúc 10:00, 30\/10/ })).toBeInTheDocument();
    const [first, second] = vi.mocked(createHumanTarotRequest).mock.calls.map(([body]) => body);
    expect(first).toMatchObject({ context: "general", question: QUESTION, spread: "three_card", consent_version: "human-tarot-v1" });
    expect(second.idempotency_key).toBe(first.idempotency_key); // a retry takes no second slot
    expect(JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage })).not.toContain("nhận thêm việc");
  });

  it.each([
    [{ reason: "full" as const, accepting: false, remaining: 0 }, "Hôm nay đã đủ 10 lượt. Bạn có thể quay lại ngày mai hoặc tự bốc ngay."],
    [{ reason: "closed" as const, accepting: false }, "Hôm nay đã ngừng nhận lượt. Ngày mai bạn quay lại nhé."],
  ])("explains when no slot is left (%o)", async (overrides, message) => {
    vi.mocked(getHumanTarotAvailability).mockResolvedValue({ ...OPEN, ...overrides });
    renderAt("/tarot");
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Nhờ người bốc/ }));
    expect(screen.getByRole("status")).toHaveTextContent(message);
    expect(screen.queryByRole("button", { name: "Gửi cho người bốc" })).not.toBeInTheDocument();
  });

  it("links to today's request instead of offering a second one", async () => {
    vi.mocked(getHumanTarotAvailability).mockResolvedValue({ ...OPEN, reason: "already_requested", accepting: false, current_request_id: WAITING.id });
    renderAt("/tarot");
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Nhờ người bốc/ }));
    expect(screen.getByRole("link", { name: /Xem yêu cầu hôm nay/ })).toHaveAttribute("href", `/tarot/nguoi-boc/${WAITING.id}`);
  });

  it("goes to the restart page when the browser session changed", async () => {
    vi.mocked(getHumanTarotAvailability).mockResolvedValue(OPEN);
    vi.mocked(createHumanTarotRequest).mockRejectedValue(new ApiProblem(401, "SESSION_CHANGED", "x"));
    renderAt("/tarot");
    const user = await typeQuestion();
    await user.click(await screen.findByRole("button", { name: /Nhờ người bốc/ }));
    await user.click(screen.getByRole("checkbox", { name: /đồng ý để người bốc/ }));
    await user.click(screen.getByRole("button", { name: "Gửi cho người bốc" }));
    expect(await screen.findByText("Start safely")).toBeInTheDocument();
  });
});

describe("human Tarot request page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each([
    ["pending" as const, "Đang chuyển tới người bốc."],
    ["delivered" as const, "Người bốc đã nhận câu hỏi."],
    ["error" as const, "Chưa chuyển được tới người bốc. App đang thử lại; lượt của bạn vẫn được giữ."],
  ])("shows the real delivery state %s while waiting", async (delivery, text) => {
    vi.mocked(getHumanTarotRequest).mockResolvedValue({ ...WAITING, delivery });
    renderAt(`/tarot/nguoi-boc/${WAITING.id}`);
    expect(await screen.findByText(text)).toBeInTheDocument();
    expect(screen.getByText("Bài sẽ mở lúc 10:00. Bạn quay lại lúc đó nhé.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Bài người bốc viết cho bạn" })).not.toBeInTheDocument();
  });

  it("checks again on request and shows the reading the server opened, as text", async () => {
    vi.mocked(getHumanTarotRequest)
      .mockResolvedValueOnce({ ...WAITING, status: "late", delivery: "delivered" })
      .mockResolvedValueOnce({
        ...WAITING,
        status: "ready",
        delivery: null,
        result: {
          reader: "human",
          imported_at: "2026-10-30T02:30:00Z",
          reading: "Dòng một.\n<img src=x onerror=alert(1)> vẫn chỉ là chữ.",
          step: "Viết ra ba việc đang ôm.",
          cards: [
            { position_key: "clear", position_label: "Điều đã rõ", card: { ...CARD, id: "major-star", title_vi: "Ngôi Sao", title_en: "The Star" } },
            { position_key: "missed", position_label: "Điều dễ bỏ sót", card: { ...CARD, id: "major-sun", title_vi: "Mặt Trời", title_en: "The Sun" } },
            { position_key: "next", position_label: "Một bước nhỏ có thể thử", card: { ...CARD, id: "major-moon", title_vi: "Mặt Trăng", title_en: "The Moon" } },
          ],
        },
      });
    renderAt(`/tarot/nguoi-boc/${WAITING.id}`);
    expect(await screen.findByRole("heading", { name: "Bài của bạn chưa hoàn tất." })).toBeInTheDocument();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Kiểm tra lại" }));
    expect(await screen.findByRole("heading", { name: "Bài người bốc viết cho bạn" })).toBeInTheDocument();
    expect(screen.getByText("Bài do người bốc viết")).toBeInTheDocument();
    expect(screen.getByText("01 · Điều đã rõ")).toBeInTheDocument();
    expect(screen.getByText(/<img src=x onerror=alert\(1\)> vẫn chỉ là chữ\./)).toBeInTheDocument();
    expect(document.querySelector("img[src='x']")).toBeNull();
    expect(screen.getByText("Viết ra ba việc đang ôm.")).toBeInTheDocument();
  });

  it("cancels after confirmation and follows the Sheet copy until it is cleared", async () => {
    vi.mocked(getHumanTarotRequest)
      .mockResolvedValueOnce(WAITING)
      .mockResolvedValueOnce({ ...WAITING, status: "cancelled", delivery: null, question: null, copy_cleared: false })
      .mockResolvedValueOnce({ ...WAITING, status: "cancelled", delivery: null, question: null, copy_cleared: true });
    vi.mocked(cancelHumanTarotRequest).mockResolvedValue(undefined);
    renderAt(`/tarot/nguoi-boc/${WAITING.id}`);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Huỷ yêu cầu" }));
    expect(screen.getByText("Không có nút hoàn tác. Lượt hôm nay không được trả lại.")).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "Huỷ yêu cầu" })[0]);
    expect(cancelHumanTarotRequest).toHaveBeenCalledWith(WAITING.id);
    expect(await screen.findByText("Bản tạm trên Google Sheet đang được xoá.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Kiểm tra lại" }));
    expect(await screen.findByText("Đã xoá bản tạm trên Google Sheet.")).toBeInTheDocument();
  });

  it("ends a day without a reading honestly", async () => {
    vi.mocked(getHumanTarotRequest).mockResolvedValue({ ...WAITING, status: "unfulfilled", delivery: null, question: null });
    renderAt(`/tarot/nguoi-boc/${WAITING.id}`);
    expect(await screen.findByRole("heading", { name: "Hôm nay người bốc chưa kịp viết bài cho bạn." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Tự bốc ngay/ })).toHaveAttribute("href", "/tarot");
  });

  it("does not reveal anything for an unknown or foreign request", async () => {
    vi.mocked(getHumanTarotRequest).mockRejectedValue(new ApiProblem(404, "HUMAN_TAROT_NOT_FOUND", "x"));
    renderAt(`/tarot/nguoi-boc/${WAITING.id}`);
    expect(await screen.findByRole("heading", { name: "Không mở được yêu cầu này." })).toBeInTheDocument();
  });
});
