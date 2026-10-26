# R03 — Hợp gu contact copy: owner-review workbook (draft)

Date: 2026-10-22 · Audit item: R03 · Story: `docs/user-stories/US-22-hop-gu-rieng-tung-cap.md`
Workbook: `docs/reviews/2026-10-22-r03-radar-copy-workbook.xlsx`

**Status: decided under owner delegation (26/10/2026), not yet wired.** Was: DRAFT, awaiting owner approval. Nothing here is wired into the renderer or added to the
approved fallback store (`fallback-approval.json`). No user sees these sentences until the owner approves
them. Wiring happens later in a separate PR.

## What it is

New Vietnamese sentences for the Hợp gu "fit" and "friction" sections. Each sentence is about one directed
synastry contact: your planet → aspect → the other person's planet (for example, "Mars của bạn → Venus của
người kia" is a different contact from the reverse). One sentence is written for every
contact × context (crush, friend, partner, someone) × voice (straight_warm, gentle_specific,
playful_grounded, roast) combination. The sentences describe things you can see happen and suggest checking
them in real life. They make no verdict, give no score, and do not guess what the other person feels or
intends.

| Sheet | Content |
|---|---|
| Hướng dẫn | Purpose, copy rules (Vietnamese), how the gate checks provenance, review columns, limits |
| Câu theo contact | 560 rows: ID, tier, contact, body_a, aspect kind/family, body_b, section, context, voice, sentence, word count, `evidence_id` pattern, fixture pair count, 4 self-check columns, Owner decision (Duyệt/Sửa/Bỏ dropdown), Owner note |
| Độ phủ | Projected metrics and every directed contact in the 50-pair fixture (532 rows) with pair count, renderable count, tier, and the reason it is not covered |
| Đối chiếu hiện tại | 6 representative pairs × 2 context/voice combinations: current fit/friction prose from `build_radar_reading` next to the new lines |

## Counts

- 35 contacts × 4 contexts × 4 voices = **560 sentences**, all unique after normalisation.
- **Tier 1 (31 contacts):**
  - the 25 most frequent contacts where both bodies are personal planets (Sun, Moon, Mercury, Venus,
    Mars). That is the 23 contacts seen in at least 3 pairs, plus 2 of the contacts seen in 2 pairs
    (`venus:square:mars`, `moon:trine:moon`), picked by greedy coverage to break the tie;
  - every contact involving a non-personal body that appears in at least 5 pairs and that Radar shows:
    `true_node:square:sun`, `jupiter:trine:pluto`, `jupiter:trine:sun`, `mercury:trine:true_node`,
    `saturn:trine:neptune`, `venus:square:jupiter`.
- **Tier 2 (4 contacts, coverage boost, each in 4 pairs):** `sun:conjunction:uranus`,
  `sun:conjunction:true_node`, `neptune:trine:venus`, `moon:trine:true_node`.
- **Excluded on purpose:** `neptune:square:pluto` (6 pairs) and `neptune:sextile:uranus` (5 pairs).
  `_motifs` drops a contact when both bodies are generational, so these two can never be shown.
- **Sections:**
  - flow contacts (trine, sextile) → fit;
  - tension contacts (square, opposition) → friction;
  - fusion contacts (conjunction) are marked `fusion`. Five are drafted as fit. `sun:conjunction:uranus`
    is drafted as friction. The owner can change any of these.

## Projected AC01 coverage (computed from the fixture, not estimated)

A pair counts as covered when at least 2 of the contacts Radar shows for it (`_motifs`) are in the
draft. None of the 50 pairs is low-signal.

| Set | Pairs covered |
|---|---|
| Tier 1 | **36/50 (72%)** |
| Tier 1 + Tier 2 | **43/50 (86%)** |

Distribution with Tier 1+2:

| Covered contacts per pair | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| Pairs | 5 | 2 | 19 | 12 | 7 | 2 | 3 |

These numbers are an upper bound. The renderer must actually choose these contacts for the visible
fit/friction sections and declare them in `highlights[].contact_lines`.

