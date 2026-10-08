import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import userEvent from "@testing-library/user-event";

import {
  activateReadingProjection,
  chooseDailyExperiment,
  ApiProblem,
  getDailyNote,
  getContextualReading,
  getCurrentDailyExperiment,
  listSavedNotes,
  type DailyNote,
  type ReadingProjection,
} from "../../shared/api/client";
import { clearCachedDailyNote } from "../../shared/storage/noteCache";
import { NoteDetailPage } from "./NoteDetailPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    activateReadingProjection: vi.fn(),
    chooseDailyExperiment: vi.fn(),
    getCurrentDailyExperiment: vi.fn(),
    getDailyNote: vi.fn(),
    getContextualReading: vi.fn(),
    listSavedNotes: vi.fn(),
  };
});

describe("NoteDetailPage rich reading", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearCachedDailyNote();
    vi.mocked(listSavedNotes).mockResolvedValue([]);
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
  });

  it("uses the same active projection as Home instead of legacy note prose", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(note);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><NoteDetailPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: "Hook từ active revision" })).toBeInTheDocument();
    expect(screen.queryByText("Legacy title")).not.toBeInTheDocument();
    expect(screen.getByText("Căn cứ trong lá số").closest("details")).not.toHaveAttribute("open");
    expect(screen.getByRole("link", { name: /Chuyện này cần nhìn từ góc nào/ })).toHaveAttribute(
      "href",
      "/tarot?origin=daily&context=general&prompt=daily-clarity",
    );
  });

  it("keeps the selected Home context instead of displaying the auto reading", async () => {
    const selected: ReadingProjection = {
      ...note.reading_projection,
      active: {
        ...note.reading_projection.active,
        experiment: {
          action_key: "c".repeat(64),
          action: "Chọn một việc làm trước.",
          observation: "Bạn đã chọn được việc nào để làm trước chưa?",
          permission: "Không hợp thì bỏ qua.",
        },
        sections: {
          ...note.reading_projection.active.sections,
          hook: "Bạn bận cả buổi, việc vẫn chưa xong.",
          thesis: "Chuyển việc liên tục khiến nhiều việc cùng dang dở.",
        },
      },
    };
    vi.mocked(getDailyNote).mockResolvedValue(note);
    vi.mocked(getContextualReading).mockResolvedValue(selected);
    vi.mocked(chooseDailyExperiment).mockRejectedValue(new ApiProblem(503, "UNAVAILABLE", "Test rejection"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/note/today?context=work"]}><NoteDetailPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: selected.active.sections.hook })).toBeInTheDocument();
    expect(getContextualReading).toHaveBeenCalledWith("work", expect.any(AbortSignal));
    expect(screen.queryByRole("heading", { name: note.reading_projection.active.sections.hook })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Chia sẻ" })).toHaveAttribute("href", "/card?context=work");
    await userEvent.click(screen.getByRole("button", { name: /Giữ để thử hôm nay/ }));
    await waitFor(() => expect(chooseDailyExperiment).toHaveBeenCalledWith(note.id, expect.objectContaining({
      background_lens: "work",
      revision_id: selected.active.revision_id,
      action_key: selected.active.experiment?.action_key,
    })));
  });

  it("does not display the cached auto note when the selected context cannot be fetched", async () => {
    vi.mocked(getDailyNote).mockResolvedValue(note);
    vi.mocked(getContextualReading).mockRejectedValue(new ApiProblem(503, "UNAVAILABLE", "Test rejection"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(["daily-note"], note);
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/note/today?context=work"]}><NoteDetailPage /></MemoryRouter></QueryClientProvider>);
    expect(await screen.findByRole("heading", { name: "Chưa mở được note." })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: note.reading_projection.active.sections.hook })).not.toBeInTheDocument();
  });

  it("lets a user open the full-chart update from the note they are reading", async () => {
    const user = userEvent.setup();
    const update = {
      ...note.reading_projection.active,
      revision_id: "00000000-0000-4000-8000-000000000011",
      mode: "full_synthesis" as const,
      precision: "exact" as const,
      sections: {
        ...note.reading_projection.active.sections,
        hook: "Bản đủ lớp đã thật sự khác",
      },
    };
    const withUpdate: DailyNote = {
      ...note,
      reading_projection: {
        ...note.reading_projection,
        active: {
          ...note.reading_projection.active,
          mode: "vibe_fallback" as const,
          precision: "unknown" as const,
        },
        available_update: {
          revision_id: update.revision_id,
          message: "Có một bản đọc mới đang chờ bạn",
          content: update,
        },
      },
    };
    const activated: ReadingProjection = {
      scope_key: note.reading_projection.scope_key,
      active: update,
      available_update: null,
      aura_transition: note.reading_projection.aura_transition,
    };
    vi.mocked(getDailyNote).mockResolvedValue(withUpdate);
    vi.mocked(activateReadingProjection).mockResolvedValue(activated);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><NoteDetailPage /></MemoryRouter></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: /Mở bản đủ lớp/ }));

    expect(await screen.findByRole("heading", { name: "Bản đủ lớp đã thật sự khác" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Note này có một bản đủ lớp" })).not.toBeInTheDocument();
  });

  it("refetches after an activation conflict so a stale gift is removed", async () => {
    const user = userEvent.setup();
    const update = {
      ...note.reading_projection.active,
      revision_id: "00000000-0000-4000-8000-000000000011",
      mode: "full_synthesis" as const,
      precision: "exact" as const,
    };
    const withUpdate: DailyNote = {
      ...note,
      reading_projection: {
        ...note.reading_projection,
        active: {
          ...note.reading_projection.active,
          mode: "vibe_fallback" as const,
          precision: "unknown" as const,
        },
        available_update: {
          revision_id: update.revision_id,
          message: "Có một bản đọc mới đang chờ bạn",
          content: update,
        },
      },
    };
    vi.mocked(getDailyNote)
      .mockResolvedValueOnce(withUpdate)
      .mockResolvedValueOnce(note);
    vi.mocked(activateReadingProjection).mockRejectedValue(
      new ApiProblem(409, "READING_UPDATE_CONFLICT", "Reading update changed"),
    );
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><NoteDetailPage /></MemoryRouter></QueryClientProvider>);

    await user.click(await screen.findByRole("button", { name: /Mở bản đủ lớp/ }));

    await waitFor(() => expect(getDailyNote).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("heading", { name: "Note này có một bản đủ lớp" })).not.toBeInTheDocument();
  });
});

