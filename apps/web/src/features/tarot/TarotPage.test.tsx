import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  createTarotGuest,
  getSession,
  getTarotSession,
  startTarotSession,
  type TarotSession,
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

const choosing: TarotSession = {
  id: "8e3b79e4-74fc-4cbc-8975-77fa0c77c6a8",
  version: 1,
  state: "choosing",
  context: "relationships",
  spread: "one_card",
  voice: "playful_grounded",
  origin: "direct",
  question: "Giữa tụi mình, điều gì đáng hỏi thẳng thay vì tiếp tục đoán?",
  fan_size: 78,
  required_cards: 1,
  selected_cards: [],
  created_at: "2026-09-27T12:00:00Z",
  updated_at: "2026-09-27T12:00:00Z",
  expires_at: "2026-10-27T06:00:00Z",
};

function renderPage(path = "/tarot") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/tarot" element={<TarotPage />} />
          <Route path="/tarot/:sessionId" element={<TarotPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TarotPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it("starts from a real question and explains the private no-login ritual", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Mang một chuyện thật vào. Tự chọn góc để nhìn lại." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xòe bài cho mình" })).toBeEnabled();
    expect(screen.getByText(/không cần đăng nhập/i)).toBeInTheDocument();
    expect(screen.getByText(/không hỏi lá xem ai đang nghĩ gì/i)).toBeInTheDocument();
  });

  it("creates a Tarot-only guest and opens the committed fan", async () => {
    const user = userEvent.setup();
    vi.mocked(getSession).mockRejectedValue(new ApiProblem(401, "GUEST_SESSION_MISSING", "missing"));
    vi.mocked(createTarotGuest).mockResolvedValue({
      state: "active",
      onboarding_status: "birth_pending",
      expires_at: "2026-10-27T12:00:00Z",
      resumed: false,
      session_epoch: "tarot-epoch",
    });
    vi.mocked(startTarotSession).mockResolvedValue(choosing);
    vi.mocked(getTarotSession).mockResolvedValue(choosing);
    renderPage();

    await user.click(screen.getByRole("button", { name: "Xòe bài cho mình" }));

    expect(createTarotGuest).toHaveBeenCalledTimes(1);
    expect(startTarotSession).toHaveBeenCalledWith(expect.objectContaining({
      context: "general",
      spread: "one_card",
      idempotency_key: expect.any(String),
    }));
    expect(await screen.findByRole("heading", { name: "Chạm lá khiến bạn dừng mắt." })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Lá úp \d+ trên 78/ })).toHaveLength(78);
  });

  it("renders a concrete completed reading instead of a generic card meaning", async () => {
    vi.mocked(getTarotSession).mockResolvedValue({
      ...choosing,
      version: 2,
      state: "complete",
      selected_cards: [{
        fan_index: 17,
        position_key: "focus",
        position_label: "Điều đáng nhìn lúc này",
        card: {
          id: "major-hermit",
          title_vi: "Ẩn Sĩ",
          title_en: "The Hermit",
          arcana: "major",
          core: "lùi khỏi tiếng ồn để nghe câu trả lời của chính mình",
          tension: "cô lập quá lâu",
          resource: "xin một khoảng riêng có thời hạn",
          source_concept_ids: ["archetype-depth"],
        },
      }],
      reading: {
        headline: "Ẩn Sĩ kéo ánh nhìn về kết nối này.",
        summary: "Câu hỏi đang chạm vào phần mình có thể nói rõ thay vì đoán hộ người kia.",
        question: choosing.question,
        question_intent: "communication",
        context: "relationships",
        spread: "one_card",
        voice: "playful_grounded",
        positions: [{
          key: "focus",
          label: "Điều đáng nhìn lúc này",
          card: {
            id: "major-hermit",
            title_vi: "Ẩn Sĩ",
            title_en: "The Hermit",
            arcana: "major",
            core: "lùi khỏi tiếng ồn để nghe câu trả lời của chính mình",
            tension: "cô lập quá lâu",
            resource: "xin một khoảng riêng có thời hạn",
            source_concept_ids: ["archetype-depth"],
          },
          meaning_here: "Điều đang hiện khá rõ là bạn cần một khoảng lùi có thời hạn.",
          everyday_scene: "Một tin nhắn đến chậm và bạn bắt đầu tự viết nốt phần còn thiếu.",
          reflection_question: "Nếu bỏ phần đang đoán, điều gì đáng hỏi thẳng?",
          small_action: "Viết một câu hỏi có thể trả lời thẳng rồi mới nhắn.",
        }],
        closing_prompt: "Giữ câu giúp bạn gọi đúng chuyện đang xảy ra.",
        disclaimer: "Một góc tự soi, không phải dự đoán chắc chắn.",
        provenance: {
          schema_version: "tarot-reading/v1",
          knowledge_version: "tarot-knowledge-v1",
          renderer_version: "tarot-renderer-v1",
          gate_version: "tarot-gates-v1",
          deck_version: "tarot-78-v1",
          spread_version: "tarot-spreads-v1",
          question_rules_version: "tarot-question-rules-v1",
          methodology_version: "tarot-methodology-v1",
          source_ids: ["pollack-78-degrees", "greer-tarot-for-yourself"],
          draw_actor: "self",
          draw_purpose: "first_reading",
        },
      },
    });
    renderPage(`/tarot/${choosing.id}`);

    expect(await screen.findByRole("heading", { name: "Ẩn Sĩ kéo ánh nhìn về kết nối này." })).toBeInTheDocument();
    expect(screen.getByText(/tin nhắn đến chậm/i)).toBeInTheDocument();
    expect(screen.getAllByText(/điều gì đáng hỏi thẳng/i)).toHaveLength(2);
    expect(screen.getByText(/viết một câu hỏi có thể trả lời thẳng/i)).toBeInTheDocument();
  });
});
