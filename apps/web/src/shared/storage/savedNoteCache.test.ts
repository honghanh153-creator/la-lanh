import { beforeEach, describe, expect, it } from "vitest";

import type { DailyNote } from "../api/client";
import { readLocalSavedNotes, saveNoteLocally } from "./savedNoteCache";

const richNote = {
  id: "00000000-0000-4000-8000-000000000009",
  note_date: "2026-09-06",
  title: "Một note đã mở",
  body: "Nội dung an toàn để lưu.",
  full_body: "PRIVATE_FULL_BODY",
  context_label: "Nguyên tố trội Đất",
  content_version: "daily-note-v3",
  persona_mode: "aura",
  persona_label: "Chắc",
  persona_version: "persona-v2",
  source_level: "natal_chart",
  astrology_source_version: "2.10.03",
  fallback_used: false,
  fallback_reason: null,
  created_at: "2026-09-06T00:00:00Z",
  awakening: {
    headline: "PRIVATE_AURA",
    summary: "PRIVATE_AURA_SUMMARY",
    factors: ["PRIVATE_FACTOR"],
    precision_label: "PRIVATE_PRECISION",
    scoring_version: "PRIVATE_SCORING",
    confidence: "PRIVATE_CONFIDENCE",
  },
  sky_chapter: {
    title: "PRIVATE_SKY",
    summary: "PRIVATE_TRANSIT",
    phase: "exact",
    phase_label: "PRIVATE_PHASE",
    signal_label: "PRIVATE_SIGNAL",
    orb: 0.1,
    observed_at: "2026-09-06T12:00:00Z",
    orb_policy_version: "transit-orbs-v1",
    ranking_version: "sky-chapter-salience-v1",
    disclaimer: "PRIVATE_DISCLAIMER",
  },
} satisfies DailyNote;

describe("savedNoteCache privacy projection", () => {
  beforeEach(() => localStorage.clear());

  it("persists only the allowlisted saved-card projection", () => {
    saveNoteLocally(richNote);

    const serialized = localStorage.getItem("la-lanh-saved-notes-v1") ?? "";
    expect(serialized).not.toContain("PRIVATE_");
    expect(serialized).not.toContain("awakening");
    expect(serialized).not.toContain("sky_chapter");
    expect(serialized).not.toContain(richNote.title);
    expect(serialized).not.toContain(richNote.body);
    expect(readLocalSavedNotes()[0]?.revision_id).toBeUndefined();
  });

  it("sanitizes legacy rich entries during read", () => {
    localStorage.setItem("la-lanh-saved-notes-v1", JSON.stringify([{
      daily_note_id: richNote.id,
      saved_at: new Date().toISOString(),
      note: richNote,
    }]));

    readLocalSavedNotes();

    expect(localStorage.getItem("la-lanh-saved-notes-v1")).not.toContain("PRIVATE_");
    expect(localStorage.getItem("la-lanh-saved-notes-v1")).not.toContain(richNote.title);
  });
});
