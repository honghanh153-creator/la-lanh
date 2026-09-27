# User experience release gate

This gate exists because a feature can be technically correct and still be a poor product.
Every beta release must pass both automated checks and a short human review.

## Automated blocking checks

Run `pnpm experience:audit` and `pnpm content:audit`. A release is blocked when Radar or Daily Note:

- produces no concrete next action;
- publishes an action without inspectable chart evidence;
- repeats the same action inside one report;
- ignores the selected relationship context or reading voice;
- uses deterministic, coercive or generic filler language;
- exposes raw birth date, coordinates or other transient input.
- assembles a hook, real-life scene and action from different contexts;
- shows an internal availability/status sentence instead of useful user copy;
- asks the user to perform an action that cannot be observed or checked in ordinary life.

`pnpm check` includes this command, so it cannot be skipped by the normal release path.

## Human experience review

Review the first-run flow, Daily Note, Reading Detail, Radar form and Radar result at 360 px and
390 px widths.

1. In five seconds, can a new user say what this screen does and what happens after the CTA?
2. Does every heading add new information rather than restate the paragraph below it?
3. Can the main result be scanned without opening technical evidence?
4. Is every suggested action concrete, reversible and usable in ordinary life?
5. Does the report explain uncertainty without turning the disclaimer into the main content?
6. Are selected, focus, error, loading and empty states visible without relying on color alone?
7. Can the flow be completed with keyboard only, without horizontal scroll or clipped text?
8. For Daily Note, can a reviewer answer in one sentence: “Chuyện gì đang xảy ra, nó xuất hiện ở
   đâu, và tôi có thể thử việc gì?” If not, the release is blocked even when all technical tests pass.

Record the tested URL, viewport, screenshots and any accepted limitations in the release evidence.
An engineer cannot mark the UX gate passed from unit tests alone.
