import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState, type ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, onTestFinished, vi } from "vitest";

import { OnboardingMotionContext } from "../../shared/ui/onboardingMotion";

import {
  activateReadingProjection,
  ApiProblem,
  checkInMood,
  chooseDailyExperiment,
  getBirthSupplement,
  getContextualReading,
  getCurrentDailyExperiment,
  getCurrentMood,
  getDailyNote,
  getResonanceStatus,
  listSavedNotes,
  recordResonance,
  reflectDailyExperiment,
  undoDailyExperiment,
  type DailyExperiment,
  type DailyNote,
  type ReadingProjection,
} from "../../shared/api/client";
import { clearCachedDailyNote, writeCachedDailyNote } from "../../shared/storage/noteCache";
import { clearChartDerivedData } from "../../shared/storage/clearChartDerivedData";
import ultravioletStyles from "../../shared/styles/ultraviolet.css?raw";
import { dailyReadOnlyKey } from "../../shared/hooks/useDailyActionView";
import { FOLDED_ACTION_LABEL, READ_ONLY_TODAY, SHOW_ACTION_AGAIN } from "../../shared/ui/ReadingContent";
import { HomePage } from "./HomePage";
import { LA_MOOD_REACTIONS } from "../../shared/ui/la/laVoice";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    activateReadingProjection: vi.fn(),
    checkInMood: vi.fn(),
    chooseDailyExperiment: vi.fn(),
    getBirthSupplement: vi.fn(),
    getContextualReading: vi.fn(),
    getCurrentDailyExperiment: vi.fn(),
    getCurrentMood: vi.fn(),
    getDailyNote: vi.fn(),
    getResonanceStatus: vi.fn(),
    listSavedNotes: vi.fn(),
    recordResonance: vi.fn(),
    reflectDailyExperiment: vi.fn(),
    undoDailyExperiment: vi.fn(),
  };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return { client, ...render(<QueryClientProvider client={client}><MemoryRouter><HomePage /></MemoryRouter></QueryClientProvider>) };
}

type MoodRow = Awaited<ReturnType<typeof checkInMood>>;

/**
 * A fake mood server: one saved row per note, the last save wins. Every save makes a new row (new
 * id and time), as the real one does. Tests that need an answer to arrive late save here first and
 * hold the answer back themselves.
 */
const moodServer = {
  rows: new Map<string, MoodRow>(),
  saves: 0,
  reset() { this.rows.clear(); this.saves = 0; },
  read(noteId: string): MoodRow | null { return this.rows.get(noteId) ?? null; },
  save(noteId: string, mood: MoodRow["mood"]): MoodRow {
    this.saves += 1;
    const row: MoodRow = {
      id: `00000000-0000-4000-8000-${String(900000 + this.saves).padStart(12, "0")}`,
      daily_note_id: noteId,
      mood,
      checked_in_at: new Date(Date.UTC(2026, 8, 7, 10, 0, this.saves)).toISOString(),
    };
    this.rows.set(noteId, row);
    return row;
  },
};

const vibe = content("00000000-0000-4000-8000-000000000010", "vibe_fallback", "Chậm lại một nhịp.");
const aura = content("00000000-0000-4000-8000-000000000011", "full_synthesis", "Bạn vừa mềm, vừa rất có biên giới.");

