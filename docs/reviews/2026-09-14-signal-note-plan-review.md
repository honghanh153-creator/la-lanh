---
title: Signal Note Experience plan review
date: 2026-09-14
document: docs/plans/2026-09-14-2047-feat-signal-note-experience-plan.md
mode: non-interactive
status: resolved
---

# Signal Note Experience plan review

## Coverage

- Coherence: completed.
- Feasibility: completed.
- Product lens: completed.
- Design lens: completed.
- Security lens: completed.
- Scope guardian: completed.
- Adversarial: completed.
- Cross-model pass: not configured; no independent-provider receipt was available.

## Applied corrections

1. Context now travels in a private enum-only POST body and has a lens-specific projection identity, while the existing GET remains context-free.
2. Date-only, cusp, limited and full-chart rendering must all honor Context Dial without changing facts, evidence, precision or confidence.
3. “Đổi góc” is non-persistent and requires an explicit new Context Dial choice; cancelling preserves the note.
4. Hit/miss feedback remains optional and purpose-consented, but receives one transaction boundary, record-bound encryption, 30-day retention, reset/revoke and deletion tests.
5. Mood remains a secondary Home section below the Daily Note hierarchy.
6. Documentation work no longer serializes independent backend/frontend work.
7. An early native vertical slice and final iOS/Android runtime smoke were added; asset sync alone is not treated as native proof.
8. A representative-user comprehension gate was added for the distinction between chart evidence and context-dependent framing.

## Dismissed or narrowed findings

- Removing all hit/miss persistence was not applied. The established product contract already requires consent, reset and deletion for bounded feedback, and the Profile surface provides a user-visible status/control consumer. The lower-friction part of the finding was retained: “Đổi góc” works without data collection or consent.
- A deterministic automatic context cycle was not added because the design correction requires explicit user selection instead; an automatic cycle would contradict user control.
- The claim that Capacitor `ios.scheme` must match the Xcode target name was rejected: that field controls the WebView navigation scheme, not the Xcode build target. Native compilation remains required, but the plan no longer directs an invalid rename.

## Remaining release conditions

- Qualified Vietnamese legal review is still required for production impact-assessment and cross-border-processing obligations.
- A missing iOS or Android toolchain is a release No-Go, not permission to substitute web QA.
