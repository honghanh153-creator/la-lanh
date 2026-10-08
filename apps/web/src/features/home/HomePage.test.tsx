import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  activateReadingProjection,
  ApiProblem,
  checkInMood,
  getBirthSupplement,
  getContextualReading,
  getCurrentMood,
  getDailyNote,
  getResonanceStatus,
  listSavedNotes,
  recordResonance,
  type DailyNote,
  type ReadingProjection,
} from "../../shared/api/client";
import { clearCachedDailyNote, writeCachedDailyNote } from "../../shared/storage/noteCache";
import ultravioletStyles from "../../shared/styles/ultraviolet.css?raw";
import { HomePage } from "./HomePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    activateReadingProjection: vi.fn(),
    checkInMood: vi.fn(),
    getBirthSupplement: vi.fn(),
    getContextualReading: vi.fn(),
    getCurrentMood: vi.fn(),
    getDailyNote: vi.fn(),
    getResonanceStatus: vi.fn(),
    listSavedNotes: vi.fn(),
    recordResonance: vi.fn(),
  };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><HomePage /></MemoryRouter></QueryClientProvider>);
}

const vibe = content("00000000-0000-4000-8000-000000000010", "vibe_fallback", "Chậm lại một nhịp.");
const aura = content("00000000-0000-4000-8000-000000000011", "full_synthesis", "Bạn vừa mềm, vừa rất có biên giới.");

