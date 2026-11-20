import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  askMonth,
  deleteSavedMonthAnswer,
  getMonthOverview,
  getMonthStatus,
  getMonthWindow,
  listSavedMonthAnswers,
  saveMonthAnswer,
  withdrawMonthConsent,
  type MonthAnswer,
  type MonthStatus,
} from "../../shared/api/client";
import { MonthAskPage } from "./MonthAskPage";
import { MonthOverviewCard } from "./MonthOverviewCard";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    askMonth: vi.fn(),
    deleteSavedMonthAnswer: vi.fn(),
    getMonthOverview: vi.fn(),
    getMonthStatus: vi.fn(),
    getMonthWindow: vi.fn(),
    listSavedMonthAnswers: vi.fn(),
    saveMonthAnswer: vi.fn(),
    withdrawMonthConsent: vi.fn(),
  };
});

const CANARY = "zqcanary7month";
const ANSWER: MonthAnswer = {
  month: "2026-11",
  topic: "work",
  topic_label: "Công việc",
  reframe: null,
  theme: "Tháng này công việc cần sắp lại cho gọn.",
  act: "Ghi ra các việc bạn đang ôm.",
  say: "Mình đang có ba việc cùng hạn, bạn muốn mình làm việc nào trước?",
  basis: { line: "Dựa vào: Sao Thổ đi qua nhà công việc của bạn.", detail: "Tháng này Sao Thổ ở cung Bạch Dương." },
  disclaimer: "Đây là một góc nhìn để bạn tự quyết, không phải điều chắc chắn sẽ xảy ra.",
  answer_key: "0123456789abcdef0123456789abcdef",
};

function status(overrides: Partial<MonthStatus> = {}): MonthStatus {
  return { available: true, typed_questions: false, month: "2026-11", consent: null, ...overrides };
}

function renderAt(element: React.ReactElement, path = "/hoi-thang") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/hoi-thang" element={element} />
          <Route path="/insights" element={element} />
          <Route path="/home" element={<p>Trang chủ</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Hỏi về tháng này (US-25)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    vi.mocked(getMonthStatus).mockResolvedValue(status());
    vi.mocked(askMonth).mockResolvedValue({ status: "answered", answer: ANSWER, need_topic: null });
    vi.mocked(listSavedMonthAnswers).mockResolvedValue([]);
  });

  it("goes back to Home while the copy is not approved", async () => {
    vi.mocked(getMonthStatus).mockResolvedValue(status({ available: false }));
    renderAt(<MonthAskPage />);
    expect(await screen.findByText("Trang chủ")).toBeInTheDocument();
  });

  it("answers a topic in three parts with the basis and the disclaimer, and no date", async () => {
    const user = userEvent.setup();
    renderAt(<MonthAskPage />);
    await user.click(await screen.findByRole("button", { name: "Công việc" }));

    expect(askMonth).toHaveBeenCalledWith({ topic: "work" });
    expect(await screen.findByRole("heading", { name: "Tháng này của bạn ở chuyện này" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Có thể làm ngay" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Có thể nói" })).toBeInTheDocument();
    expect(screen.getByText(ANSWER.basis.line)).toBeInTheDocument();
    expect(screen.getByText(ANSWER.disclaimer)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\d{2}\.\d{2}/);
    expect(screen.queryByText(/[Đđ]ếm|còn \d+ câu/)).toBeNull();
  });

  it("shows the easier window only after the tap", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthWindow).mockResolvedValue({
      found: true,
      start: "2026-11-24",
      end: "2026-11-26",
      basis: "Dựa vào: Mặt Trăng đi qua nhà công việc của bạn.",
      line: "Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút.",
    });
    renderAt(<MonthAskPage />);
    await user.click(await screen.findByRole("button", { name: "Công việc" }));
    await screen.findByText(ANSWER.theme);

    expect(getMonthWindow).not.toHaveBeenCalled();
    expect(screen.queryByText(/24\.11/)).toBeNull();
    await user.click(screen.getByRole("button", { name: /Xem lúc nào dễ hơn/ }));
    expect(getMonthWindow).toHaveBeenCalledWith("work");
    expect(await screen.findByText(/24\.11 – 26\.11/)).toBeInTheDocument();
    expect(screen.getByText("Làm lúc nào cũng được; khoảng này chỉ dễ hơn một chút.")).toBeInTheDocument();
  });

  it("never saves on its own; Lưu saves once", async () => {
    const user = userEvent.setup();
    vi.mocked(saveMonthAnswer).mockResolvedValue({
      id: "11111111-1111-1111-1111-111111111111",
      month: "2026-11",
      saved_at: "2026-11-20T05:00:00Z",
      answer: { ...ANSWER, answer_key: "" },
    });
    renderAt(<MonthAskPage />);
    await user.click(await screen.findByRole("button", { name: "Công việc" }));
    await screen.findByText(ANSWER.theme);
    expect(saveMonthAnswer).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Lưu" }));
    expect(saveMonthAnswer).toHaveBeenCalledWith("work", ANSWER.answer_key);
    expect(await screen.findByRole("button", { name: /Đã lưu/ })).toBeDisabled();
  });

  it("lists saved answers only when opened, and deletes one", async () => {
    const user = userEvent.setup();
    vi.mocked(listSavedMonthAnswers).mockResolvedValue([
      { id: "22222222-2222-2222-2222-222222222222", month: "2026-11", saved_at: "2026-11-20T05:00:00Z", answer: { ...ANSWER, answer_key: "" } },
    ]);
    vi.mocked(deleteSavedMonthAnswer).mockResolvedValue();
    renderAt(<MonthAskPage />);
    await screen.findByRole("button", { name: "Công việc" });
    expect(listSavedMonthAnswers).not.toHaveBeenCalled();

    await user.click(screen.getByText("Câu đã lưu"));
    await user.click(await screen.findByRole("button", { name: /Xóa/ }));
    expect(deleteSavedMonthAnswer).toHaveBeenCalledWith("22222222-2222-2222-2222-222222222222");
  });

  it("has no typed box while the switch is off", async () => {
    renderAt(<MonthAskPage />);
    await screen.findByRole("button", { name: "Công việc" });
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("typed questions need the consent box, then are sent once and kept nowhere", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthStatus).mockResolvedValue(status({
      typed_questions: true,
      consent: { version: "month-typed-question-v1", copy_id: "consent.month.typed_question", text: "Câu đồng ý (bản nháp)." },
    }));
    renderAt(<MonthAskPage />);
    const box = await screen.findByRole("textbox");
    await user.type(box, `Làm sao nói với sếp ${CANARY} là mình quá tải?`);
    const submit = screen.getByRole("button", { name: "Hỏi Lá" });
    expect(submit).toBeDisabled();

    await user.click(screen.getByRole("checkbox"));
    await user.click(submit);
    expect(askMonth).toHaveBeenCalledWith({ question: `Làm sao nói với sếp ${CANARY} là mình quá tải?`, consent_version: "month-typed-question-v1" });
    await screen.findByText(ANSWER.theme);
    expect(JSON.stringify({ ...localStorage })).not.toContain(CANARY);
    expect(JSON.stringify({ ...sessionStorage })).not.toContain(CANARY);
    expect(window.location.href).not.toContain(CANARY);
  });

  it("lets the person withdraw consent to typed questions", async () => {
    const user = userEvent.setup();
    vi.mocked(withdrawMonthConsent).mockResolvedValue();
    vi.mocked(getMonthStatus).mockResolvedValue(status({
      typed_questions: true,
      consent: { version: "month-typed-question-v1", copy_id: "consent.month.typed_question", text: "Câu đồng ý (bản nháp)." },
    }));
    renderAt(<MonthAskPage />);
    const box = await screen.findByRole("checkbox");
    await user.click(box);
    expect(box).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Rút lại đồng ý cho câu gõ" }));
    expect(withdrawMonthConsent).toHaveBeenCalled();
    await waitFor(() => expect(box).not.toBeChecked());
  });

  it("shows only the crisis notice for crisis text and clears the box", async () => {
    const user = userEvent.setup();
    const notice = "Câu thông báo an toàn đã duyệt.";
    vi.mocked(getMonthStatus).mockResolvedValue(status({
      typed_questions: true,
      consent: { version: "month-typed-question-v1", copy_id: "consent.month.typed_question", text: "Câu đồng ý (bản nháp)." },
    }));
    vi.mocked(askMonth).mockRejectedValue(new ApiProblem(422, "CRISIS_NOTICE", "Content is not supported", {
      code: "CRISIS_NOTICE",
      notice: { copy_id: "crisis.self_harm.notice.month", text: notice },
    }));
    renderAt(<MonthAskPage />);
    await user.type(await screen.findByRole("textbox"), "Dạo này mình chỉ muốn chết");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Hỏi Lá" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(notice);
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("textbox")).toHaveValue("");
    expect(screen.queryByText("Có thể nói")).toBeNull();
  });
});

