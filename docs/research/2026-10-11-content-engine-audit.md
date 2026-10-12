# Content engine audit — Astro Daily, Tarot, Luna rewrite (11/10/2026)

Read-only audit after the owner found the staging Note and Tarot text hard to read. Staging and production both run with generation off (no Luna): what users see is the deterministic engine output.

## Luna rewrite: what it can and cannot change

- Asynchronous write-behind: deterministic text is served first; a queued rewrite appears only on a later visit (Daily: as an "available update" the user must tap; Tarot: silently on reopening).
- Eligible only with generation on, separate AI consent, pilot cap (≤20 active sessions), Western readings; `beta_10/50` sample readings, not people.
- Daily: may replace only hook, manifestation, micro_action (70 words total). Never the thesis paragraph, transit, evidence, disclaimers, experiment, labels. `daily_detail` has no worker projector.
- Tarot: may replace headline, summary, per-card meaning, closing. Never scene/example, reflection question, action, names, labels. Roast readings are never rewritten; the raw question is never sent (one of six focus keys).
- Quality evidence: one synthetic paid probe (output not kept); the "670-case corpus" is a count manifest; no human-scored results.
- Latent bug: a Luna-rewritten Daily note combined with Roast becomes half-roasted (Roast matches exact direct text; the thesis still matches, the rewritten hook/action do not; gentle/sharp tone can flip).
- **Conclusion:** Luna can at best smooth a few short fields for a small pilot. It cannot fix structure, labels, disclaimers, jargon, relevance or the source meaning.

## Astro Daily: root causes (most impact first)

1. Thesis = four sentences from four tables (rule meaning + issue meaning + takeaway + limitation), no subject; the same idea repeats ~6 times across hook/thesis/scene/action/observation (`daily_psychology.py:1093-1137`).
2. "Vì sao hôm nay?" rarely explains the situation: the issue comes from natal factors, the shown transit is the most salient (outer planets weighted). Simulation (20 charts × 60 days): 18/337 shown transits were part of the issue's evidence; Pluto 28%; same transit most consecutive days.
3. Jargon ("vuông", "orb 0.335°", "pha tách dần", degrees, "Nhà 8") is forced by exact canonical-claim gates; plain `transit_copy` exists but Daily replaces it. Conflicts with US-03 AC07 (plain-language evidence).
4. The 70/30 natal/transit composition gate forces padding sentences and silently drops the transit (~16% of days).
5. Rendering: four disclaimers, two headings for one action, "Vì sao hôm nay?" up to three times; limitation inside the main text. Bug: date-only/non-exact users never see the micro action on Note Detail.
6. Arena leads ("Ví dụ với người kia.") are fragments kept to pass the meaning gate.
7. Review tooling never reviews the thesis or transit/evidence text.
- Volume: 15 situations × (6 headlines, 8 scenes, 8 actions); one chart sees 2–7 situations over 60 days.

## Tarot: root causes

1. Does not answer the question: the question only maps to 5 intents (keyword match), 8 goal keywords and the 5-card layout; headline is fixed per intent; yes/no questions get no stance.
2. Card meanings ignore position (one meaning/pitfall/action per card per topic; positions only change wrapper words; 3-card positions 1 and 3 fall into catch-all wording).
3. Summary is a list ("Card: sentence." ×N), encouraged by the every-card-name gate; only 3 cross-card links exist.
4. Duplicated scaffolding: "Ví dụ để đối chiếu: Ví dụ: Có lần…", "Một việc bạn có thể thử: Thử nhé:", "Ý chính của lá:", English names ("8 of Swords").
5. Gates are word-count/marker based (push padding); audit uses one fixed question per topic.
6. Readings freeze at draw time for ~30 days; engine fixes don't reach existing sessions.

## Constraints any fix must keep

Privacy envelope (no raw question/birth data to providers), no prediction/mind-reading, evidence binding (or change the gate contract deliberately), card order/positions, Roast exact-text mapping with owner re-approval for new lines, content audits and versioning (frozen saved/shared snapshots).
