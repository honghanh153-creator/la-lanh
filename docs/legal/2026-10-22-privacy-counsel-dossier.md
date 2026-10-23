# Privacy dossier for owner and counsel (audit P09/P10)

Prepared 22/10/2026 from the code at `collab/integration` c3fab33 plus the open audit PRs. **This is not legal
advice and not a legal conclusion.** It collects facts, file references and the questions a Vietnamese data-
protection lawyer must answer before the next scope change. Claude did not accept any DPA or change consent text.

## Legal baseline (checked 22/10/2026)

- Law on Personal Data Protection No. 91/2025/QH15, passed 26/6/2025, in force 01/01/2026 (official text on
  [vbpl.moj.gov.vn](https://vbpl.moj.gov.vn); summary: [PwC VN brief, 28/01/2026](https://www.pwc.com/vn/vn/publications/legal-news-brief/20260128-new-rules-personal-data-protection.html)).
- Decree No. 356/2025/NĐ-CP detailing the Law, issued 31/12/2025, in force 01/01/2026, replacing Decree
  13/2023/NĐ-CP ([official .doc on vbpl.moj.gov.vn](https://vbpl.moj.gov.vn/TW/Lists/vbpq/Attachments/187276/ND.356.2025.doc);
  [EY alert, 03/2026](https://www.ey.com/content/dam/ey-unified-site/ey-com/vi-vn/technical/tax/documents/ey-vietnam-legal-alert-march-2026-decree-no356-2025-nd-cp-providing-detailed-guidance-for-implementation-of-personal-data-protection-law-viet.pdf)).
- Only the existence, dates and replacement were re-verified here, from secondary sources pointing at the official
  text. Article-level duties below are **questions**, not quotes. Counsel should read the official PDFs and check
  for amending decrees after 31/12/2025 (an earlier research note also cites Decree 87/2026; not re-checked here).
- Platform rules (Apple App Privacy, Google Play Data Safety) must be re-read at submission time.

## P10 — inventory, destinations and processors

Processors named in the data map (`store-privacy-data-map.md:12`) and runbooks:

| Processor | Role | Location | Data | Status |
|---|---|---|---|---|
| Hetzner VPS | hosting (API, web, workers, backups on disk) | Germany | everything the API processes | live |
| Supabase | PostgreSQL | Frankfurt, Germany | all stored rows (app-level AES-GCM for prose, snapshots, labels) | live |
| OpenAI | Luna rewrite (Daily pilot) | provider region per DPA | minimized derived Daily content, never raw birth data or Tarot question | pilot on, ≤20 opt-in; **DPA not yet accepted by owner** |
| Google | sign-in | — | — | **off** until acceptance (P12) |

Field inventory (summary; the data map is the detailed source):

| Field | Purpose | Stored as | Lifetime | Deletion path |
|---|---|---|---|---|
| Owner birth date | chart | AES-GCM | profile lifetime (30 d anonymous / 365 d linked inactivity) | guest erase, precision withdrawal |
| Owner birth time, place, coordinates | houses/Moon | AES-GCM; legacy plaintext place columns NULLed on write (P06 check) | profile lifetime | supplement removal |
| Chart and derived astrology profile | readings | AES-GCM snapshot; legacy JSON readable (P06) | profile lifetime | recompute/erase |
| Daily prose, mood | Daily | prose AES-GCM; **mood plaintext enum** | visible ≤24 h, purge eligible from 18 h; saved notes follow profile | cleanup, history clear |
| Tarot question, frame, reading | Tarot | one AES-GCM payload; raw question no longer in Web Storage (P01, #41) | 29 d 18 h | delete, expiry cleanup |
| Radar B birth data (private check) | one result | **not stored** (computed in memory) | — | — |
| Radar nickname, result | Hợp gu | AES-GCM; context/voice plaintext; HMAC retry digests | private 24 h; consented invite 30 d | cleanup (deferred by send fence) |
| Share snapshot | share link | AES-GCM | 14 d access; inactive rows purged by cleanup (P05, #49) | revoke, cleanup |
| Experiment, resonance | feedback | AES-GCM | 29 d 18 h / 30 d | cleanup, reset |
| Device copies | offline retry | localStorage ids/mood | mood and save 24 h, unsave 30 d (P04, #48) | clear-device |
| Matching profile/consent | deferred feature | — | new collection returns 410 (P02, #42) | legacy read/erase kept |

**Fixed in this PR:** the Apple App Privacy table put the Radar audience in the "Tracking" column. Tracking is now
"No" for that row (there is no tracking), and the audience moved into the data description.

Questions for counsel (P10):

1. Controller/processor roles for Hetzner, Supabase and OpenAI under Law 91/2025 and Decree 356/2025; is a DPA plus
   the providers' standard terms enough, or is a separate agreement form required?
2. Hosting in Germany: does storing Vietnamese users' data in Germany and Frankfurt count as cross-border transfer
   requiring an impact assessment dossier and filing? Content, timing and authority.
3. Is a processing impact assessment required for the app itself (sensitive data? birth data and derived astrology
   profile; relationship results)? Which fields count as sensitive under Decree 356?
4. Mood as a plaintext operational enum: acceptable with RLS and grants, or should it be encrypted?
5. Incident process: notification deadlines and recipients; what the operator log must hold.
6. In-app copy says other history is kept "tối đa 30 ngày" while physical deletion can be delayed by send fences
   and backups (P05, P07). Does the copy have to say so?

## P09 — third-party (B) data and rights

Facts from the code (`radar/service.py`):

- **Private check:** A enters B's birth data after attesting that B allowed it (`authorization_attested`,
  `AUTHORIZED_INPUT_VERSION`). B's raw data is not stored. The result, labelled with A's nickname for B, is kept 24 h.
  B never interacts with the app and has **no receipt** and no self-service view, export or withdrawal.
- **Invite:** B uses B's own profile and consents (`radar-pair-v1`). B receives a receipt for view and withdraw:
  `RECEIPT_TTL = 7 days`. A's result copy lives `CONSENTED_RESULT_TTL = 30 days`. **From day 8 to day 30, B
  cannot see or withdraw the result through the app.**
- A's attestation is a statement by A, not proof that B consented.

Owner decisions needed (P09):

| # | Decision | Options |
|---|---|---|
| D1 | Receipt vs result gap | (a) extend `RECEIPT_TTL` to 30 days (receipt is a capability: more exposure if leaked); (b) shorten consented result to 7 days; (c) keep both and run a manual rights channel for days 8–30 |
| D2 | B rights without a receipt | Manual request channel (email/in-app form) with verification that does **not** collect B's DOB again over an unprotected channel. Suggested: B proves possession of the invite link or receipt, or A deletes on request. Counsel to confirm what is enough. |
| D3 | Private-check lawful basis | Is A's attestation an acceptable basis for processing B's birth data transiently, with a 24 h derived result? If not: invite-only, or no stored result. |
| D4 | Notice to B | Whether B must be informed (and how) when A runs a private check; currently B is not contacted. |

Process to prepare once decided (not built here): request intake, identity check, response deadline per Decree
356, deletion across rows and rewrite jobs, response template, log of requests without storing B's raw data.

## What is not claimed

- That M1's "not identifiable" assessment is a legal conclusion for the whole app.
- That AES-GCM, no-store or timers erase every copy (backups P07, provider copies, recipient screenshots).
- That consent v1 must be bumped: no scope change is proposed here; a bump or new waiver needs a separate decision.