describe("Tháng này của bạn in Khám phá", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.mocked(getMonthStatus).mockResolvedValue(status());
    vi.mocked(getMonthOverview).mockResolvedValue({
      month: "2026-11",
      items: [
        { area: "work", label: "Công việc", line: "Dòng công việc.", try_text: "Việc thử 1." },
        { area: "love", label: "Tình cảm", line: "Dòng tình cảm.", try_text: "Việc thử 2." },
        { area: "money", label: "Tiền", line: "Dòng tiền.", try_text: "Việc thử 3." },
        { area: "self", label: "Bản thân", line: "Dòng bản thân.", try_text: "Việc thử 4." },
      ],
    });
  });

  it("shows four areas with one thing to try each, no dates, reminder off by default", async () => {
    const user = userEvent.setup();
    renderAt(<MonthOverviewCard />, "/insights");
    expect(await screen.findByRole("heading", { name: "Tháng 11 của bạn" })).toBeInTheDocument();
    expect(screen.getAllByText(/Việc thử \d/)).toHaveLength(4);
    expect(document.body.textContent).not.toMatch(/\d{2}\.\d{2}/);
    const reminder = screen.getByRole("checkbox", { name: "Nhắc mình đầu tuần trên Trang chủ" });
    expect(reminder).not.toBeChecked();
    await user.click(reminder);
    await waitFor(() => expect(localStorage.getItem("la_lanh_month_weekly_reminder")).toBe("on"));
  });

  it("renders nothing while the feature is not available", async () => {
    vi.mocked(getMonthStatus).mockResolvedValue(status({ available: false }));
    const { container } = renderAt(<MonthOverviewCard />, "/insights");
    await waitFor(() => expect(getMonthStatus).toHaveBeenCalled());
    expect(getMonthOverview).not.toHaveBeenCalled();
    expect(container.querySelector(".month-overview")).toBeNull();
  });
});
