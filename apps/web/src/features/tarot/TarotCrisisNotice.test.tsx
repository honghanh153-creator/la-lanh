import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  crisisNoticeFrom,
  createTarotGuest,
  getSession,
  getTarotSession,
  startTarotSession,
} from "../../shared/api/client";
import { TarotPage } from "./TarotPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    createTarotGuest: vi.fn(),
    deleteTarotSession: vi.fn(),
    getSession: vi.fn(),
    getTarotSession: vi.fn(),
    selectTarotCard: vi.fn(),
    startTarotSession: vi.fn(),
  };
});

const NOTICE = "Ứng dụng không hỗ trợ nội dung này.";

function crisisProblem() {
  return new ApiProblem(422, "CRISIS_NOTICE", "Content is not supported", {
    code: "CRISIS_NOTICE",
    notice: { copy_id: "crisis.self_harm.notice", text: NOTICE },
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/tarot"]}>
        <Routes>
          <Route path="/tarot" element={<TarotPage />} />
          <Route path="/tarot/:sessionId" element={<p>Fan opened</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Tarot crisis notice (owner decision 14.11.2026)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    vi.mocked(getSession).mockRejectedValue(new ApiProblem(401, "GUEST_SESSION_MISSING", "missing"));
    vi.mocked(createTarotGuest).mockResolvedValue({
      state: "active",
      onboarding_status: "birth_pending",
      expires_at: "2026-10-27T12:00:00Z",
      resumed: false,
      session_epoch: "tarot-epoch",
    });
  });

  it("shows only the approved notice, no reading, no phone links and no network error", async () => {
    const user = userEvent.setup();
    vi.mocked(startTarotSession).mockRejectedValue(crisisProblem());
    renderPage();

    await user.type(screen.getByPlaceholderText("Ví dụ: Mình nên nói rõ hay chờ thêm?"), "Dạo này mình chỉ muốn chết");
    await user.click(screen.getByRole("button", { name: /^Xòe \d lá/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(NOTICE);
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.queryByText("Fan opened")).not.toBeInTheDocument();
    expect(getTarotSession).not.toHaveBeenCalled();
    expect(screen.queryByText(/kiểm tra mạng/)).not.toBeInTheDocument();
    expect(document.querySelector('a[href^="tel:"]')).toBeNull();
  });

  it("clears the notice when the next question starts a session", async () => {
    const user = userEvent.setup();
    vi.mocked(startTarotSession).mockRejectedValueOnce(crisisProblem());
    renderPage();
    const field = screen.getByPlaceholderText("Ví dụ: Mình nên nói rõ hay chờ thêm?");

    await user.type(field, "minh muon chet");
    await user.click(screen.getByRole("button", { name: /^Xòe \d lá/ }));
    expect(await screen.findByText(NOTICE)).toBeInTheDocument();

    vi.mocked(startTarotSession).mockReturnValueOnce(new Promise(() => {}));
    await user.clear(field);
    await user.type(field, "Mình nên nói rõ hay chờ thêm?");
    await user.click(screen.getByRole("button", { name: /^Xòe \d lá/ }));
    expect(screen.queryByText(NOTICE)).not.toBeInTheDocument();
  });
});

describe("crisisNoticeFrom", () => {
  it("reads only a well-formed crisis problem", () => {
    expect(crisisNoticeFrom(crisisProblem())).toBe(NOTICE);
    expect(crisisNoticeFrom(new ApiProblem(422, "CRISIS_NOTICE", "x", {}))).toBeNull();
    expect(crisisNoticeFrom(new ApiProblem(422, "INPUT_INVALID", "x", { notice: { text: NOTICE } }))).toBeNull();
    expect(crisisNoticeFrom(new Error("network"))).toBeNull();
  });
});