The fixture's contact distribution is very flat: 532 distinct directed contacts, at most 6 pairs each. So
frequency-picked copy covers real users less well than it covers this fixture. Reaching 50/50 would take
about 10 more contacts beyond Tier 1+2, picked by greedy coverage, which overfits the fixture. A principled full target
would be all 125 personal–personal directed contacts (2,000 sentences).

## AC02 and AC03: expectations and limits

- **AC02, contact lines alone:** context changes 100% of them and voice changes 100% of them, across
  the 4 voices in this file.
  - Same contact and context: all 4 voices differ in the first 3 words, and word overlap is below 50%
    for every pair of voices (script-checked).
  - Same contact and voice: across contexts, word overlap is at most 38.5%.
- **AC02 on the real sections:**
  - Today each reading has about 26.7 fit/friction sentences, and none of them change with context or
    voice.
  - If wiring only *appends* the covered contact lines, the changed share is only **about 9%**.
  - To reach 50%, wiring has to *replace* the generic chapter prose, so contact lines become most of
    the fit/friction sentences.
- **Voice set mismatch:**
  - Runtime `RelationshipVoice` has `deep_dive`, not `roast`, and the gate iterates the runtime enum.
  - The owner must decide whether roast replaces deep_dive or is added as a fifth voice. If it is added,
    deep_dive needs its own lines.
  - Roast also needs a `VoiceProfile`: tease the user only, never cruel, never about appearance or body.
- **AC03 cannot be met by this workbook alone:**
  - Each sentence belongs to one contact, and every drafted contact appears in at least 2 pairs. With
    one variant per cell, cross-pair overlap of contact lines is **100%**.
  - Simulated frozen variants per cell (picked by seed) bring it to 83% (k=2), 68% (k=3) and 55% (k=4).
  - The gate also counts the headline, summary and other visible prose, which overlap 91% today.
  - Getting below 30% needs more than this copy: several variants per cell, frozen at creation (R05),
    plus sentences built from pair-specific facts. Examples are orb band, element/modality balance,
    two-contact combinations, and house overlays when both birth times are known. All of these would be
    in the wiring PR.
  - There is also a structural tension the wiring design must solve. AC01 credits a line only if it is
    never shown without its contact. AC03 penalises any line shown in another pair.

## Self-checks run (script, on all 560 sentences)

| Check | Result |
|---|---|
| Banned words (`soulmate`, `định mệnh`, `chắc chắn`, `red flag`, `điểm hợp`) | **0 hits** |
| Wider judgement list (`challenging`, `tri kỷ`, `duyên số`, `hợp nhau`, `không hợp`, `toxic`, `%`, …) | 0 hits |
| Roast lines: appearance/body words | 0 hits |
| Mind-reading phrases (`thích bạn`, `nhớ bạn`, `muốn bạn`, `cảm nắng`, …) | 0 hits |
| Exactly one sentence each (same splitter as `variety_baseline`) | Pass |
| Length (counted in syllables) | 18–30 |
| At least one observable-action verb | 560/560 |
| Uniqueness | 560/560 unique |

The checks are heuristics. They do not replace the owner's reading. The Hướng dẫn sheet quotes the
banned words, but only as the rule itself.

## Owner review and what happens after approval

1. **Review.** The owner sets Owner decision to Duyệt, Sửa or Bỏ on each row. For Sửa, write the
   replacement text in Owner note.
2. **Separate wiring PR, using approved rows only:**
   - declare each line as `contact_lines: [{text, evidence_id}]` in the cited highlight;
   - keep stored results frozen until they expire (24 hours for a private check, 30 days for an accepted
     invite);
   - choose variants once, when the result is created, and freeze them (R05/AC05);
   - keep the AC07 unknown-time rule: no Moon for a person whose birth time is unknown;
   - register the copy in the content grammar and approval manifest (AC08).
