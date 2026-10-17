import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  createTarotGuest,
  getSession,
  getTarotSession,
  selectTarotCard,
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
  spread_map: "one_focus",
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
          <Route path="/welcome" element={<p>Start safely</p>} />
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

  it("keeps locked cards when the local interpretation is unavailable", async () => {
    vi.mocked(getTarotSession).mockResolvedValue({ ...choosing, state: "complete", reading: null });
    renderPage(`/tarot/${choosing.id}`);
    expect(await screen.findByRole("heading", { name: "Chưa mở được phần diễn giải." })).toBeInTheDocument();
    expect(screen.getByText("Bộ lá của bạn không thay đổi.")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "78 lá bài úp" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xóa lần bốc này" })).toBeEnabled();
  });

  it("starts question-first and keeps the draw disabled until the question is useful", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Bạn đang muốn gỡ chuyện gì?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xòe 3 lá" })).toBeDisabled();
    expect(screen.getByText(/không cần đăng nhập/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mình chưa biết hỏi gì" })).toBeEnabled();
  });

  it("describes the selected depth rather than the original recommendation", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "5 lá, đào sâu" }));
    expect(screen.getByRole("heading", { name: "5 lá · Gỡ chuyện nhiều lớp" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "3 lá · Nhìn rõ trước khi hành động" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "1 lá, nhanh" }));
    expect(screen.getByRole("heading", { name: "1 lá · Chạm đúng điểm" })).toBeVisible();
  });

  it("does not submit a question under a different guest that replaced this tab's session", async () => {
    sessionStorage.setItem("la-lanh-session-epoch", "epoch-a");
    vi.mocked(getSession).mockResolvedValue({
      state: "active", session_epoch: "epoch-b", onboarding_status: "completed", resumed: true,
      expires_at: "2026-11-09T00:00:00Z",
    });
    const user = userEvent.setup();
    renderPage();
    await user.type(screen.getByRole("textbox", { name: /Câu hỏi của bạn/ }), "Mình nên nói rõ hay chờ thêm?");
    await user.click(screen.getByRole("button", { name: "Xòe 3 lá" }));
    expect(await screen.findByText("Start safely")).toBeVisible();
    expect(startTarotSession).not.toHaveBeenCalled();
    expect(createTarotGuest).not.toHaveBeenCalled();
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

    await user.type(screen.getByPlaceholderText("Ví dụ: Mình nên nói rõ hay chờ thêm?"), "Mình nên dừng lại?");
    await user.click(screen.getByRole("button", { name: "Xòe 1 lá" }));

    expect(createTarotGuest).toHaveBeenCalledTimes(1);
    expect(startTarotSession).toHaveBeenCalledWith(expect.objectContaining({
      context: "general",
      spread: "one_card",
      idempotency_key: expect.any(String),
    }));
    expect(await screen.findByRole("heading", { name: "Chạm lá khiến bạn dừng mắt." })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Lá úp \d+ trên 78/ })).toHaveLength(78);
  });

  it("recommends a five-card map for a repeating pattern and sends that depth", async () => {
    const user = userEvent.setup();
    const question = "Vì sao mình cứ lặp lại chuyện này?";
    const fiveCard: TarotSession = {
      ...choosing,
      question,
      spread: "five_card",
      spread_map: "five_loop",
      required_cards: 5,
    };
    vi.mocked(getSession).mockResolvedValue({
      state: "active",
      onboarding_status: "completed",
      expires_at: "2026-10-27T12:00:00Z",
      resumed: true,
      session_epoch: "existing-epoch",
    });
    vi.mocked(startTarotSession).mockResolvedValue(fiveCard);
    vi.mocked(getTarotSession).mockResolvedValue(fiveCard);
    renderPage();

    await user.type(screen.getByPlaceholderText("Ví dụ: Mình nên nói rõ hay chờ thêm?"), question);
    expect(screen.getByRole("heading", { name: "5 lá · Gỡ chuyện nhiều lớp" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xòe 5 lá" }));

    expect(startTarotSession).toHaveBeenCalledWith(expect.objectContaining({ spread: "five_card" }));
    expect(await screen.findByText("0/5 lá")).toBeInTheDocument();
  });

  it("renders a concrete completed reading instead of a generic card meaning", async () => {
    const user = userEvent.setup();
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
        headline: "Bạn cần một chút thời gian trước khi nhắn lại.",
        summary: "Ẩn Sĩ nhắc bạn dành một khoảng riêng để nghĩ rõ mình muốn nói gì.",
        question: choosing.question,
        question_intent: "communication",
        context: "relationships",
        spread: "one_card",
        spread_map: "one_focus",
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

    const overview = await screen.findByRole("region", { name: "Tóm tắt bài của bạn" });
    expect(screen.queryByRole("heading", { name: "Bài của bạn đang mở" })).not.toBeInTheDocument();
    expect(within(overview).getByRole("heading", { name: "Bạn cần một chút thời gian trước khi nhắn lại." })).toBeInTheDocument();
    const chapters = screen.getByRole("region", { name: "Mở từng lá để đọc thêm" });
    expect(overview.compareDocumentPosition(chapters) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "lùi khỏi tiếng ồn để nghe câu trả lời của chính mình" })).not.toBeInTheDocument();
    const chapter = chapters.querySelector("details");
    expect(chapter).not.toHaveAttribute("open");
    expect(chapter?.querySelector(".tarot-chapter-thumb svg[data-art='major:hermit']")).toBeInTheDocument();
    expect(within(overview).getByRole("list", { name: "Các lá bạn đã rút" })).toBeInTheDocument();
    await user.click(within(overview).getByRole("button", { name: /^01\. Ẩn Sĩ, Điều đáng nhìn lúc này/ }));
    expect(chapter).toHaveAttribute("open");
    chapter?.removeAttribute("open");
    await user.click(within(chapters).getByText("Ẩn Sĩ"));
    expect(chapter).toHaveAttribute("open");
    expect(screen.getByText(/tin nhắn đến chậm/i)).toBeInTheDocument();
    expect(screen.getAllByText(/điều gì đáng hỏi thẳng/i)).toHaveLength(2);
    expect(screen.getByText(/viết một câu hỏi có thể trả lời thẳng/i)).toBeInTheDocument();
    expect(screen.getByRole("note", { name: "Lưu ý về bản đọc" })).toHaveTextContent(
      "Một góc tự soi, không phải dự đoán chắc chắn.",
    );
  });

  it("keeps English names and engine versions in collapsed technical details (US-20 AC12)", async () => {
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
        headline: "Bạn cần một chút thời gian trước khi nhắn lại.",
        summary: "Ẩn Sĩ nhắc bạn dành một khoảng riêng để nghĩ rõ mình muốn nói gì.",
        question: choosing.question,
        question_intent: "communication",
        context: "relationships",
        spread: "one_card",
        spread_map: "one_focus",
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

    const chapters = await screen.findByRole("region", { name: "Mở từng lá để đọc thêm" });
    expect(within(chapters).queryByText("The Hermit")).not.toBeInTheDocument();
    const tech = screen.getByText("Chi tiết kỹ thuật").closest("details");
    expect(tech).not.toHaveAttribute("open");
    expect(tech).toHaveTextContent("Tên lá gốc: The Hermit");
    expect(tech).toHaveTextContent("Engine tarot-knowledge-v1");
  });

  it("shows no action block for a role without a step (US-20 AC07)", async () => {
    vi.mocked(getTarotSession).mockResolvedValue({
      ...choosing,
      version: 2,
      state: "complete",
      selected_cards: [{
        fan_index: 17,
        position_key: "clear",
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
        headline: "Bạn cần một chút thời gian trước khi nhắn lại.",
        summary: "Ẩn Sĩ nhắc bạn dành một khoảng riêng để nghĩ rõ mình muốn nói gì.",
        question: choosing.question,
        question_intent: "communication",
        context: "relationships",
        spread: "one_card",
        spread_map: "one_focus",
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
          small_action: null,
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

    const chapters = await screen.findByRole("region", { name: "Mở từng lá để đọc thêm" });
    expect(within(chapters).queryByText("Một việc bạn có thể thử")).not.toBeInTheDocument();
    expect(within(chapters).getByText(/khoảng lùi có thời hạn/)).toBeInTheDocument();
  });

  it("shows magic only after the final successful pick; skipping never picks or starts again", async () => {
    const user = userEvent.setup();
    const card: TarotSession["selected_cards"][number]["card"] = {
      id: "major-hermit", title_vi: "Ẩn Sĩ", title_en: "The Hermit", arcana: "major",
      core: "Một khoảng riêng", tension: "Cô lập quá lâu", resource: "Nghỉ có thời hạn", source_concept_ids: [],
    };
    const complete: TarotSession = {
      ...choosing, version: 2, state: "complete",
      selected_cards: [{ fan_index: 0, position_key: "focus", position_label: "Điều đáng nhìn", card }],
      reading: {
        headline: "Bạn cần thời gian trước khi nhắn lại.", summary: "Ẩn Sĩ gợi một khoảng riêng.",
        question: choosing.question, question_intent: "communication", context: "relationships",
        spread: "one_card", spread_map: "one_focus", voice: "playful_grounded",
        positions: [{ key: "focus", label: "Điều đáng nhìn", card, meaning_here: "Nghỉ trước khi trả lời.",
          everyday_scene: "Bạn chưa muốn nhắn lại.", reflection_question: "Bạn muốn nói gì?", small_action: "Viết nháp." }],
        closing_prompt: "Chọn điều đúng với chuyện thật.", disclaimer: "Một góc tự soi.",
        provenance: { schema_version: "tarot-reading/v1", knowledge_version: "fixture", renderer_version: "fixture",
          gate_version: "fixture", deck_version: "fixture", spread_version: "fixture", question_rules_version: "fixture",
          methodology_version: "fixture", source_ids: [], draw_actor: "self", draw_purpose: "first_reading" },
      },
    };
    vi.mocked(getTarotSession).mockResolvedValue(choosing);
    vi.mocked(selectTarotCard).mockResolvedValue(complete);
    renderPage(`/tarot/${choosing.id}`);
    await user.click(await screen.findByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(await screen.findByRole("heading", { name: "Bài của bạn đang mở" })).toHaveFocus();
    expect(screen.queryByRole("region", { name: "Tóm tắt bài của bạn" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xem bài ngay →" }));
    expect(await screen.findByRole("heading", { name: "Tóm tắt bài của bạn" })).toHaveFocus();
    expect(selectTarotCard).toHaveBeenCalledExactlyOnceWith(choosing.id, 0, choosing.version);
    expect(startTarotSession).not.toHaveBeenCalled();
    expect(getTarotSession).toHaveBeenCalledTimes(1);
  });

  it("does not show the reveal scene after an intermediate pick", async () => {
    const user = userEvent.setup();
    const active: TarotSession = { ...choosing, spread: "three_card", required_cards: 3 };
    vi.mocked(getTarotSession).mockResolvedValue(active);
    vi.mocked(selectTarotCard).mockResolvedValue({ ...active, version: 2 });
    renderPage(`/tarot/${active.id}`);
    await user.click(await screen.findByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(screen.queryByRole("heading", { name: "Bài của bạn đang mở" })).not.toBeInTheDocument();
    expect(screen.getByRole("group", { name: "78 lá bài úp" })).toBeInTheDocument();
  });

  it("opens the unavailable state without a ceremony if the last pick has no reading", async () => {
    const user = userEvent.setup();
    vi.mocked(getTarotSession).mockResolvedValue(choosing);
    vi.mocked(selectTarotCard).mockResolvedValue({ ...choosing, state: "complete", reading: null });
    renderPage(`/tarot/${choosing.id}`);
    await user.click(await screen.findByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(await screen.findByRole("heading", { name: "Chưa mở được phần diễn giải." })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Bài của bạn đang mở" })).not.toBeInTheDocument();
    expect(startTarotSession).not.toHaveBeenCalled();
  });

  it("retains the fan and does not fake a reveal after a failed selection", async () => {
    const user = userEvent.setup();
    vi.mocked(getTarotSession).mockResolvedValue(choosing);
    vi.mocked(selectTarotCard).mockRejectedValue(new ApiProblem(503, "UNAVAILABLE", "unavailable"));
    renderPage(`/tarot/${choosing.id}`);
    await user.click(await screen.findByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Lá đã chọn vẫn được giữ");
    expect(screen.getByRole("group", { name: "78 lá bài úp" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Bài của bạn đang mở" })).not.toBeInTheDocument();
  });
});

describe("TarotPage accessibility and card art", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete (HTMLElement.prototype as Partial<HTMLElement>).animate;
  });

  it("names topic and depth buttons and explains why the draw is disabled", async () => {
    const user = userEvent.setup();
    renderPage();
    const topics = screen.getByRole("group", { name: "Chủ đề câu hỏi" });
    const names = within(topics).getAllByRole("button").map((button) => button.getAttribute("aria-label"));
    expect(names).toEqual(["Một chuyện", "Quan hệ", "Công việc", "Giao tiếp", "Năng lượng", "Bản thân"]);
    expect(within(topics).getByRole("button", { name: "Một chuyện" })).toHaveAttribute("aria-pressed", "true");
    await user.click(within(topics).getByRole("button", { name: "Quan hệ" }));
    expect(within(topics).getByRole("button", { name: "Quan hệ" })).toHaveAttribute("aria-pressed", "true");
    const depth = screen.getByRole("group", { name: "Đổi độ sâu" });
    expect(within(depth).getAllByRole("button").map((button) => button.getAttribute("aria-label")))
      .toEqual(["1 lá, nhanh", "3 lá, vừa đủ", "5 lá, đào sâu"]);

    const draw = screen.getByRole("button", { name: "Xòe 3 lá" });
    expect(draw).toBeDisabled();
    expect(draw).toHaveAccessibleDescription(/Nhập câu hỏi từ 8 ký tự/);
    await user.type(screen.getByRole("textbox", { name: /Câu hỏi của bạn/ }), "Mình nên nói rõ hay chờ thêm?");
    expect(screen.getByRole("button", { name: /^Xòe \d lá$/ })).toBeEnabled();
    expect(screen.queryByText(/Nhập câu hỏi từ 8 ký tự/)).not.toBeInTheDocument();
  });

  it("fans card backs without visible numbers while keeping accessible names", async () => {
    vi.mocked(getTarotSession).mockResolvedValue({
      ...choosing,
      required_cards: 3,
      selected_cards: [{ fan_index: 4, position_key: "seen", position_label: "Điều đã rõ", card: {
        id: "cups-7", title_vi: "Bảy Cốc", title_en: "Seven of Cups", arcana: "minor", suit: "cups", rank: "7",
        core: "x", tension: "y", resource: "z", source_concept_ids: [],
      } }],
    });
    renderPage(`/tarot/${choosing.id}`);
    const fan = await screen.findByRole("group", { name: "78 lá bài úp" });
    const cards = within(fan).getAllByRole("button");
    expect(cards).toHaveLength(78);
    expect(fan.textContent).toBe("");
    expect(within(fan).getByRole("button", { name: "Lá úp 3 trên 78" })).toBeEnabled();
    const picked = within(fan).getByRole("button", { name: "Lá úp 5 trên 78" });
    expect(picked).toBeDisabled();
    expect(picked).toHaveAttribute("aria-pressed", "true");
    const slots = screen.getByLabelText("Các vị trí đã chọn");
    expect(slots.querySelector("svg[data-art='minor:cups:7']")).toHaveAttribute("aria-hidden", "true");
    expect(within(slots).getByText("Bảy Cốc")).toBeInTheDocument();
    expect(within(slots).getAllByText("Chưa chọn")).toHaveLength(2);
  });

  function stubLayout() {
    vi.spyOn(HTMLElement.prototype, "offsetWidth", "get").mockReturnValue(58);
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(
      { x: 0, y: 0, left: 10, top: 300, width: 58, height: 96, right: 68, bottom: 396, toJSON: () => ({}) },
    );
    const animate = vi.fn(() => ({ finished: new Promise<never>(() => undefined), cancel: vi.fn() }));
    (HTMLElement.prototype as unknown as { animate: typeof animate }).animate = animate;
    return animate;
  }

  const sevenOfCups: TarotSession["selected_cards"][number] = {
    fan_index: 0, position_key: "seen", position_label: "Điều đã rõ", card: {
      id: "cups-7", title_vi: "Bảy Cốc", title_en: "Seven of Cups", arcana: "minor", suit: "cups", rank: "7",
      core: "x", tension: "y", resource: "z", source_concept_ids: [],
    },
  };

  it("lifts and flips an intermediate pick into its slot when motion is allowed", async () => {
    const animate = stubLayout();
    const user = userEvent.setup();
    const active: TarotSession = { ...choosing, spread: "three_card", required_cards: 3 };
    vi.mocked(getTarotSession).mockResolvedValue(active);
    vi.mocked(selectTarotCard).mockResolvedValue({ ...active, version: 2, selected_cards: [sevenOfCups] });
    renderPage(`/tarot/${active.id}`);
    await user.click(await screen.findByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(await within(screen.getByLabelText("Các vị trí đã chọn")).findByText("Bảy Cốc")).toBeInTheDocument();
    expect(document.querySelector(".tarot-pick-flight svg[data-art='minor:cups:7']")).toBeInTheDocument();
    expect(animate).toHaveBeenCalled();
    expect(document.querySelector("[data-slot-art='0']")).toHaveClass("is-arriving");
    expect(screen.getByText("Đã lật Bảy Cốc cho Điều đã rõ.")).toBeInTheDocument();
  });

  it("skips the pick animation for system reduced motion", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
    const animate = stubLayout();
    const user = userEvent.setup();
    const active: TarotSession = { ...choosing, spread: "three_card", required_cards: 3 };
    vi.mocked(getTarotSession).mockResolvedValue(active);
    vi.mocked(selectTarotCard).mockResolvedValue({ ...active, version: 2, selected_cards: [sevenOfCups] });
    renderPage(`/tarot/${active.id}`);
    expect(await screen.findByLabelText("Bộ bài đang xòe")).toHaveAttribute("data-tarot-motion", "off");
    await user.click(screen.getByRole("button", { name: "Lá úp 1 trên 78" }));
    expect(await within(screen.getByLabelText("Các vị trí đã chọn")).findByText("Bảy Cốc")).toBeInTheDocument();
    expect(document.querySelector(".tarot-pick-flight")).not.toBeInTheDocument();
    expect(animate).not.toHaveBeenCalled();
    expect(document.querySelector("[data-slot-art='0']")).not.toHaveClass("is-arriving");
    expect(selectTarotCard).toHaveBeenCalledExactlyOnceWith(active.id, 0, active.version);
  });
});