describe("HomePage rich reading", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    clearCachedDailyNote();
    vi.mocked(getCurrentMood).mockResolvedValue(null);
    vi.mocked(listSavedNotes).mockResolvedValue([]);
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not found"));
    vi.mocked(getResonanceStatus).mockResolvedValue({
      consented: false,
      feedback_count: 0,
      last_choice: null,
    });
  });

  it("disables Home motion under reduced-motion and keeps the pause rule scoped to decoration", () => {
    const reducedMotion = ultravioletStyles.slice(ultravioletStyles.lastIndexOf("@media (prefers-reduced-motion: reduce)"));
    expect(reducedMotion).toContain("animation: none !important");
    expect(reducedMotion).toContain(".home-motion-toggle { display: none; }");
    expect(ultravioletStyles).toContain('.home-page[data-home-motion="paused"] :is(.home-note-moon img, .home-advice-star, .home-explore-routes__choices a:first-child img, .home-explore-routes__choices a:last-child img) { animation-play-state: paused; }');
  });

  it("pauses and resumes decorative motion without replacing the note or disabling its actions", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();
    const user = userEvent.setup();
    const headline = await screen.findByRole("heading", { name: vibe.sections.hook });
    const home = screen.getByRole("main");
    expect(home).toHaveAttribute("data-home-motion", "running");

    await user.click(screen.getByRole("button", { name: "Tạm dừng chuyển động" }));
    expect(home).toHaveAttribute("data-home-motion", "paused");
    expect(headline).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Đọc thêm" })).toHaveAttribute("href", "/note/today");
    expect(screen.getByRole("button", { name: "Trúng" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Góc đang đọc Lá chọn" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Bật chuyển động" }));
    expect(home).toHaveAttribute("data-home-motion", "running");
    expect(vi.mocked(getDailyNote)).toHaveBeenCalledTimes(1);
  });

  it("starts with a clear product promise, proves value with today's note, then routes to every live capability", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();

    const valueHeading = await screen.findByRole("heading", { name: "Hôm nay có gì đáng để ý?" });
    const noteRegion = await screen.findByRole("region", { name: "Note hôm nay" });
    const discoveryRegion = screen.getByRole("region", { name: "Khám phá thêm" });

    expect(valueHeading.compareDocumentPosition(noteRegion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(noteRegion.compareDocumentPosition(discoveryRegion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(discoveryRegion).getByRole("link", { name: "Mình & người ấy" })).toHaveAttribute("href", "/radar");
    expect(within(discoveryRegion).getByRole("link", { name: "Rút Tarot" })).toHaveAttribute("href", "/tarot");
    expect(screen.getByRole("link", { name: "Khám phá" })).toHaveAttribute("href", "/insights");
    expect(screen.queryByRole("button", { name: "Giữ việc này để thử" })).not.toBeInTheDocument();
    expect(screen.queryByText("Lá Chứng")).not.toBeInTheDocument();
    expect(within(noteRegion).getByRole("button", { name: "Trúng" })).toBeInTheDocument();
    expect(within(noteRegion).getByRole("button", { name: "Chưa trúng" })).toBeInTheDocument();
    expect(within(noteRegion).getByRole("link", { name: "Chia sẻ note" })).toHaveAttribute("href", "/card");
    expect(screen.queryByRole("button", { name: "Lưu lại" })).not.toBeInTheDocument();
    expect(within(noteRegion).getByText("Hôm nay của bạn")).toBeInTheDocument();
    expect(within(noteRegion).getByRole("complementary", { name: "Việc có thể thử hôm nay" })).toBeInTheDocument();
    expect(within(noteRegion).queryByText("Vì sao dành cho bạn?")).not.toBeInTheDocument();
    expect(within(noteRegion).queryByText(/Đọc từ (dữ liệu ngày sinh|lá số đầy đủ)/)).not.toBeInTheDocument();
  });

  it("keeps the value promise and routes available when the daily note fails", async () => {
    vi.mocked(getDailyNote).mockRejectedValue(new Error("offline"));
    renderPage();

    const valueHeading = await screen.findByRole("heading", { name: "Hôm nay có gì đáng để ý?" });
    const emptyHeading = await screen.findByRole("heading", { name: "Note chưa về kịp." });
    const discoveryRegion = screen.getByRole("region", { name: "Khám phá thêm" });
    expect(valueHeading.compareDocumentPosition(emptyHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(emptyHeading.compareDocumentPosition(discoveryRegion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByRole("link", { name: "Khám phá" })).toHaveAttribute("href", "/insights");
    expect(within(discoveryRegion).getByRole("link", { name: /Rút Tarot/ })).toHaveAttribute("href", "/tarot");
  });

  it("keeps a cached reading visible when its background refresh fails", async () => {
    const cached = noteWith(projection(vibe));
    writeCachedDailyNote(cached);
    vi.mocked(getDailyNote).mockRejectedValue(new Error("offline"));
    renderPage();

    const valueHeading = await screen.findByRole("heading", { name: "Hôm nay có gì đáng để ý?" });
    const noteRegion = await screen.findByRole("region", { name: "Note hôm nay" });
    const discoveryRegion = screen.getByRole("region", { name: "Khám phá thêm" });
    expect(valueHeading.compareDocumentPosition(noteRegion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(noteRegion.compareDocumentPosition(discoveryRegion) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(await screen.findByText("Đang xem đúng bản đã mở gần nhất trên máy")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
  });

  it("keeps a cached note readable but exposes session recovery for live features", async () => {
    writeCachedDailyNote(noteWith(projection(vibe)));
    vi.mocked(getDailyNote).mockRejectedValue(
      new ApiProblem(401, "GUEST_SESSION_MISSING", "Guest session is missing"),
    );
    renderPage();

    expect(await screen.findByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Mở lại Trạm để cập nhật Note và Bản đồ" })).toHaveAttribute("href", "/welcome");
  });

  it("explains how to reopen a missing guest session instead of calling it a network error", async () => {
    vi.mocked(getDailyNote).mockRejectedValue(
      new ApiProblem(401, "GUEST_SESSION_MISSING", "Guest session is missing"),
    );
    renderPage();

    expect(await screen.findByRole("heading", { name: "Phiên riêng đã khép lại." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mở lại Trạm Bắt Sóng" })).toHaveAttribute("href", "/welcome");
    expect(screen.queryByText("Kiểm tra kết nối rồi thử lại.")).not.toBeInTheDocument();
  });

  it("recovers an expired guest session instead of misreporting a network error", async () => {
    vi.mocked(getDailyNote).mockRejectedValue(
      new ApiProblem(401, "GUEST_EXPIRED", "Guest session has expired"),
    );
    renderPage();

    expect(await screen.findByRole("heading", { name: "Phiên riêng đã khép lại." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mở lại Trạm Bắt Sóng" })).toHaveAttribute("href", "/welcome");
    expect(screen.queryByText("Kiểm tra kết nối rồi thử lại.")).not.toBeInTheDocument();
  });

  it("keeps Vibe and Aura copy distinct without exposing chart provenance on Home", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    const first = renderPage();
    expect(screen.queryByText("Đọc từ dữ liệu ngày sinh của bạn")).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
    first.unmount();
    clearCachedDailyNote();

    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(aura)));
    renderPage();
    expect(screen.queryByText("Đọc từ lá số đầy đủ của bạn")).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: aura.sections.hook })).toBeInTheDocument();
  });

  it("keeps a full-chart gift closed until explicit activation", async () => {
    const user = userEvent.setup();
    const withGift = projection(vibe, aura);
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(withGift));
    vi.mocked(activateReadingProjection).mockResolvedValue(projection(aura));
    renderPage();

    expect(await screen.findByRole("heading", { name: "Note này có một bản đủ lớp" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: aura.sections.hook })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Mở bản đủ lớp" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: aura.sections.hook })).toBeInTheDocument());
    expect(screen.queryByRole("heading", { name: "Note này có một bản đủ lớp" })).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Bản đọc mới đã mở");
  });

  it("refetches the daily note after an activation conflict so a stale gift disappears", async () => {
    const user = userEvent.setup();
    const withGift = noteWith(projection(vibe, aura));
    const refreshed = noteWith(projection(aura));
    vi.mocked(getDailyNote)
      .mockResolvedValueOnce(withGift)
      .mockResolvedValueOnce(refreshed);
    vi.mocked(activateReadingProjection).mockRejectedValue(
      new ApiProblem(409, "READING_UPDATE_CONFLICT", "Reading update changed"),
    );
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Mở bản đủ lớp" }));

    await waitFor(() => expect(getDailyNote).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: aura.sections.hook })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Note này có một bản đủ lớp" })).not.toBeInTheDocument();
  });

  it("keeps context in memory and changes framing through a body-only request", async () => {
    const user = userEvent.setup();
    const baseNote = noteWith(projection(vibe));
    const workReading = {
      ...vibe,
      revision_id: "00000000-0000-4000-8000-000000000012",
      sections: {
        ...vibe.sections,
        hook: "Công việc hôm nay cần một câu chốt.",
        manifestation: "Ở công việc, một khoảng dừng giúp bạn nhìn rõ việc cần ưu tiên.",
        micro_action: "Gạch một việc chưa cần làm hôm nay.",
      },
    };
    vi.mocked(getDailyNote).mockResolvedValue(baseNote);
    vi.mocked(getContextualReading).mockResolvedValue(projection(workReading));
    renderPage();

    const noteRegion = await screen.findByRole("region", { name: "Note hôm nay" });
    const contextRegion = screen.getByRole("region", { name: "Góc đang đọc" });
    expect(noteRegion).toContainElement(contextRegion);
    await user.click(screen.getByRole("button", { name: "Góc đang đọc Lá chọn" }));
    await user.click(screen.getByRole("button", { name: "Việc cần chốt" }));

    await waitFor(() => expect(getContextualReading).toHaveBeenCalledWith("work"));
    expect(await screen.findByRole("heading", { name: workReading.sections.hook })).toBeInTheDocument();
    expect(screen.getByText(workReading.sections.manifestation)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Đọc thêm/ })).toHaveAttribute("href", "/note/today?context=work");
    expect(screen.getByRole("link", { name: "Chia sẻ note" })).toHaveAttribute("href", "/card?context=work");
    expect(localStorage.getItem("la-lanh-signal-context-v1")).toBeNull();
    expect(screen.queryByText("Vì sao dành cho bạn?")).not.toBeInTheDocument();
  });

  it("keeps energy and self-care available without crowding the first scan", async () => {
    const user = userEvent.setup();
    const energyReading = {
      ...vibe,
      revision_id: "00000000-0000-4000-8000-000000000014",
      sections: {
        ...vibe.sections,
        hook: "Cơ thể đang xin bạn giảm một nhịp.",
        manifestation: "Cơ thể đang giảm tốc trước khi đầu óc chịu dừng.",
      },
    };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(getContextualReading).mockResolvedValue(projection(energyReading));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Góc đang đọc Lá chọn" }));
    await user.click(screen.getByRole("button", { name: "Nhịp cơ thể" }));

    await waitFor(() => expect(getContextualReading).toHaveBeenCalledWith("energy"));
    expect(await screen.findByRole("heading", { name: energyReading.sections.hook })).toBeInTheDocument();
    expect(screen.getByText(energyReading.sections.manifestation)).toBeInTheDocument();
  });

  it("asks just in time before recording hit or miss and sends only bounded fields", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(recordResonance).mockResolvedValue({
      choice: "hit",
      background_lens: null,
      created_at: "2026-09-14T00:00:00Z",
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Trúng" }));
    expect(recordResonance).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog", { name: "Giữ phản hồi này?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Để sau" }));
    expect(recordResonance).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Trúng" }));
    await user.click(screen.getByRole("button", { name: "Đồng ý và gửi" }));

    await waitFor(() => expect(recordResonance).toHaveBeenCalledWith(baseNoteId, {
      choice: "hit",
      revision_id: vibe.revision_id,
      background_lens: null,
    }));
    expect(await screen.findByRole("status")).toHaveTextContent("Đã ghi nhận: trúng với bạn.");
  });

  it("keeps angle changes in the Context Dial and waits for an explicit different choice", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(getContextualReading).mockResolvedValue(projection({
      ...vibe,
      revision_id: "00000000-0000-4000-8000-000000000013",
      sections: { ...vibe.sections, manifestation: "Trong chuyện tình cảm, hãy để ý khoảng lặng trước câu trả lời." },
    }));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Góc đang đọc Lá chọn" }));
    expect(screen.getByRole("dialog", { name: "Bạn muốn Note giúp nhìn rõ điều gì?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đóng" })).toHaveFocus();
    expect(recordResonance).not.toHaveBeenCalled();
    expect(getContextualReading).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Một mối quan hệ" }));
    await waitFor(() => expect(getContextualReading).toHaveBeenCalledWith("relationships"));
    expect(recordResonance).not.toHaveBeenCalled();
  });

  it("keeps mood check-in behind one playful icon and saves the selected mood", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(checkInMood).mockResolvedValue({
      id: "00000000-0000-4000-8000-000000000099",
      daily_note_id: baseNoteId,
      mood: "Chill",
      checked_in_at: "2026-09-28T00:00:00Z",
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Chọn mood hôm nay" }));
    expect(screen.getByRole("dialog", { name: "Hôm nay bạn đang ở mood nào?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Chill/ }));

    await waitFor(() => expect(checkInMood).toHaveBeenCalledWith(baseNoteId, "Chill"));
    expect(screen.queryByRole("dialog", { name: "Hôm nay bạn đang ở mood nào?" })).not.toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Mood hôm nay: Chill" })).toBeInTheDocument();
  });
});

const baseNoteId = "00000000-0000-4000-8000-000000000001";

function content(revisionId: string, mode: "vibe_fallback" | "full_synthesis", hook: string) {
  return {
    revision_id: revisionId, source: "deterministic" as const, mode,
    purpose: "daily_note" as const, tradition: "western" as const,
    precision: mode === "vibe_fallback" ? "unknown" as const : "exact" as const,
    sections: {
      hook,
      thesis: mode === "vibe_fallback" ? "Đây là một lớp đọc nhẹ từ ngày sinh." : "Nhiều yếu tố trong lá số đang được đọc cùng nhau.",
      manifestation: "Ngoài đời có thể trông như một khoảng dừng trước khi trả lời.",
      transit: null,
      micro_action: "Chọn một câu cần nói rõ hôm nay.",
    },
    evidence: { title: "Căn cứ trong lá số", claims: ["Một dữ kiện đã duyệt"], framework_disclosure: "Chiêm tinh là một khung diễn giải." },
    disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
    created_at: "2026-09-07T00:00:00Z",
  };
}

function projection(active: ReturnType<typeof content>, update?: ReturnType<typeof content>): ReadingProjection {
  return {
    scope_key: "a".repeat(64), active,
    available_update: update ? { revision_id: update.revision_id, message: "Có một bản đọc mới đang chờ bạn", content: update } : null,
    aura_transition: { profile_readiness: "vibe", transition_id: null, acknowledged: false, unlock_layers: [] },
  };
}

function noteWith(readingProjection: ReadingProjection): DailyNote {
  return {
    id: baseNoteId, note_date: "2026-09-07",
    title: "Legacy title", body: "Legacy body", full_body: "Legacy full body",
    context_label: "Legacy context", content_version: "legacy-v1", persona_mode: "vibe",
    persona_label: "Mềm", persona_version: "v1", source_level: "date_only_sun",
    astrology_source_version: "2.10.03", fallback_used: false, fallback_reason: null,
    created_at: "2026-09-07T00:00:00Z", awakening: null, sky_chapter: null,
    reading_projection: readingProjection,
  };
}
