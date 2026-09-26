import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DailyNote, ReadingProjection } from "../api/client";
import {
  clearCachedDailyNote,
  dismissReadingUpdate,
  isReadingUpdateDismissed,
  readCachedDailyNote,
  replaceCachedReadingProjection,
  writeCachedDailyNote,
} from "./noteCache";

const note = {
  id: "00000000-0000-4000-8000-000000000001",
  note_date: "2026-09-06",
  title: "Một note mới",
  body: "Một câu ngắn.",
  full_body: "Một câu dài hơn.",
  context_label: "Tổng hòa chart",
  content_version: "daily-note-v3",
  persona_mode: "aura",
  persona_label: "Chắc",
  persona_version: "persona-v2",
  source_level: "natal_chart",
  astrology_source_version: "2.10.03",
  fallback_used: false,
  fallback_reason: null,
  created_at: "2026-09-06T00:00:00Z",
  awakening: null,
  sky_chapter: null,
} satisfies DailyNote;

describe("noteCache privacy", () => {
  beforeEach(() => {
    localStorage.clear();
    clearCachedDailyNote();
  });

  afterEach(() => vi.useRealTimers());

  it("keeps private note fallback out of persistent browser storage", () => {
    writeCachedDailyNote(note);

    expect(readCachedDailyNote()?.note.id).toBe(note.id);
    expect(localStorage.length).toBe(0);
  });

  it("removes plaintext cache created by older builds", () => {
    localStorage.setItem("la-lanh-daily-note-cache-v1", JSON.stringify({ note }));

    clearCachedDailyNote();

    expect(localStorage.getItem("la-lanh-daily-note-cache-v1")).toBeNull();
  });

  it("forgets the private fallback at the 36-hour boundary", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-06T00:00:00Z"));
    writeCachedDailyNote(note);

    vi.advanceTimersByTime(36 * 60 * 60 * 1000);

    expect(readCachedDailyNote()).toBeNull();
    expect(readCachedDailyNote()).toBeNull();
  });

  it("reads a rich projection only for the exact scope and active revision", () => {
    const richNote = {
      ...note,
      reading_projection: projection("scope-a", "00000000-0000-4000-8000-000000000010"),
    } satisfies DailyNote;
    writeCachedDailyNote(richNote);

    expect(readCachedDailyNote({
      scopeKey: "scope-a",
      revisionId: "00000000-0000-4000-8000-000000000010",
    })?.note.id).toBe(note.id);
    expect(readCachedDailyNote({
      scopeKey: "scope-a",
      revisionId: "00000000-0000-4000-8000-000000000099",
    })).toBeNull();
  });

  it("replaces only the matching projection and clears its stale update", () => {
    const first = projection("scope-a", "00000000-0000-4000-8000-000000000010");
    first.available_update = {
      message: "Có một bản đọc mới đang chờ bạn",
      revision_id: "00000000-0000-4000-8000-000000000011",
      content: { ...first.active, revision_id: "00000000-0000-4000-8000-000000000011" },
    };
    writeCachedDailyNote({ ...note, reading_projection: first } satisfies DailyNote);

    expect(replaceCachedReadingProjection(
      projection("scope-b", "00000000-0000-4000-8000-000000000020"),
    )).toBe(false);
    expect(replaceCachedReadingProjection(
      projection("scope-a", "00000000-0000-4000-8000-000000000011"),
    )).toBe(true);
    expect(readCachedDailyNote()?.note.reading_projection?.active.revision_id)
      .toBe("00000000-0000-4000-8000-000000000011");
    expect(readCachedDailyNote()?.note.reading_projection?.available_update).toBeNull();
  });

  it("keeps dismissed update identity in memory for this app session", () => {
    dismissReadingUpdate("scope-a", "00000000-0000-4000-8000-000000000011");

    expect(isReadingUpdateDismissed(
      "scope-a",
      "00000000-0000-4000-8000-000000000011",
    )).toBe(true);
    expect(localStorage.length).toBe(0);
  });
});

function projection(scopeKey: string, revisionId: string): ReadingProjection {
  return {
    scope_key: scopeKey,
    aura_transition: { profile_readiness: "aura_ready", transition_id: "b".repeat(64), acknowledged: true, unlock_layers: ["multi_factor"] },
    active: {
      revision_id: revisionId,
      source: "deterministic" as const,
      mode: "full_synthesis" as const,
      purpose: "daily_note" as const,
      tradition: "western" as const,
      precision: "exact" as const,
      sections: {
        hook: "Bạn không thiếu quyết tâm.",
        thesis: "Bạn đang cần một nhịp rõ hơn.",
        manifestation: "Ngoài đời, điều này có thể hiện ra khi bạn chậm trả lời.",
        transit: null,
        micro_action: "Viết xuống một điều cần nói.",
      },
      evidence: {
        title: "Căn cứ trong lá số",
        claims: ["Sao Thủy ở Song Tử"],
        framework_disclosure: "Chiêm tinh là một khung diễn giải.",
      },
      disclaimer: "Lá gợi một góc nhìn — quyền quyết định vẫn ở bạn.",
      created_at: "2026-09-07T00:00:00Z",
    },
    available_update: null,
  };
}
