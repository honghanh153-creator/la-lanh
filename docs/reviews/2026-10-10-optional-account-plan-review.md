# Optional account plan review — 2026-10-10

Plan: `docs/plans/2026-10-10-1310-fix-optional-login-and-data-continuity-plan.md`.
Six independent native reviewer contexts: coherence, feasibility, security, design, scope and adversarial. No paid external cross-model calls. This is document review, not code/security certification.

Accepted and applied: U5 must implement remaining confirmed lifecycle defects (coherence P2); U4 must own history-clear confirmation/error/success UI (design P2); device credentials must be digest-only (security advisory). Feasibility, scope and adversarial returned no additional actionable findings. Underlying managed SMTP delivery, real PostgreSQL concurrency/migration rehearsal, physical mobile and live verification remain release gates, not waived by this review.

Implementation uses sequential native edits in the existing dirty worktree. Existing changes are preserved; no commit, deploy, live auth settings or billable provider calls are authorized in this run. Account 365-day inactivity is a newly disclosed opt-in policy, not a retroactive change to existing guest storage. New history retention must not silently shorten pre-policy history.
