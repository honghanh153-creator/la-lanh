# Cosmic Glass Signal — product UI system

Status: selected for US01–US06 on 2026-09-02.

## Product vocabulary

- Sun-only profile: `Vibe · <archetype>`, for example `Vibe · Mềm`.
- Complete natal profile: `Aura · <archetype>`, for example `Aura · Mềm`.
- Self-reported mood prompt: `Hôm nay bạn thấy sao?` — never reuse “Vibe” here.
- Factual placements such as `Mặt Trời Cự Giải` stay in reveal, profile detail and provenance, not the Home summary pill.

The archetype is a short, tentative presentation label, not a diagnosis or a complete description of a person.

## Five type tokens

| Token | Mobile size/line | Weight | Use |
|---|---:|---:|---|
| Display | 40/43 | 800 | One reveal title or welcome promise |
| Greeting | 32/36 | 800 | Page greeting and major outcome |
| Section | 18/24 | 700–800 | Card and section headings |
| Body | 16/25 | 400–600 | Note, explanations and fields |
| Label | 13/18 | 600–800 | Pill, navigation, source and validation |

Be Vietnam Pro is the only typeface across UI, notes, cards and exported assets. Personality comes from weight, scale, spacing and coral underlines; no handwriting or secondary font is allowed.

## Surface matrix

| Surface | Material | Blur | Readability rule |
|---|---|---:|---|
| App background | Celestial image + solid theme color | No | Focal artwork stays at top-right; central/lower negative space remains quiet |
| Brand, profile and icon controls | Thin glass | Yes | 44px target, visible border and focus ring |
| Archetype pill | Thin glass | Yes | One line when possible; label remains understandable without color |
| Daily Note outer frame | Thin glass | Yes | Decorative/protective layer only |
| Daily Note paper | Opaque ivory | No | Dark ink, body contrast ≥ 4.5:1 |
| Mood, settings and format controls | Medium glass | Yes | Selected state uses shape/border plus color |
| Input fields | Strong/opaque surface | No | Labels never rely on placeholders |
| Consent and provenance | Medium glass | Yes | Plain-language disclosure remains expanded when required |
| Locked insight | Medium glass | Yes | Lock and action label both communicate state |
| Bottom navigation | Medium glass | Yes | `aria-current`, icon + text, safe-area padding |
| Modal/sheet | Strong glass | Yes | Focus enters dialog and returns to trigger |

When Reduce Transparency is enabled, every glass surface becomes an opaque semantic surface without losing hierarchy.

## Signal palette

- Midnight indigo: product canvas and depth.
- Smoky lilac: secondary text, borders and non-primary signals.
- Acid lime: one primary action or selected state within a local group.
- Electric cyan: provenance/source and informational signal.
- Warm peach: one intimate accent or warning emphasis.
- Ivory paper: long-form content surface.

## App shell and routes

- Persistent tabs after onboarding: `Hôm nay`, `Khám phá`, `Đã lưu`, `Mình`.
- Onboarding, consent, birth input, reveal detail, card maker and public share use focused flow navigation without the bottom bar.
- Note detail returns to Home without losing mood/save state.
- The shell observes the device safe area; 320, 390 and 430px layouts must not scroll horizontally.

## State contract

Every feature screen must own loading, empty, retryable error, offline/cached, success and destructive-confirmation states when applicable. Status changes are announced through a live region. Focus is visible; a selected mood/segment/tab has a text or shape cue in addition to color.
