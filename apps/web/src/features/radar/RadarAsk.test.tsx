import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { getRadarAskAnswer, getRadarAskQuestions } from "../../shared/api/client";
import { RadarAsk } from "./RadarAsk";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getRadarAskQuestions: vi.fn(), getRadarAskAnswer: vi.fn() };
});

function renderAsk() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><RadarAsk requestId="r-1" /></QueryClientProvider>);
}

describe("RadarAsk (Hợp gu B)", () => {
  it("shows nothing while the server offers no approved question", async () => {
    vi.mocked(getRadarAskQuestions).mockResolvedValue({ version: "radar-ask-v1", questions: [] });
    const { container } = renderAsk();
    await vi.waitFor(() => expect(getRadarAskQuestions).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("answers a chosen question from the server and offers a sentence to send, no typing", async () => {
    vi.mocked(getRadarAskQuestions).mockResolvedValue({ version: "radar-ask-v1", questions: [
      { id: "message", text: "Nhắn tin cho người ấy kiểu nào thì dễ nghe?" },
      { id: "mind", text: "Người ấy có thích mình không?" },
    ] });
    vi.mocked(getRadarAskAnswer).mockResolvedValue({
      version: "radar-ask-v1", question_id: "mind", question: "Người ấy có thích mình không?",
      say: "Lá không đoán được người ấy nghĩ gì. Bạn có thể hỏi thẳng:", why: "", try_today: null,
      can_send: "Mình thấy vui khi nói chuyện với bạn. Bạn thấy sao?", refusal: true, based_on: null,
    });
    const user = userEvent.setup();
    renderAsk();

    expect(await screen.findByRole("heading", { name: "Bạn muốn hỏi gì về hai bạn?" })).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Người ấy có thích mình không?" }));
    expect(await screen.findByText("Lá không đoán được người ấy nghĩ gì. Bạn có thể hỏi thẳng:")).toBeInTheDocument();
    expect(screen.getByText("“Mình thấy vui khi nói chuyện với bạn. Bạn thấy sao?”")).toBeInTheDocument();
    expect(getRadarAskAnswer).toHaveBeenCalledWith("r-1", "mind", expect.anything());
    await user.click(screen.getByRole("button", { name: "Hỏi câu khác" }));
    expect(screen.getByRole("button", { name: "Nhắn tin cho người ấy kiểu nào thì dễ nghe?" })).toBeInTheDocument();
  });
});
