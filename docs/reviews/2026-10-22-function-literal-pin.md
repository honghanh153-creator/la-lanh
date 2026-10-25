# In-function copy pin (audit O04, 22/10/2026)

`fallback_approval.py` pinned module-level copy tables and versions, but prose written as string literals
inside functions (Radar sections, Daily renderer phrases, Tarot sentence joins) could change without the
approval check noticing.

- New: `source_literals` / `function_literals` hash, per module, the sorted multiset of every non-ASCII string
  literal inside a function body (f-strings keep their text with `{}` per placeholder; docstrings excluded;
  each literal once). Key: `<module>#function_literals`.
- Scope: Daily (`daily_psychology`, `companion`, `voice`, `renderers`), every pinned Tarot module, and
  `radar.reading`.
- Pinned at `collab/integration` c3fab3311d65, the code of the current production release
  (release receipt in PR #40, not yet merged): **byte-identical, no copy change**, so no new
  owner content approval is needed for the pin itself. Every later change to such a literal now needs owner
  approval and a refresh, like a table.
- Limits: ASCII-only copy (e.g. "Chill") and text assembled from non-literal sources are not covered by this
  hash; they remain under the tables, versions and content audits.
