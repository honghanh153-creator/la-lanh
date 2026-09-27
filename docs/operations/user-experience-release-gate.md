# User experience release gate

This gate exists because a feature can be technically correct and still be a poor product.
Every beta release must pass both automated checks and a short human review.

## Automated blocking checks

Run `pnpm experience:audit`. A release is blocked when Radar:

- produces no concrete next action;
- publishes an action without inspectable chart evidence;
- repeats the same action inside one report;
- ignores the selected relationship context or reading voice;
- uses deterministic, coercive or generic filler language;
- exposes raw birth date, coordinates or other transient input.

`pnpm check` includes this command, so it cannot be skipped by the normal release path.

## Human experience review

Review the first-run flow, Radar form and result at 360 px and 390 px widths.

1. In five seconds, can a new user say what this screen does and what happens after the CTA?
2. Does every heading add new information rather than restate the paragraph below it?
3. Can the main result be scanned without opening technical evidence?
4. Is every suggested action concrete, reversible and usable in ordinary life?
5. Does the report explain uncertainty without turning the disclaimer into the main content?
6. Are selected, focus, error, loading and empty states visible without relying on color alone?
7. Can the flow be completed with keyboard only, without horizontal scroll or clipped text?

Record the tested URL, viewport, screenshots and any accepted limitations in the release evidence.
An engineer cannot mark the UX gate passed from unit tests alone.
