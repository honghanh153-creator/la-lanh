---
title: Current Product Baseline - Cosmic Glass Signal
date: 2026-09-01
type: reference
source: prototype-and-current-app
---

# Current Product Baseline — Cosmic Glass Signal

## Purpose

This file records the baseline inherited from 2026-09-01 and the selected update on 2026-09-02. Direction **02 — Cosmic Glass Signal** supersedes Electric Note as the visual and vocabulary source of truth for US-01–US-06 while preserving the useful “personal note” metaphor. It is a reference for UI, UX, copy, interaction feel, security and release readiness.

## Reference artifacts

| Artifact | Path | Use |
|---|---|---|
| Selected Cosmic Glass direction | `docs/design-directions/home-2026-09-02-v2/02-cosmic-glass-signal.png` | Visual source of truth for every US-01–US-06 screen and light/dark component hierarchy. |
| Approved visual direction | `prototype/public/design-reference.png` | Primary reference for Home note concept, palette, collage energy, and CTA balance. |
| Current prototype Home | `prototype/home-screenshot.png` | Legacy reference for Note hierarchy and mood row; not the selected visual style. |
| Current prototype saved screen | `prototype/saved-screenshot.png` | Reference for saved-note library tone. |
| Current prototype birth time screen | `prototype/birthTime-screenshot.png` | Reference for unlock/update profile flow. |
| Current prototype share/card screen | `prototype/card-screenshot.png` | Reference for shareable artifact direction, with privacy corrections required by US-05. |
| Design QA note | `prototype/design-qa.md` | Notes on palette, typography, scanability, and current fidelity gaps. |

## Selected baseline to apply

- Midnight indigo atmosphere, smoky-lilac glass, cyan/lime signal accents and restrained warm highlights.
- Dark is the closest expression of the selected reference; light uses the same hierarchy and components on a mist-lilac ground.
- Glass is functional: use it for controls, disclosures, locked layers and navigation. Reading/note surfaces stay substantially opaque.
- Be Vietnam Pro là font duy nhất; không quá năm type token và không dùng handwriting font.
- `Vibe · <3–5 chữ>` is the compact Sun-only label; `Aura · <3–5 chữ>` is reserved for a valid deeper NatalChart.
- Mood prompt is exactly “Hôm nay bạn thấy sao?”; never call mood “Vibe”.
- Factual placements, chart depth, precision and source versions remain available in provenance/detail.

## Legacy qualities to preserve, not legacy styling

- “A small note you cannot ignore” as the core content metaphor.
- Daily Note remains the primary reading surface, not a dashboard tile among equals.
- Celestial atmosphere supports hierarchy; it never competes with content or reduces contrast.

## UX qualities to preserve

- The app should feel like a personal note from the universe, not a dashboard.
- Home opens on Daily Note, not a feed.
- Mood check-in uses “Hôm nay bạn thấy sao?”, remains light and tappable, and is visually distinct from Vibe/Aura.
- Share/save are useful but must not overpower the note.
- Unlock prompts should feel like a hidden layer being opened, not a form request.

## Corrections required before using this baseline as product behavior

- The share mock must not show date of birth, even in stylized text.
- Font usage must be consolidated into a small type system; the current fallback mix is useful for prototyping but too inconsistent for product.
- Local storage must not hold sensitive birth data.
- Web/PWA is a reference/companion surface for behavior and responsive QA. The native app remains the release target and release gate; a passing web build does not prove secure storage, native sharing, permissions, deep links, background/resume behavior or platform accessibility.
- House/Rising/Moon claims must be gated by actual data completeness and chart precision.

## Native release gates

- Secure storage and deletion verified on device for guest token and sensitive birth data; no raw birth data in browser storage.
- Native share sheet, image export permissions, cancel/error callbacks and metadata stripping verified on supported OS versions.
- Deep link, offline/resume, app lifecycle, safe-area, keyboard, screen reader, Dynamic Type/text scaling, Reduce Motion and Reduced Transparency verified natively.
- Transport security, certificate policy, log/crash redaction and applicable mobile privacy/security checklist pass.
- No release claim may cite web/PWA-only evidence for a native-only gate; unresolved native evidence stays explicitly `Pending` or `Blocked`.
