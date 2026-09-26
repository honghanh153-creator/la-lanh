import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  acknowledgeAuraTransition,
  activateReadingProjection,
  ApiProblem,
  getDailyNote,
  type DailyNote,
  type ReadingProjection,
} from "../../shared/api/client";
import { clearCachedDailyNote } from "../../shared/storage/noteCache";
import { AuraCutoverPage } from "./AuraCutoverPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    acknowledgeAuraTransition: vi.fn(),
    activateReadingProjection: vi.fn(),
    getDailyNote: vi.fn(),
  };
});

const transitionId = "t".repeat(64);
const active = content("00000000-0000-4000-8000-000000000010", "vibe_fallback", "Note Vibe hiện tại");
const aura = content("00000000-0000-4000-8000-000000000011", "full_synthesis", "Một bản đọc nhiều lớp hơn");

describe("AuraCutoverPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    clearCachedDailyNote();
  });

  it("shows an evidence receipt and keeps the current note with opaque acknowledgement", async () => {
    const user = userEvent.setup();
    const current = projection(active, aura, "aura_ready");
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(current));
    vi.mocked(acknowledgeAuraTransition).mockResolvedValue({
      ...current,
      aura_transition: { ...current.aura_transition, acknowledged: true },
    });
    renderPage();

    const heading = await screen.findByRole("heading", { name: "Aura không tự thay Note của bạn." });
    expect(heading).toBeInTheDocument();
    await waitFor(() => expect(heading).toHaveFocus());
    expect(screen.getByText("Các House và lĩnh vực đời sống")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: aura.sections.hook })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Giữ Note hiện tại" }));

    await waitFor(() => expect(acknowledgeAuraTransition).toHaveBeenCalledWith("s".repeat(64), transitionId));
    expect(localStorage.getItem(`la-lanh-aura-transition-ack-v1:${transitionId}`)).toBe("1");
  });

  it("keeps the current Aura acknowledged after refresh with empty local storage", async () => {
    localStorage.clear();
    const current = projection(active, aura, "aura_ready");
    vi.mocked(getDailyNote).mockResolvedValue(noteWith({
      ...current,
      aura_transition: { ...current.aura_transition, acknowledged: true },
    }));

    renderPage();

    expect(await screen.findByText("Bạn đã xem lựa chọn này trước đó.")).toBeInTheDocument();
    expect(localStorage.getItem(`la-lanh-aura-transition-ack-v1:${transitionId}`)).toBeNull();
  });

  it("activates the available revision only after an explicit choice", async () => {
    const user = userEvent.setup();
    const current = projection(active, aura, "aura_ready");
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(current));
    vi.mocked(activateReadingProjection).mockResolvedValue({
      ...current,
      active: aura,
      available_update: null,
      aura_transition: { ...current.aura_transition, acknowledged: true },
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Dùng Aura hôm nay" }));

    await waitFor(() => expect(activateReadingProjection).toHaveBeenCalledWith("s".repeat(64), aura.revision_id));
  });

  it("does not overclaim a limited result", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(noteWith(projection(active, null, "limited")));
    renderPage();

    expect(await screen.findByRole("heading", { name: "Kết quả hiện tại vẫn còn giới hạn." })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Dùng Aura hôm nay" })).not.toBeInTheDocument();
  });

  it("refetches after an activation conflict and preserves the current choice", async () => {
    const user = userEvent.setup();
    const refreshedNote = noteWith(projection(active, null, "aura_ready"));
    vi.mocked(getDailyNote)
      .mockResolvedValue(refreshedNote)
      .mockResolvedValueOnce(noteWith(projection(active, aura, "aura_ready")));
    vi.mocked(activateReadingProjection).mockRejectedValue(new ApiProblem(409, "STALE", "stale"));
    renderPage();

    const activateButton = await screen.findByRole("button", { name: "Dùng Aura hôm nay" });
    const fetchesBeforeActivation = vi.mocked(getDailyNote).mock.calls.length;
    await user.click(activateButton);

    expect(await screen.findByText("Bản Aura đã thay đổi ở nơi khác. Lá Lành đã tải lại trạng thái hiện tại; bạn không mất bản Note đang dùng.")).toBeInTheDocument();
    await waitFor(() => expect(vi.mocked(getDailyNote).mock.calls.length).toBeGreaterThan(fetchesBeforeActivation));
  });
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><AuraCutoverPage /></MemoryRouter></QueryClientProvider>);
}

function content(revisionId: string, mode: "vibe_fallback" | "full_synthesis", hook: string) {
  return {
    revision_id: revisionId,
    source: "deterministic" as const,
    mode,
    purpose: "daily_note" as const,
    tradition: "western" as const,
    precision: mode === "full_synthesis" ? "exact" as const : "unknown" as const,
    sections: {
      hook,
      thesis: "Nhiều nhịp đang được đọc cùng nhau.",
      manifestation: "Ngoài đời có thể trông như một khoảng dừng.",
      transit: null,
      micro_action: "Chọn một việc nhỏ.",
    },
    evidence: { title: "Căn cứ trong lá số", claims: ["Dữ kiện đã duyệt"], framework_disclosure: "Khung diễn giải." },
    disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
    created_at: "2026-09-16T00:00:00Z",
  };
}

function projection(activeReading: ReturnType<typeof content>, available: ReturnType<typeof content> | null, readiness: "aura_ready" | "limited"): ReadingProjection {
  return {
    scope_key: "s".repeat(64),
    active: activeReading,
    available_update: available ? { revision_id: available.revision_id, message: "Có một bản đọc mới đang chờ bạn", content: available } : null,
    aura_transition: {
      profile_readiness: readiness,
      transition_id: readiness === "aura_ready" ? transitionId : null,
      acknowledged: false,
      unlock_layers: readiness === "aura_ready" ? ["multi_factor", "house_arena"] : [],
    },
  };
}

function noteWith(readingProjection: ReadingProjection): DailyNote {
  return {
    id: "00000000-0000-4000-8000-000000000001",
    note_date: "2026-09-16",
    title: "Note hôm nay",
    body: "Một note.",
    full_body: "Một note đầy đủ.",
    context_label: "Tự động",
    content_version: "v1",
    persona_mode: "vibe",
    persona_label: "Mềm",
    persona_version: "v1",
    source_level: "date_only_sun",
    astrology_source_version: "2.10.03",
    fallback_used: false,
    fallback_reason: null,
    created_at: "2026-09-16T00:00:00Z",
    awakening: null,
    sky_chapter: null,
    reading_projection: readingProjection,
  };
}