const note = {
  id: "00000000-0000-4000-8000-000000000001", note_date: "2026-09-07",
  title: "Legacy title", body: "Legacy body", full_body: "Legacy full body",
  context_label: "Legacy context", content_version: "legacy-v1", persona_mode: "vibe",
  persona_label: "Mềm", persona_version: "v1", source_level: "date_only_sun",
  astrology_source_version: "2.10.03", fallback_used: false, fallback_reason: null,
  created_at: "2026-09-07T00:00:00Z", awakening: null, sky_chapter: null,
  reading_projection: {
    scope_key: "a".repeat(64), available_update: null,
    aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
    active: {
      revision_id: "00000000-0000-4000-8000-000000000010", source: "deterministic",
      mode: "full_synthesis", purpose: "daily_note", tradition: "western", precision: "exact",
      sections: {
        hook: "Hook từ active revision", thesis: "Thesis từ active revision.",
        manifestation: "Ngoài đời có thể trông như một nhịp dừng.", transit: null,
        micro_action: "Chọn một việc nhỏ.",
      },
      evidence: { title: "Căn cứ trong lá số", claims: ["Dữ kiện đã duyệt"], framework_disclosure: "Khung diễn giải." },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.", created_at: "2026-09-07T00:00:00Z",
    },
  },
} satisfies DailyNote;
