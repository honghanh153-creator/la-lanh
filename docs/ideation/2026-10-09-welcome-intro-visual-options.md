# Replacement welcome — visual selection

Status: the owner selected displayed option 1 and requested slightly more spectacular animation. A revised still keyframe was shown before implementation. The existing welcome now implements that selection locally; it is not deployed. No application API key or paid application request was used.

The authoritative numbering is their displayed order in this chat:

| Displayed option | Direction | Generated preview |
|---|---|---|
| 1 | Lật lá đầu tiên | `/Users/phamhanh/.codex/generated_images/019eea8d-5cee-7e90-aea9-7e655ab613c8/exec-ad428e77-d786-4b80-a0d5-228a7a6a5595.png` |
| 2 | Cửa mở vào mình | `/Users/phamhanh/.codex/generated_images/019eea8d-5cee-7e90-aea9-7e655ab613c8/exec-bf6c5a01-9548-4c56-ad72-5085924c76eb.png` |
| 3 | Thấy ích trước khi bắt đầu | `/Users/phamhanh/.codex/generated_images/019eea8d-5cee-7e90-aea9-7e655ab613c8/exec-3593cf34-ee76-442b-9fd0-05eec2c7d4d1.png` |

The selected preview is copied to `docs/design-directions/welcome-flip-2026-10-09/selected.png`. The animation-intent revision is `motion-keyframe.png` in that directory. The other previews remain unselected. Do not infer a voice choice from this visual selection.

## Shared brief

- Target: replacement first welcome of the existing mobile-first app, 390 × 844; web remains its preview surface.
- Outcome: a new reader understands why to use Lá Lành and enters the existing birth flow through one primary CTA.
- Palette: cream `#f7f4eb`, ink `#15132c`, ultraviolet `#54249b`, lime `#dfff4f`. One Be Vietnam Pro font, readable body and restrained hierarchy.
- Actual references attached to every generation: `docs/reviews/ultraviolet-fidelity-2026-10-06/after/06-welcome.png` and `01-home-full.png`. They ground design language, not their retired wording or navigation placement.
- No additional onboarding step, sign-in requirement, feature inventory or new deferred matchmaking capability.
- CTA retains explicit consent timing; viewing the welcome never creates a guest or records consent. Preserve demo, privacy, restart and pending Radar behavior.
- Images are static keyframes, not delivered animations. Implementation must supply gentle looping motion, a working pause control, reduced-motion support and no autoplay audio or flashing.

## Prompt distinctions

1. A floating textured violet card and cream/purple moon above direct copy: “Hiểu mình hơn. Bớt đoán mò.” Motion intention: slow card float/flip and orbit.
2. Copy first: “Chuyện của bạn, nhìn rõ hơn một chút.” A lunar portal between parted purple curtains. Motion intention: gentle opening and slow lunar rotation.
3. Show value first: “Bớt nghĩ vòng. Nhìn chuyện rõ hơn.” A labeled sample daily note, not a claim to already know the visitor. Motion intention: subtle note/moon animation.

Each prompt requested app content only, no device/browser chrome, warm cream/purple/lime, one font, exact Vietnamese copy, one dominant CTA, readable footer, no clipping, and date anchor 2026-10-09 with no visible date. Built-in tool used; no CLI/API fallback.

## Selected implementation

- Replaces `/welcome`, not a new route or a fourth onboarding step.
- Original copy and two CTAs preserved from option 1. No guest creation, consent or AI request when viewing or pausing the introduction.
- Three separately generated transparent raster assets under `apps/web/public/assets/welcome/`, optimized to WebP (total 384,992 bytes). Card, moon and orbit are independently animated; the orbit is layered in front of and behind the card.
- Card turns in perspective on an 8-second loop; moon drifts and rotates on a 12-second loop; orbit sweeps and changes opacity on a 9-second loop. Text, buttons and logo remain still. No sound, blinking, artificial progress or mandatory waiting.
- Shared onboarding pause state remains active through birth and reveal. Reduced-motion media preference suppresses all hero animations and hides the unnecessary motion button. Small screens keep natural vertical scrolling rather than clipping actions.
- Existing pending Radar intent, explicit restart, retry/idempotency and offline/expired messages preserved.
- Actual local flow tested with synthetic data: welcome → birth → reveal → Home. Demo, privacy, pause/resume and Profile's existing light/dark setting tested. 390 × 844, 320 × 568 and desktop 1280 × 900 reviewed.
- See the current welcome entry in project-root `design-qa.md` and `docs/reviews/security-content-2026-10-09/welcome-comparison-final.png`. Native iOS/Android and an OS-level reduced-motion toggle are not manually exercised in this unit.

Accessibility sources checked: [W3C pause/stop/hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) and [MDN reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion). This change adds no personal-data fields, external SDKs, provider requests or billing changes.

## Pending decisions

Visual selection is resolved. The optional affectionate-sharp voice is a separate choice, documented in `2026-10-09-affectionate-sharp-voice-samples.md`; direct remains approved.

Security/content progress and outstanding release gates are in `docs/reviews/2026-10-09-security-content-work-handoff.md`. These previews do not mean the full plan is done, reviewed, pushed or deployed.