3. **Gate.** After wiring, run `scripts/audit_radar_us22.py` (PR #47). Its strict-xfail flips only when
   AC01–AC03 pass.

## Handoff (AGENTS.md)

- **Sources checked:**
  - US-22;
  - `apps/api/app/domains/radar/reading.py`: body/aspect tables, `_motifs` filter, section and highlight
    structure;
  - `relationships/knowledge.py` (voice profiles) and `relationships/models.py` (voice enum);
  - `scripts/variety_baseline.py`: contexts, `_radar_chart` unknown-time handling, sentence splitter;
  - `scripts/audit_radar_us22.py` at PR #47 head `d4a1623`: the provenance rule;
  - `tests/fixtures/variety/radar-pairs-v1.json`.
- **Findings fixed here:** none in code. This is a draft-copy deliverable only.
- **Unresolved risks:**
  - AC03 is structurally unmet by single-variant contact copy;
  - the roast vs deep_dive voice decision;
  - AC02 needs wiring that replaces the generic prose;
  - coverage is measured on a small, flat synthetic fixture;
  - fusion section choices need an owner call.
- **AC/DoD still open:**
  - US-22 AC01–AC03 and AC05 (not wired);
  - AC08 (grammar/manifest);
  - AC09 (audit in `pnpm check`);
  - AC10 (owner approval of this file).
- **Privacy:** synthetic data only. The workbook contains no personal data. No new data flows.


## Delegated decision (26/10/2026)

The owner delegated copy decisions to Claude on 26/10/2026. Hợp gu's fourth voice is `deep_dive`, as the runtime has it,
not `roast` (decision record #84, item 8). A first-pass reviewer read the 420 non-roast rows against the "Hướng dẫn"
rules, US-22 and this document. Claude then checked a sample and every row the reviewer was unsure about. The
"Owner decision" / "Owner note" columns carry each decision ("Uỷ quyền 26/10: …"). This is one careful reading, not a
reader comprehension test.

| Voice | Approve | Rewrite | Not used |
|---|---|---|---|
| straight_warm | 135 | 5 | – |
| gentle_specific | 127 | 13 | – |
| playful_grounded | 121 | 19 | – |
| roast | – | – | 140 (fourth voice is `deep_dive`) |

The 37 rewrites keep their contact, section, context and voice; Codex polishes them before wiring. They fix:
- **The other person's inner need stated as fact** (mostly gentle_specific: "muốn được khen / công nhận / tự hào"). The
  workbook's mind-reading list did not catch these.
- **Double meanings and hidden verdicts in jokes:**
  - possible sexual readings;
  - "không sai người" (an implied "right person");
  - rating the other person ("chấm thêm", "đánh giá năm sao");
  - "bẩm sinh";
  - one line that normalised opening a partner's bank history.
- **Friction lines that judge the other person,** and one playful line that praised answering a crush's fear with a plan,
  against sibling lines that say listen first.

**`deep_dive` lines (added 26/10/2026, sheet "Câu deep_dive"):** 140 draft sentences, 35 contacts × 4 contexts. Each keeps
its cell's section and contact meaning: 92 fit, 48 friction. They passed a script check:
- one sentence each;
- no banned, fate, astrology or flagged-frame words, and no workbook mind-reading phrases;
- first three words differ from the three sibling voices;
- word overlap with each sibling under 50% (highest 39%);
- 140 unique lines, and no opening phrase used more than 8 times.

They run 31–40 syllables. **Decision (delegated):** `deep_dive` may use up to 40 syllables, against 30 for the other
voices, because its closing "check or limit" is what makes the voice. All are approved as a draft for Codex to polish.
Four friction/crush lines are flagged in the note column.

Conditions for the wiring PR (not done here):
1. **Wire the `deep_dive` lines** and run the AC02 gate on them. One line per cell still leaves 100% overlap between pairs
   that share a contact (AC03).
2. **Break the fixed template per voice.** Most straight_warm lines open "Khi…", most gentle_specific "Có thể…/Nếu…", and
   playful_grounded is almost always "scenario: punchline". With 2–6 lines per reading this shows. Add second variants per
   cell (also needed for AC03), or a renderer rule against two lines with the same opening in one reading.
3. **Thin repeated jokes:** hệ thống/thuật toán, "hội … N thành viên", "không lương", kế toán, kịch bản, phiên bản, trà
   sữa. Each motif should appear at most once per reading.
4. **Keep the stated limits:** each contact's astrological meaning and the fusion section choices were not re-judged
   here. AC03, AC05 and AC08–AC10, plus wiring, stay open.