describe("HomePage rich reading", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    clearCachedDailyNote();
    // The mood calls talk to one fake server, so a read after a save returns what was saved.
    moodServer.reset();
    vi.mocked(getCurrentMood).mockImplementation((noteId) => Promise.resolve(moodServer.read(noteId)));
    vi.mocked(checkInMood).mockImplementation((noteId, mood) => Promise.resolve(moodServer.save(noteId, mood)));
    vi.mocked(listSavedNotes).mockResolvedValue([]);
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not found"));
    vi.mocked(getResonanceStatus).mockResolvedValue({
      consented: false,
      feedback_count: 0,
      last_choice: null,
    });
  });

  it.each([false, true])("drops a contextual reading after precision withdrawal (pending=%s)", async (pending) => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    let complete!: (value: ReadingProjection) => void;
    const oldWork = { ...aura, sections: { ...aura.sections, hook: "Private old contextual reading" } };
    const delayed = new Promise<ReadingProjection>((resolve) => { complete = resolve; });
    vi.mocked(getContextualReading).mockReturnValue(pending ? delayed : Promise.resolve(projection(oldWork)));
    const { client } = renderPage();
    await user.click(await screen.findByRole("button", { name: "Góc đang đọc Lá chọn" }));
    await user.click(screen.getByRole("button", { name: "Việc cần chốt" }));
    await waitFor(() => expect(getContextualReading).toHaveBeenCalledTimes(1));
    if (!pending) await screen.findByRole("heading", { name: oldWork.sections.hook });
    const dateOnly = { ...vibe, sections: { ...vibe.sections, hook: "Current date-only reading" } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(dateOnly)));
    await act(async () => { await clearChartDerivedData(client); });
    if (pending) await act(async () => { complete(projection(oldWork)); await delayed; });
    expect(await screen.findByRole("heading", { name: dateOnly.sections.hook })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: oldWork.sections.hook })).not.toBeInTheDocument();
    expect(client.getQueryData(["daily-note-context", "work"])).toBeUndefined();
  });

  it("treats a rejected contextual reading as a content error without a retry hint", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(getContextualReading).mockRejectedValue(
      new ApiProblem(422, "READING_CONTENT_REJECTED", "Reading content rejected"),
    );
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Góc đang đọc Lá chọn" }));
    await user.click(screen.getByRole("button", { name: "Việc cần chốt" }));

    const rejected = "Chưa mở được bản đọc. Không cần điền lại khi thông tin đã đủ.";
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(rejected));
    expect(screen.getByRole("status")).toHaveTextContent(rejected);
    expect(screen.queryByText(/thử lại/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Chưa bắt được góc mới/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: vibe.sections.hook })).toBeInTheDocument();
  });

  it("keeps the retry hint when a contextual reading fails on the network", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    vi.mocked(getContextualReading).mockRejectedValue(new ApiProblem(503, "READING_UNAVAILABLE", "Reading unavailable"));
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Góc đang đọc Lá chọn" }));
    await user.click(screen.getByRole("button", { name: "Việc cần chốt" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(
      "Chưa đổi được góc. Note hiện tại vẫn được giữ nguyên; bạn có thể thử lại.",
    ));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Chưa bắt được góc mới. Note đang thấy vẫn được giữ nguyên, không có nội dung mới nào được nhận.",
    );
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
    expect(screen.getByRole("link", { name: "Đọc đầy đủ" })).toHaveAttribute("href", "/note/today");
    expect(screen.getByRole("button", { name: "Trúng" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Góc đang đọc Lá chọn" })).toBeEnabled();

    await user.click(screen.getByRole("button", { name: "Bật chuyển động" }));
    expect(home).toHaveAttribute("data-home-motion", "running");
    expect(vi.mocked(getDailyNote)).toHaveBeenCalledTimes(1);
  });

  it("carries a pause set during onboarding into Home and resumes the whole app from there", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    const user = userEvent.setup();
    function SharedMotion({ children }: { children: ReactNode }) {
      const [paused, setPaused] = useState(true); // paused on Welcome before reaching Home
      return <div data-testid="shell" data-motion={paused ? "paused" : "running"}>
        <OnboardingMotionContext.Provider value={{ paused, toggle: () => setPaused((value) => !value) }}>{children}</OnboardingMotionContext.Provider>
      </div>;
    }
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><SharedMotion><HomePage /></SharedMotion></MemoryRouter></QueryClientProvider>);

    await screen.findByRole("heading", { name: vibe.sections.hook });
    expect(screen.getByRole("main")).toHaveAttribute("data-home-motion", "paused");
    await user.click(screen.getByRole("button", { name: "Bật chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-home-motion", "running");
    expect(screen.getByTestId("shell")).toHaveAttribute("data-motion", "running");
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

  it("lets Lá say the card's own line from the content matrix", async () => {
    const withLine = { ...vibe, sections: { ...vibe.sections, companion: "Hỏi lại một câu thôi, đỡ hơn đoán cả buổi." } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLine)));
    renderPage();

    expect(await screen.findByText("Hỏi lại một câu thôi, đỡ hơn đoán cả buổi.")).toBeInTheDocument();
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

  it("uses Lá's bubble as one notice slot: the gift outranks the birth-time reminder", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe, aura)));
    vi.mocked(getBirthSupplement).mockResolvedValue({ birth_time_mode: "unknown", time_precision: null, place_display_name: null, timezone_id: null } as never);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Note này có một bản đủ lớp" })).toBeInTheDocument();
    expect(screen.queryByText("Còn lá ẩn chờ bạn mở")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Để bản mới lại sau" }));
    expect(screen.queryByRole("heading", { name: "Note này có một bản đủ lớp" })).not.toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /Thêm giờ & nơi sinh/ })).toHaveAttribute("href", "/birth-time");
    await userEvent.click(screen.getByRole("button", { name: "Để 3 ngày sau" }));
    expect(screen.queryByRole("link", { name: /Thêm giờ & nơi sinh/ })).not.toBeInTheDocument();
    expect(Number(localStorage.getItem("la-lanh-birth-supplement-snooze-until"))).toBeGreaterThan(Date.now());
  });

  it("shows Lá's own line when no notice needs the bubble, and lets the user hide it", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();
    await screen.findByRole("heading", { name: vibe.sections.hook });
    const hide = screen.getByRole("button", { name: "Ẩn câu của Lá" });
    await userEvent.click(hide);
    expect(screen.queryByRole("button", { name: "Ẩn câu của Lá" })).not.toBeInTheDocument();
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
    expect(screen.getByRole("link", { name: /Đọc đầy đủ/ })).toHaveAttribute("href", "/note/today?context=work");
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

  it("asks the US-04 mood question below the Note, never in the hero (AC-GWT-01, US-03 AC21)", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    const { container } = renderPage();

    const moodHeading = await screen.findByRole("heading", { name: "Hôm nay bạn thấy sao?" });
    const note = screen.getByRole("region", { name: "Note hôm nay" });
    expect(note.compareDocumentPosition(moodHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(note).not.toContainElement(moodHeading);
    expect(container.querySelector(".home-value-hero")).not.toContainElement(
      screen.getByRole("button", { name: "Chọn cảm giác hôm nay" }),
    );
    expect(screen.queryByText("Chọn mood")).not.toBeInTheDocument();
  });

  it("saves the selected mood from the check-in below the Note", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" }));
    expect(screen.getByRole("dialog", { name: "Hôm nay bạn thấy sao?" })).toBeInTheDocument();
    expect(screen.queryByText("Hôm nay bạn đang ở mood nào?")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Chill/ }));

    await waitFor(() => expect(checkInMood).toHaveBeenCalledWith(baseNoteId, "Chill"));
    expect(screen.queryByRole("dialog", { name: "Hôm nay bạn thấy sao?" })).not.toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Cảm giác hôm nay: Chill" })).toBeInTheDocument();
  });

  it("lets Lá answer the chosen mood instead of a card line that assumes another mood (Wave 1)", async () => {
    const user = userEvent.setup();
    const tired = { ...vibe, sections: { ...vibe.sections, companion: "Thu hẹp lựa chọn khi đang mệt." } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(tired)));
    renderPage();

    expect(await screen.findByText("Thu hẹp lựa chọn khi đang mệt.")).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" }));
    await user.click(screen.getByRole("button", { name: /Chill/ }));
    await waitFor(() => expect(screen.queryByText("Thu hẹp lựa chọn khi đang mệt.")).not.toBeInTheDocument());
    expect(screen.getAllByText(LA_MOOD_REACTIONS.Chill).length).toBeGreaterThan(0);
  });

  it("shows the lighter action after a Đuối check-in and lets the reader switch back (#627)", async () => {
    const user = userEvent.setup();
    const original = vibe.sections.micro_action;
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
    renderPage();

    // Before any check-in the card's own action shows and nothing offers a switch.
    expect(await screen.findByText(original)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Xem việc ban đầu" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Xem việc nhẹ hơn" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Chọn cảm giác hôm nay" }));
    await user.click(screen.getByRole("button", { name: /Đuối/ }));
    expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
    expect(screen.queryByText(original)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Xem việc ban đầu" }));
    expect(screen.getByText(original)).toBeInTheDocument();
    expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xem việc nhẹ hơn" }));
    expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();

    // Another mood brings the card's own action back and removes the switch.
    await user.click(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" }));
    await user.click(screen.getByRole("button", { name: /Chill/ }));
    expect(await screen.findByText(original)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Xem việc nhẹ hơn" })).not.toBeInTheDocument();
    // The choice never reaches device storage.
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("lighter");
  });

  it("does not carry yesterday's Đuối into the next day's note when Home stays open (US-04 AC12, #627)", async () => {
    const user = userEvent.setup();
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
    const { client } = renderPage();
    await user.click(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" }));
    await user.click(screen.getByRole("button", { name: /Đuối/ }));
    expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
    await screen.findByRole("button", { name: "Cảm giác hôm nay: Đuối" });

    // Past midnight the refetch returns the next day's note; no mood has been picked for it.
    const nextDay = { ...noteWith(projection(withLighter)), id: "00000000-0000-4000-8000-000000000002", note_date: "2026-09-08" };
    vi.mocked(getDailyNote).mockResolvedValue(nextDay);
    await act(async () => { await client.invalidateQueries(); });

    await waitFor(() => expect(getCurrentMood).toHaveBeenCalledWith(nextDay.id, expect.anything()));
    expect(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" })).toBeInTheDocument();
    expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Xem việc ban đầu" })).not.toBeInTheDocument();
  });

  // `start` is the mood already saved when Home opens. The rows that start from the mood the
  // other tab returns to are the ones where a confirmed pick used to come back (review auto-3).
  it.each([
    { start: null, here: "Đuối", elsewhere: "Chill", lighterAfter: false },
    { start: null, here: "Chill", elsewhere: "Đuối", lighterAfter: true },
    { start: "Chill", here: "Đuối", elsewhere: "Chill", lighterAfter: false },
    { start: "Đuối", here: "Chill", elsewhere: "Đuối", lighterAfter: true },
  ] as const)("follows a mood changed in another tab: saved $start, picked $here here, $elsewhere elsewhere (#627)", async ({ start, here, elsewhere, lighterAfter }) => {
    const user = userEvent.setup();
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
    if (start) moodServer.save(baseNoteId, start);
    const { client } = renderPage();
    await user.click(await screen.findByRole("button", { name: start ? `Cảm giác hôm nay: ${start}` : "Chọn cảm giác hôm nay" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: new RegExp(here) }));
    await screen.findByRole("button", { name: `Cảm giác hôm nay: ${here}` });
    // After the save Home reads the mood again; that read is the saved mood, also for the note page.
    await waitFor(() => expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(here));

    // The mood is changed in another tab; this tab fetches it again.
    moodServer.save(baseNoteId, elsewhere);
    await act(async () => { await client.invalidateQueries({ queryKey: ["daily-note-mood"] }); });

    expect(await screen.findByRole("button", { name: `Cảm giác hôm nay: ${elsewhere}` })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(withLighter.lighter_action.action) !== null).toBe(lighterAfter);
      expect(screen.queryByRole("button", { name: "Xem việc ban đầu" }) !== null).toBe(lighterAfter);
    });
    expect(screen.queryByText(vibe.sections.micro_action) !== null).toBe(!lighterAfter);
  });

  it("keeps the card's own action while a Đuối pick is unsaved, even when a slow mood read lands meanwhile (review auto-4)", async () => {
    const user = userEvent.setup();
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    let landRead!: (value: MoodRow) => void;
    let landSave!: () => void;
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
    // The first read is slow and carries the mood saved before it started (Chill).
    const before = moodServer.save(baseNoteId, "Chill");
    vi.mocked(getCurrentMood).mockImplementationOnce(() => new Promise((resolve) => { landRead = resolve; }));
    vi.mocked(checkInMood).mockImplementationOnce((noteId, mood) => {
      const saved = moodServer.save(noteId, mood);
      return new Promise((resolve) => { landSave = () => resolve(saved); });
    });
    renderPage();

    // The first mood read is still on its way when the reader picks Đuối.
    await user.click(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" }));
    await user.click(screen.getByRole("button", { name: /Đuối/ }));
    await screen.findByRole("button", { name: "Cảm giác hôm nay: Đuối" });
    const ordinary = () => {
      expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
      expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /Xem việc/ })).not.toBeInTheDocument();
    };
    ordinary();

    // The slow read lands with the older saved mood while the save is still pending.
    await act(async () => { landRead(before); await new Promise((resolve) => setTimeout(resolve, 30)); });
    ordinary();
    expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();

    // Only the confirmed save, read back from the server, brings the lighter action.
    await act(async () => { landSave(); await Promise.resolve(); });
    expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xem việc ban đầu" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
  });

  it.each([
    { saved: "Chill", pick: "Đuối" },
    { saved: null, pick: "Đuối" },
    { saved: "Đuối", pick: "Chill" },
  ] as const)("never shows the lighter action for a pick that failed to save: saved $saved, picked $pick (review auto-4)", async ({ saved, pick }) => {
    const user = userEvent.setup();
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
    if (saved) moodServer.save(baseNoteId, saved);
    vi.mocked(checkInMood).mockImplementation(() => Promise.reject(new Error("offline")));
    renderPage();

    await user.click(await screen.findByRole("button", { name: saved ? `Cảm giác hôm nay: ${saved}` : "Chọn cảm giác hôm nay" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: new RegExp(pick) }));
    expect((await screen.findAllByText("Đã giữ cảm xúc trên máy. Lá Lành sẽ đồng bộ khi có mạng.")).length).toBeGreaterThan(0);

    // The control keeps the pick (it will be sent again); the action waits for a saved mood.
    expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${pick}` })).toBeInTheDocument();
    expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Xem việc/ })).not.toBeInTheDocument();
  });

  describe("async paths of the lighter action (#627 audit)", () => {
    const withLighter = { ...vibe, lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light" as const, experiment: null } };
    const nextDay = { ...noteWith(projection(withLighter)), id: "00000000-0000-4000-8000-000000000002", note_date: "2026-09-08" };
    const expectOrdinary = () => {
      expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
      expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /Xem việc/ })).not.toBeInTheDocument();
    };
    /** The next save is held: `succeed` commits it on the server and answers, `fail` rejects it. */
    function holdNextSave() {
      const held: { succeed: () => void; fail: () => void; commit: () => MoodRow } = { succeed: () => {}, fail: () => {}, commit: () => { throw new Error("no save yet"); } };
      vi.mocked(checkInMood).mockImplementationOnce((noteId, mood) => new Promise((resolve, reject) => {
        let row: MoodRow | undefined;
        // `commit` alone is a save the server has stored whose answer has not arrived yet.
        held.commit = () => (row ??= moodServer.save(noteId, mood));
        held.succeed = () => resolve(held.commit());
        held.fail = () => reject(new Error("offline"));
      }));
      return held;
    }
    /** Picks `pick` on the Home that is on screen; resolves once the control shows it. */
    async function pickMood(current: "Đuối" | "Chill" | null, pick: "Đuối" | "Chill") {
      const user = userEvent.setup();
      await user.click(await screen.findByRole("button", { name: current ? `Cảm giác hôm nay: ${current}` : "Chọn cảm giác hôm nay" }));
      await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: new RegExp(pick) }));
      await screen.findByRole("button", { name: `Cảm giác hôm nay: ${pick}` });
    }
    /** Opens Home with `saved` as the saved mood and picks `pick`; the save stays pending. */
    async function pickWithPendingSave(saved: "Đuối" | "Chill" | null, pick: "Đuối" | "Chill") {
      vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
      if (saved) moodServer.save(baseNoteId, saved);
      const settle = holdNextSave();
      const page = renderPage();
      await pickMood(saved, pick);
      return { ...page, settle };
    }
    /** Lets the page finish reacting: the cache changes a tick before the page re-renders. */
    const settled = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 30)); });

    it("refetch while a save is pending: the saved mood read again does not bring the lighter action for the unsaved pick", async () => {
      const { client, settle } = await pickWithPendingSave("Chill", "Đuối");
      expectOrdinary();
      await act(async () => { await client.invalidateQueries({ queryKey: ["daily-note-mood"] }); });
      await settled();
      expectOrdinary();
      await act(async () => { settle.succeed(); await Promise.resolve(); });
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
    });

    it("refetch while a save away from Đuối is pending: the card's own action stays until the save settles", async () => {
      const { client, settle } = await pickWithPendingSave("Đuối", "Chill");
      // Saved is still Đuối, but the reader has just picked Chill: no lighter action meanwhile.
      expectOrdinary();
      await act(async () => { await client.invalidateQueries({ queryKey: ["daily-note-mood"] }); });
      await settled();
      expectOrdinary();
      await act(async () => { settle.succeed(); await Promise.resolve(); });
      await waitFor(() => expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Chill"));
      await settled();
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Chill" })).toBeInTheDocument();
      expectOrdinary();
    });

    // Review auto-5: another tab saves again while this tab's save is pending, so the refetch
    // returns a different row (new id and time), not the identical one the tests above return.

    it.each([
      { saved: "Đuối", pick: "Chill", elsewhere: "Đuối", outcome: "fails" },
      { saved: "Đuối", pick: "Chill", elsewhere: "Đuối", outcome: "succeeds" },
      { saved: "Chill", pick: "Đuối", elsewhere: "Chill", outcome: "fails" },
      { saved: "Chill", pick: "Đuối", elsewhere: "Chill", outcome: "succeeds" },
      { saved: null, pick: "Chill", elsewhere: "Đuối", outcome: "fails" },
    ] as const)("a newer saved row fetched while a save is pending never replaces the unsaved pick: saved $saved, picked $pick, $elsewhere saved elsewhere, save $outcome", async ({ saved, pick, elsewhere, outcome }) => {
      const { client, settle } = await pickWithPendingSave(saved, pick);
      const savedElsewhere = moodServer.save(baseNoteId, elsewhere);
      await act(async () => { await client.invalidateQueries({ queryKey: ["daily-note-mood"] }); });
      await waitFor(() => expect(client.getQueryData<{ id: string }>(["daily-note-mood", baseNoteId])?.id).toBe(savedElsewhere.id));
      await settled();

      // The new row is the saved mood now, but the pick here is still unsaved: the control keeps
      // the pick and the card keeps its own action, even though the saved mood may be Đuối.
      expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${pick}` })).toBeInTheDocument();
      expectOrdinary();

      if (outcome === "fails") {
        await act(async () => { settle.fail(); await Promise.resolve(); });
        expect((await screen.findAllByText("Đã giữ cảm xúc trên máy. Lá Lành sẽ đồng bộ khi có mạng.")).length).toBeGreaterThan(0);
        await settled();
        expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${pick}` })).toBeInTheDocument();
        expectOrdinary();
        return;
      }
      await act(async () => { settle.succeed(); await Promise.resolve(); });
      await waitFor(() => expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(pick));
      await settled();
      expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${pick}` })).toBeInTheDocument();
      if (pick === "Đuối") expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
      else expectOrdinary();
    });

    it("day change while a save is pending, then it succeeds: yesterday's Đuối stays with yesterday's note", async () => {
      const { client, settle } = await pickWithPendingSave(null, "Đuối");
      vi.mocked(getDailyNote).mockResolvedValue(nextDay);
      await act(async () => { await client.invalidateQueries(); });
      expect(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" })).toBeInTheDocument();

      await act(async () => { settle.succeed(); await Promise.resolve(); });
      await settled();
      // The save belongs to yesterday's note: stored there and applied to that note's mood only.
      // The new day has no mood and keeps its own action.
      expect(moodServer.read(baseNoteId)?.mood).toBe("Đuối");
      expect(moodServer.read(nextDay.id)).toBeNull();
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");
      expect(client.getQueryData(["daily-note-mood", nextDay.id])).toBeNull();
      expect(screen.getByRole("button", { name: "Chọn cảm giác hôm nay" })).toBeInTheDocument();
      expectOrdinary();
    });

    it("day change while a save is pending, then it fails: the pick waiting to sync is filed under yesterday's note", async () => {
      // A failed check-in is only kept for a known session.
      sessionStorage.setItem("la-lanh-session-epoch", "epoch-a");
      onTestFinished(() => sessionStorage.removeItem("la-lanh-session-epoch"));
      const { client, settle } = await pickWithPendingSave(null, "Đuối");
      vi.mocked(getDailyNote).mockResolvedValue(nextDay);
      await act(async () => { await client.invalidateQueries(); });
      expect(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" })).toBeInTheDocument();

      await act(async () => { settle.fail(); await Promise.resolve(); });
      expect((await screen.findAllByText("Đã giữ cảm xúc trên máy. Lá Lành sẽ đồng bộ khi có mạng.")).length).toBeGreaterThan(0);
      const waiting = JSON.parse(localStorage.getItem("la-lanh-pending-mood-v1") ?? "null") as { note_id?: string; mood?: string } | null;
      expect(waiting).toMatchObject({ note_id: baseNoteId, mood: "Đuối" });
      // Nothing is sent for the new day, and it keeps its own action.
      expect(vi.mocked(checkInMood).mock.calls.every(([noteId]) => noteId === baseNoteId)).toBe(true);
      expect(screen.getByRole("button", { name: "Chọn cảm giác hôm nay" })).toBeInTheDocument();
      expectOrdinary();
    });

    it("two picks in quick succession: a second pick cannot start while a save is pending, so two saves never race", async () => {
      const user = userEvent.setup();
      await pickWithPendingSave(null, "Đuối");
      await user.click(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" }));
      const options = within(screen.getByRole("dialog")).getAllByRole("button").filter((button) => button.hasAttribute("aria-pressed"));
      expect(options).toHaveLength(5);
      for (const option of options) expect(option).toBeDisabled();
      await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: /Chill/ }));
      expect(checkInMood).toHaveBeenCalledTimes(1);
    });

    const reopenHome = (client: QueryClient) => render(<QueryClientProvider client={client}><MemoryRouter><HomePage /></MemoryRouter></QueryClientProvider>);

    it("unmount while a save is pending: the answer still becomes the saved mood and shows on return", async () => {
      const { client, settle, unmount } = await pickWithPendingSave(null, "Đuối");
      unmount();
      await act(async () => { settle.succeed(); await Promise.resolve(); });
      // The answer is applied to the shared saved mood although its screen is gone.
      expect(client.getQueryData<{ mood: string } | null>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");

      // Coming back to Home (same cache): the saved mood is Đuối, so the lighter action shows.
      reopenHome(client);
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
    });

    it("unmount while a save is pending, then it fails: nothing shows the lighter action on return until a save succeeds", async () => {
      const { client, settle, unmount } = await pickWithPendingSave(null, "Đuối");
      unmount();
      await act(async () => { settle.fail(); await Promise.resolve(); });
      expect(moodServer.read(baseNoteId)).toBeNull();

      // On return the pick may be sent again; while that is unsaved the card keeps its own action.
      vi.mocked(checkInMood).mockImplementation(() => new Promise(() => {}));
      reopenHome(client);
      expect(await screen.findByText(vibe.sections.micro_action)).toBeInTheDocument();
      await settled();
      expectOrdinary();
    });

    it("save succeeds but the read after it fails: the save's own answer is the saved mood", async () => {
      const { client, settle } = await pickWithPendingSave("Chill", "Đuối");
      vi.mocked(getCurrentMood).mockImplementationOnce(() => Promise.reject(new Error("offline")));
      await act(async () => { settle.succeed(); await Promise.resolve(); });
      await settled();
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
      expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
    });

    // One test per reordering of answers (coordinator, 17.11). All of them go through
    // `newerMoodRow`: an answer is applied only if it is not older than the row already applied.
    it.each([
      { saved: "Chill" },
      // "No mood" has no time to compare, so here only replacing the slow read protects the save.
      { saved: null },
    ] as const)("read vs save: a read started before the save's answer and landing after it does not put the older state back (saved before: $saved)", async ({ saved }) => {
      const { client, settle } = await pickWithPendingSave(saved, "Đuối");
      // A refetch starts while the save is pending; the server answers it with what it had
      // before the save, and that answer is slow.
      const before = moodServer.read(baseNoteId);
      let landRead: (() => void) | undefined;
      vi.mocked(getCurrentMood).mockImplementationOnce(() => new Promise((resolve) => { landRead = () => resolve(before); }));
      void client.invalidateQueries({ queryKey: ["daily-note-mood"] });
      await waitFor(() => expect(landRead).toBeDefined());

      await act(async () => { settle.succeed(); await Promise.resolve(); });
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
      await act(async () => { landRead!(); await Promise.resolve(); });
      await settled();

      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
      expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
    });

    it("failure then success: a failed pick leaves nothing behind, and the next saved pick is the saved mood", async () => {
      vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(withLighter)));
      vi.mocked(checkInMood).mockImplementationOnce(() => Promise.reject(new Error("offline")));
      const { client } = renderPage();
      await pickMood(null, "Chill");
      expect((await screen.findAllByText("Đã giữ cảm xúc trên máy. Lá Lành sẽ đồng bộ khi có mạng.")).length).toBeGreaterThan(0);
      expect(client.getQueryData(["daily-note-mood", baseNoteId])).toBeFalsy();
      expectOrdinary();

      // The next pick is saved (the default fake server stores and answers at once).
      await pickMood("Chill", "Đuối");
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
      await settled();
      expect(moodServer.read(baseNoteId)?.mood).toBe("Đuối");
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
    });

    it("failure then success in the other order of answers: an older save failing late does not undo the newer saved mood", async () => {
      // Save A (Chill) is held. Home is closed and reopened; save B (Đuối) is stored and answered.
      const { client, settle: saveA, unmount } = await pickWithPendingSave(null, "Chill");
      unmount();
      reopenHome(client);
      await pickMood(null, "Đuối");
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();

      // Now A fails, in the callback of the Home that is no longer on screen.
      await act(async () => { saveA.fail(); await Promise.resolve(); });
      await settled();
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe("Đuối");
      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
      expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
      expect(checkInMood).toHaveBeenCalledTimes(2);
    });

    // Review auto-6: the answer to an older save arrives after a newer save, across a remount.
    it.each([
      { first: "Đuối", second: "Chill" },
      { first: "Chill", second: "Đuối" },
    ] as const)("answers out of order across a remount: $first saved first and answered last, $second saved second: the server's last row wins", async ({ first, second }) => {
      // Save A: the server stores it at once, but its answer is delayed.
      const { client, settle: saveA, unmount } = await pickWithPendingSave(null, first);
      saveA.commit();
      unmount();

      // Back on Home: the server already has A. Save B is stored and answered straight away.
      reopenHome(client);
      await pickMood(first, second);
      await waitFor(() => expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(second));
      await settled();

      // Now A's answer arrives, in the callback of the Home that is no longer on screen. The read
      // that follows an answer is held back here, so only the ordering rule stands between A's
      // older row and the saved mood.
      vi.mocked(getCurrentMood).mockImplementationOnce(() => new Promise(() => {}));
      await act(async () => { saveA.succeed(); await Promise.resolve(); });
      await settled();

      expect(moodServer.read(baseNoteId)?.mood).toBe(second);
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(second);
      expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${second}` })).toBeInTheDocument();
      if (second === "Đuối") {
        expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Xem việc ban đầu" })).toBeInTheDocument();
      } else {
        expectOrdinary();
      }
    });

    // Review auto-7 (P2): a rejected older answer must not undo the reader's own choice of action.
    it("a rejected older answer keeps the reader's choice of action", async () => {
      const user = userEvent.setup();
      const { client, settle: saveA, unmount } = await pickWithPendingSave(null, "Chill");
      saveA.commit();
      unmount();
      reopenHome(client);
      await pickMood("Chill", "Đuối");
      expect(await screen.findByText(withLighter.lighter_action.action)).toBeInTheDocument();
      await settled();
      // The reader switches to the card's own action before A's answer arrives.
      await user.click(screen.getByRole("button", { name: "Xem việc ban đầu" }));
      expect(await screen.findByRole("button", { name: "Xem việc nhẹ hơn" })).toBeInTheDocument();

      vi.mocked(getCurrentMood).mockImplementationOnce(() => new Promise(() => {}));
      await act(async () => { saveA.succeed(); await Promise.resolve(); });
      await settled();

      expect(screen.getByRole("button", { name: "Cảm giác hôm nay: Đuối" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Xem việc nhẹ hơn" })).toBeInTheDocument();
      expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
      expect(screen.queryByText(withLighter.lighter_action.action)).not.toBeInTheDocument();
    });

    // Review auto-7 (P1): request order and write order can differ. The server stamps a save when
    // it writes it (the fake does the same), so the save written last is the newest, even though
    // it was requested first and is answered last.
    it.each([
      { first: "Đuối", second: "Chill" },
      { first: "Chill", second: "Đuối" },
    ] as const)("request order reversed: $first requested first but written last, $second requested second and written first: the last written wins", async ({ first, second }) => {
      // Save A is requested; the server has not written it yet (it waits for its turn).
      const { client, settle: saveA, unmount } = await pickWithPendingSave(null, first);
      unmount();

      // Back on Home: the server has nothing yet. Save B is written and answered straight away.
      reopenHome(client);
      await pickMood(null, second);
      await waitFor(() => expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(second));
      await settled();
      const writtenB = moodServer.read(baseNoteId)!;

      // Now the server writes A, after B, and answers. The follow-up read is held back, so the
      // answer itself must be accepted as the newest row.
      vi.mocked(getCurrentMood).mockImplementationOnce(() => new Promise(() => {}));
      await act(async () => { saveA.succeed(); await Promise.resolve(); });
      await settled();

      const writtenA = moodServer.read(baseNoteId)!;
      expect(writtenA.mood).toBe(first);
      expect(Date.parse(writtenA.checked_in_at)).toBeGreaterThan(Date.parse(writtenB.checked_in_at));
      expect(client.getQueryData<{ mood: string }>(["daily-note-mood", baseNoteId])?.mood).toBe(first);
      expect(screen.getByRole("button", { name: `Cảm giác hôm nay: ${first}` })).toBeInTheDocument();
      if (first === "Đuối") {
        expect(screen.getByText(withLighter.lighter_action.action)).toBeInTheDocument();
      } else {
        expectOrdinary();
      }
    });
  });

  it("keeps the card's own action on a Đuối day when no lighter action is approved (#627)", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Chọn cảm giác hôm nay" }));
    await user.click(screen.getByRole("button", { name: /Đuối/ }));
    await waitFor(() => expect(checkInMood).toHaveBeenCalledWith(baseNoteId, "Đuối"));
    expect(screen.getByText(vibe.sections.micro_action)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Xem việc ban đầu" })).not.toBeInTheDocument();
  });

  it("dates the loading hero by the Vietnam day, not the UTC day (PL-12)", () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    try {
      // 18:30 UTC on 10.03 is 01:30 on 11.03 in Vietnam.
      vi.setSystemTime(new Date("2026-03-10T18:30:00Z"));
      vi.mocked(getDailyNote).mockReturnValue(new Promise<DailyNote>(() => {}));
      const { container } = renderPage();
      const hero = container.querySelector(".home-value-hero time");
      expect(hero).toHaveTextContent("Hôm nay");
      expect(hero).toHaveAttribute("datetime", "2026-03-11");
    } finally {
      vi.useRealTimers();
    }
  });
});

// #741: Home shows and changes the kept action through the same controls as the note page
// (US-03 §22, AC33). Synthetic data only.
describe("HomePage kept action (#741)", () => {
  const cues = { observation: "Bạn thấy nhẹ hơn chưa?", permission: "Không hợp thì bỏ qua." };
  const own = { action_key: "d".repeat(64), action: "Chọn một câu cần nói rõ hôm nay.", ...cues };
  const light = { action_key: "e".repeat(64), action: "Uống một ly nước rồi ngồi yên hai phút.", ...cues };
  const keepable = { ...aura, experiment: own, lighter_action: { action: light.action, weight: "light" as const, experiment: light } };
  const held = (offer: typeof own, over: Partial<DailyExperiment> = {}): DailyExperiment => ({
    id: "10000000-0000-4000-8000-000000000001", version: 1, daily_note_id: baseNoteId,
    revision_id: keepable.revision_id, state: "chosen", background_lens: "auto", ...offer, outcome: null,
    created_at: "2026-09-07T12:00:00Z", updated_at: "2026-09-07T12:00:00Z",
    expires_at: "2026-10-07T12:00:00Z", reflected_at: null, ...over,
  });
  const advice = () => screen.findByRole("complementary", { name: "Việc có thể thử hôm nay" });

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    clearCachedDailyNote();
    moodServer.reset();
    vi.mocked(getCurrentMood).mockImplementation((noteId) => Promise.resolve(moodServer.read(noteId)));
    vi.mocked(listSavedNotes).mockResolvedValue([]);
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not found"));
    vi.mocked(getResonanceStatus).mockResolvedValue({ consented: false, feedback_count: 0, last_choice: null });
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(keepable)));
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
  });

  it("keeps the action on screen from Home, with the same request as the note page", async () => {
    const user = userEvent.setup();
    vi.mocked(chooseDailyExperiment).mockResolvedValue(held(own));
    renderPage();
    const card = within(await advice());
    await user.click(await card.findByRole("button", { name: "Giữ để thử hôm nay" }));

    expect(await card.findByRole("button", { name: "Bỏ giữ việc này" })).toBeEnabled();
    expect(card.queryByRole("button", { name: "Giữ để thử hôm nay" })).not.toBeInTheDocument();
    expect(chooseDailyExperiment).toHaveBeenCalledWith(baseNoteId, {
      revision_id: keepable.revision_id, background_lens: "auto", action_key: own.action_key,
      consent_version: "action-experiment-v1", expected_experiment_id: null, expected_version: null,
    });
    expect(screen.getAllByText("Đã giữ một việc nhỏ để thử hôm nay. Bạn có thể dừng bất cứ lúc nào.").length).toBeGreaterThan(0);
  });

  it("shows an action kept earlier (on the note page) and stops keeping it", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(held(own));
    vi.mocked(undoDailyExperiment).mockImplementation(() => {
      vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
      return Promise.resolve();
    });
    renderPage();
    const card = within(await advice());
    await user.click(await card.findByRole("button", { name: "Bỏ giữ việc này" }));

    expect(await card.findByRole("button", { name: "Giữ để thử hôm nay" })).toBeEnabled();
    expect(vi.mocked(undoDailyExperiment).mock.calls[0][0]).toEqual({ experiment_id: held(own).id, expected_version: 1 });
  });

  it("asks once before replacing the kept action with the one on screen", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(held(light, { version: 3 }));
    vi.mocked(chooseDailyExperiment).mockResolvedValue(held(own, { id: "10000000-0000-4000-8000-000000000002" }));
    renderPage();
    const card = within(await advice());
    expect(await card.findByText("Việc đang giữ")).toBeInTheDocument();
    expect(card.getAllByText(light.action).length).toBeGreaterThan(0);

    await user.click(card.getByRole("button", { name: "Thay việc đang giữ" }));
    expect(chooseDailyExperiment).not.toHaveBeenCalled();
    await user.click(card.getByRole("button", { name: "Xác nhận thay việc đang giữ" }));
    await waitFor(() => expect(chooseDailyExperiment).toHaveBeenCalledWith(baseNoteId, expect.objectContaining({
      action_key: own.action_key, expected_experiment_id: held(light).id, expected_version: 3,
    })));
    expect(await card.findByRole("button", { name: "Bỏ giữ việc này" })).toBeInTheDocument();
    expect(card.queryByText("Việc đang giữ")).not.toBeInTheDocument();
  });

  it("opens the look-back only when asked and records the outcome", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(held(own));
    vi.mocked(reflectDailyExperiment).mockResolvedValue(held(own, { state: "reflected", outcome: "helpful", version: 2 }));
    renderPage();
    const card = within(await advice());
    await card.findByRole("button", { name: "Bỏ giữ việc này" });
    expect(card.queryByRole("group", { name: "Điều gì đúng với bạn?" })).not.toBeInTheDocument();

    await user.click(card.getByRole("button", { name: "Mở phần nhìn lại" }));
    await user.click(card.getByRole("button", { name: "Có ích một chút" }));
    expect(await card.findByText("Có ích một chút")).toBeInTheDocument();
    expect(vi.mocked(reflectDailyExperiment).mock.calls[0][0]).toEqual({ experiment_id: held(own).id, expected_version: 1, outcome: "helpful" });
    expect(card.queryByRole("button", { name: "Bỏ giữ việc này" })).not.toBeInTheDocument();
  });

  it("follows the action on screen: on a low day the lighter action is the one kept", async () => {
    const user = userEvent.setup();
    moodServer.save(baseNoteId, "Đuối");
    vi.mocked(chooseDailyExperiment).mockResolvedValue(held(light));
    renderPage();
    const card = within(await advice());
    expect(await card.findByText(light.action)).toBeInTheDocument();
    await user.click(await card.findByRole("button", { name: "Giữ để thử hôm nay" }));
    await waitFor(() => expect(chooseDailyExperiment).toHaveBeenCalledWith(baseNoteId, expect.objectContaining({ action_key: light.action_key })));
  });

  it("reads no kept action and shows no keep button when today's reading offers none", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();
    const card = within(await advice());
    expect(card.getByText(vibe.sections.micro_action)).toBeInTheDocument();
    expect(card.queryByRole("button", { name: "Giữ để thử hôm nay" })).not.toBeInTheDocument();
    expect(getCurrentDailyExperiment).not.toHaveBeenCalled();
  });

  // #700: "Hôm nay chỉ muốn đọc" folds the action box to one line.
  it("folds the action box to one line and opens it again, without a request, storage or leaving Home (#700)", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(held(own));
    const { client } = renderPage();
    const card = within(await advice());
    await card.findByRole("button", { name: "Bỏ giữ việc này" });
    const calls = () => [getDailyNote, getCurrentDailyExperiment, getCurrentMood, checkInMood, chooseDailyExperiment, undoDailyExperiment, reflectDailyExperiment, recordResonance]
      .map((mock) => vi.mocked(mock).mock.calls.length);
    const callsBefore = calls();
    const storedBefore = JSON.stringify({ ...localStorage, ...sessionStorage });

    const fold = card.getByRole("button", { name: READ_ONLY_TODAY });
    fold.focus();
    await user.keyboard("{Enter}");

    const folded = await screen.findByRole("complementary", { name: FOLDED_ACTION_LABEL });
    expect(within(folded).getByRole("button", { name: SHOW_ACTION_AGAIN })).toHaveFocus();
    expect(within(folded).getAllByRole("button")).toHaveLength(1);
    expect(folded).not.toHaveTextContent(own.action);
    expect(folded).not.toHaveTextContent("Thử một việc nhỏ");
    // The note itself and the way to the full note stay.
    expect(screen.getByRole("heading", { name: keepable.sections.hook })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Đọc đầy đủ/ })).toBeInTheDocument();
    // Not "bỏ việc": nothing was sent, nothing was written to the device, no sign-in prompt.
    expect(calls()).toEqual(callsBefore);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).toBe(storedBefore);
    expect(client.getQueryData(dailyReadOnlyKey(baseNoteId))).toBe(true);
    expect(screen.queryByText(/Đã bỏ giữ/)).not.toBeInTheDocument();

    await user.keyboard("{Enter}");
    const open = within(await advice());
    expect(open.getByRole("button", { name: READ_ONLY_TODAY })).toHaveFocus();
    expect(open.getByText(own.action)).toBeInTheDocument();
    // The kept action is still kept.
    expect(await open.findByRole("button", { name: "Bỏ giữ việc này" })).toBeInTheDocument();
    expect(undoDailyExperiment).not.toHaveBeenCalled();
  });

  it("opens the box again for the next day's note when Home stays open (#700, US-04 AC12)", async () => {
    const user = userEvent.setup();
    const { client } = renderPage();
    await user.click(await within(await advice()).findByRole("button", { name: READ_ONLY_TODAY }));
    await screen.findByRole("complementary", { name: FOLDED_ACTION_LABEL });

    const nextNoteId = "00000000-0000-4000-8000-000000000002";
    const tomorrow = { ...noteWith(projection(keepable)), id: nextNoteId, note_date: "2026-09-08" };
    vi.mocked(getDailyNote).mockResolvedValue(tomorrow);
    await act(async () => { await client.invalidateQueries(); });

    const card = within(await advice());
    expect(await card.findByRole("button", { name: READ_ONLY_TODAY })).toBeInTheDocument();
    expect(card.getByText(own.action)).toBeInTheDocument();
  });

  it("offers the fold button for an action that cannot be kept too (#700)", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(vibe)));
    renderPage();
    await userEvent.click(await within(await advice()).findByRole("button", { name: READ_ONLY_TODAY }));
    const folded = await screen.findByRole("complementary", { name: FOLDED_ACTION_LABEL });
    expect(folded).not.toHaveTextContent(vibe.sections.micro_action);
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
