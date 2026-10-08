---
title: Daily scene and advice psychology engine
date: 2026-10-02
status: approved-for-implementation
---

# Daily scene and advice psychology engine

## Goal capsule

Home must feel like a useful “thẻ hôm nay”, not a generic self-help paragraph. The main card describes one concrete situation, cue, or action the user may notice today. Advice is a separate, bounded “Thử điều này hôm nay” block. Home does not show chart evidence, “Vì sao dành cho bạn?”, or “Đọc từ ngày sinh”; those remain available on the detail surface.

The engine will use ten psychology books as editorial lenses, not as clinical authority and not as source text. It stores only source metadata and original Vietnamese atoms. It must not diagnose, predict a certain event, or infer sensitive traits.

## Requirements

- R1 — Daily `hook` and `manifestation` are descriptive, observable, and free of advice language.
- R2 — Daily `micro_action` is one small, reversible action with a visible completion condition.
- R3 — Scene and advice are selected independently but must be compatible through a typed matrix.
- R4 — Selection remains deterministic for one local date and produces at least 365 distinct daily compositions.
- R5 — Astrology may rank the lens but must not be presented as proof of a psychological condition.
- R6 — Home removes evidence/source disclosure and presents the advice as a distinct block.
- R7 — Reading detail keeps chart evidence and the existing disclaimer.
- R8 — Release gates reject imperative language in scenes, abstract scenes, certainty, diagnosis, unsafe advice, and mismatched scene/advice pairs.
- R9 — No raw birth data, mood, question, or reading copy is sent to search or an external psychology service.
- R10 — Book-derived concepts are paraphrased into original product rules; no copyrighted passages are stored.

## Source set and boundaries

The initial ten anchors are: *Thinking, Fast and Slow*; *Influence*; *Mindset*; *Flow*; *Emotional Intelligence*; *Self-Compassion*; *The Happiness Trap*; *Nonviolent Communication*; *Mistakes Were Made (But Not by Me)*; and *The Person and the Situation*.

They cover fast inference, social influence, response to challenge, attention, emotion recognition, self-talk, distance from thoughts, observation-versus-judgment, self-justification, and situational context. The product uses these as editorial dimensions only. It does not claim that these books form a diagnostic model, that every claim is equally established, or that a card predicts what will happen.

## Implementation units

### U1 — Versioned psychology matrix

Files:

- `apps/api/app/domains/readings/daily_psychology.py`
- `apps/api/app/domains/readings/models.py`
- `apps/api/tests/readings/test_daily_psychology.py`

Add immutable source metadata, issue families, observable scenes, and compatible advice atoms. Compose them with the existing local-date mixed-radix scheduler. Record source IDs and matrix version in internal `knowledge_refs`; never expose book names as a claim about the user.

### U2 — Renderer and gates

Files:

- `apps/api/app/domains/readings/renderers.py`
- `apps/api/app/domains/readings/gates.py`
- `apps/api/app/domains/readings/review_agent.py`
- `apps/api/tests/readings/test_renderers.py`
- `apps/api/tests/readings/test_gates.py`
- `apps/api/tests/readings/test_review_agent.py`

Apply the matrix only to Western Daily Note output. Keep Reading Detail unchanged. Add separate scene/advice semantics to the meaning and release-review gates. A scene fails if it tells the user what to do; advice fails if it is vague, diagnostic, coercive, or unrelated to the selected issue.

### U3 — Home information architecture

Files:

- `apps/web/src/features/home/HomePage.tsx`
- `apps/web/src/features/home/HomePage.test.tsx`
- `apps/web/src/shared/styles/signal-note.css`

Present “Một cảnh có thể gặp hôm nay” as the main card. Render “Lời nhắc hôm nay” as a visually separate advice block and keep the hold/reflect CTA. Remove evidence and birth-data source labels from Home. Preserve mood, feedback, context selection, share, detail, and unlock behavior.

### U4 — Product and operations documentation

Files:

- `docs/foundation/daily-psychology-scene-advice-engine.md`
- `docs/foundation/la-lanh-reading-knowledge-spec.md`
- `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`
- `docs/operations/content-matrix-release-gate.md`
- `design-qa.md`

Document the matrix, source/license boundary, security/privacy posture, and UX acceptance rules.

## Verification contract

- API unit tests prove source coverage, deterministic replay, 365-day uniqueness, arena coverage, scene/advice separation, and five-gate acceptance.
- Web tests prove Home has no chart-source/evidence disclosure, shows a descriptive scene before advice, and retains every live CTA.
- `pnpm content:audit` and `pnpm content:review` must pass.
- Full lint, typecheck/build, and test suites must pass.
- Browser QA at mobile width verifies scan order, contrast, no overflow, and no console errors.

## Definition of done

- A first-time user can answer “thẻ hôm nay nói mình có thể gặp cảnh gì?” after one scan.
- The main card contains no advice; the advice is clearly labeled and actionable.
- Home contains neither “Vì sao dành cho bạn?” nor “Đọc từ ngày sinh/lá số”.
- The deterministic engine can generate 365 non-repeating accepted cards without storing user history.
- Content generation remains server-side, local, source-traceable, privacy-minimal, and non-diagnostic.
