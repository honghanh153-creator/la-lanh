import type { DailyNote, ShareFormat } from "../../shared/api/client";
import {
  buildShareArtSvg,
  elementForPersonaLabel,
  elementNames,
  personaTag,
  SHARE_PRIVACY_FOOTER,
  type ShareArtSpec,
} from "./shareArt";

type ShareableNote = Pick<DailyNote, "title" | "persona_label" | "persona_mode" | "reading_projection">;

/** Copy that is allowed on a note share card: headline, one supporting line, plain persona tag. */
export function shareCopy(note: ShareableNote) {
  const reading = note.reading_projection?.active;
  return {
    title: reading?.sections.hook ?? note.title,
    body: reading && reading.mode !== "vibe_fallback" ? reading.sections.manifestation : "",
    tag: personaTag(note.persona_label),
  };
}

/** Same art spec for the in-app card and the public safe link (snapshot title/body/label only). */
export function noteArtSpec(input: { title: string; body?: string | null; personaLabel?: string | null }): ShareArtSpec {
  const element = elementForPersonaLabel(input.personaLabel);
  const tag = personaTag(input.personaLabel);
  return {
    kicker: "Note hôm nay",
    hook: input.title,
    support: input.body || null,
    badge: [tag, element ? elementNames[element] : null].filter(Boolean).join(" · ") || "Lá Lành",
    tag: null,
    element,
    sign: null,
    footer: SHARE_PRIVACY_FOOTER,
  };
}

export function noteSpecFromNote(note: ShareableNote): ShareArtSpec {
  const copy = shareCopy(note);
  return noteArtSpec({ title: copy.title, body: copy.body, personaLabel: note.persona_label });
}

export function cardSvg(note: ShareableNote, format: ShareFormat, fontCss = "") {
  return buildShareArtSvg(noteSpecFromNote(note), format, fontCss);
}
