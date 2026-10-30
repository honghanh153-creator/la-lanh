# P09 / P10 scope, applicability and exemption assessment (draft, 29/10/2026)

**Status: draft by Claude for the owner/engineering assessment. Not legal advice. No compliance claim.**
The owner decided on 29/10/2026 not to engage counsel, so open P09/P10 items are owned by owner/engineering
(registry rows P09, P10 and R07, and P09 D1–D4). This document records facts from the code and docs, the rules
checked in the official texts, the gaps between them, and proposed changes. It does not conclude that the app
complies with the law, and it does not conclude that the app breaks it. Every proposal needs the owner's
confirmation (section 6).

Code base read: `collab/integration` at `e0d62fa`. Production state comes from
`docs/operations/hetzner-supabase-release-runbook.md` (release `89ebdb0cf6b9`, 26/10/2026). Claude had no server,
database or provider access, so the live flags, row counts and provider consoles were not checked.

How the law was checked. The full texts of Law 91/2025/QH15 and Decree 356/2025/NĐ-CP were read from the Official
Gazette (Công báo) originals. The author re-read the article text cited below for Law Art. 1, 2, 4, 9, 10, 11,
19–24, 33, 38 and 39, and for Decree Art. 3–6, 10, 12, 17–19 and 41. Decree 330/2026/NĐ-CP (penalties) was read
by a sub-agent from the scanned official PDF only; the author did not re-read it. Sources are in section 7.

## 1. Legal baseline (verified 29/10/2026)

| Topic | Rule (paraphrased) | Where |
|---|---|---|
| In force | Law 91 in force 01/01/2026; Decree 356 (31/12/2025) in force 01/01/2026; Decree 13/2023 ceased to have effect that day | Law Art. 38.1; Decree 356 Art. 42.2 |
| Who is covered | Vietnamese agencies, organisations **and individuals**, plus foreign ones processing data of Vietnamese citizens | Law Art. 1.2; Decree 356 Art. 2 |
| Basic data | Date of birth (3.2); place of birth (3.4); marital status (3.8); family relationships (3.9); a catch-all for anything else that identifies a person (3.11) | Decree 356 Art. 3 |
| Sensitive data | Includes private life and personal or family secrets (c); health (d); sex life or orientation (e); location from a positioning service (h); tracking of behaviour and activity on online services (l). Birth time and astrology are not named. | Decree 356 Art. 4.1 |
| Consent validity | Must be voluntary, and the person must know (a) data types and purpose, (b) the controller, (c) their rights and obligations | Law Art. 9.2 |
| Consent form | Clear and verifiable; **per purpose**; not conditioned on other purposes; silence is not consent | Law Art. 9.3–9.4 |
| Consent records | In-app technical consent is accepted; the controller stores it and carries the burden of proof; no default opt-in; tell the person when the data is sensitive | Decree 356 Art. 6.1–6.4 |
| Consent timing | Consent before collection, unless the law says otherwise | Law Art. 11.1 |
| Without consent | Includes performing the data subject's agreement (d); oversight measures still required | Law Art. 19.1–19.2 |
| Withdrawal and restriction | Request in writing (electronic counts); not retroactive | Law Art. 10 |
| Rights | Know; consent or withdraw; view and correct; obtain a copy, delete, restrict, object; complain | Law Art. 4.1 |
| Response times | Acknowledge in 2 working days. Withdraw, restrict or object: 15 days (20 if a processor must act). View, correct or provide a copy: 10 days (15). Delete: 20 days (30). One extension allowed, with reasons. The controller must publish the procedure. | Decree 356 Art. 5 |
| Automated processing | Tell the person about automated processing, explain how the algorithm works and how it affects them, and offer a way to opt out | Decree 356 Art. 10.3 |
| Cloud | The contract must reference Vietnamese data-protection law, data flows, roles, security and deletion; data on cloud must be encrypted at rest and in transit | Decree 356 Art. 12.2, 12.4 |
| Cross-border | Includes **using a platform outside Vietnam to process data collected in Vietnam** and storage on servers or cloud abroad. File a transfer impact dossier within **60 days** of the first transfer, then update it (every 6 months if changed). | Law Art. 20.1–20.3, 22; Decree 356 Art. 17.1, 18 |
| Cross-border exemptions | State bodies; employee data on cloud; a person transferring their own data; press; already-public data; emergencies; cross-border HR; travel, payment, visa and similar contracts | Law Art. 20.6; Decree 356 Art. 17.3 |
| Processing impact assessment (DPIA) | Controllers (organisations **or individuals**) prepare it and file one original within **60 days** of first processing, then update it | Law Art. 21–22; Decree 356 Art. 19 |
| Data protection officer | "Agencies and organisations" must appoint a qualified person or unit, or hire a provider | Law Art. 33.2; Decree 356 Art. 13 |
| Breach notice | Notify the authority within 72 h when a violation may harm a person's life, health, honour, dignity or property | Law Art. 23.1; Decree 356 Art. 28 |
| Children | The legal representative exercises a child's rights | Law Art. 24.2 |
| Exemption | Small enterprises and startups may skip Art. 21, 22 and 33.2 for 5 years; household businesses and micro-enterprises are exempt from them. **Not** if they sell processing services, **directly process sensitive data**, or reach 100,000 data subjects (cumulative). **Art. 20 is never exempt.** | Law Art. 38.2–38.3; Decree 356 Art. 41 |
| Third-party data entered by a user | No specific rule. What applies: data subjects must respect others' data (Art. 4.2(b)); consent comes from the data subject (Art. 9.1, 11.1) | Law Art. 4, 9, 11 |
| Authority | The dedicated unit of the Ministry of Public Security (A05) and the national data-protection portal | Decree 356 Art. 39 |
| Transition | Consent obtained under Decree 13 stays valid | Law Art. 39 |

Platform rules re-read, notice and consistency only:

- **Apple 5.1.1(i)–(ii) and 5.1.2(i).** The privacy policy must say what is collected and how, retention and
  deletion, and how to withdraw consent. Sharing with third parties, including third-party AI, needs explicit
  permission.
- **Apple 5.1.1(viii).** Apps may not compile personal information from sources other than the user directly, or
  without explicit consent. This is relevant to `private_check`.
- **Google Play User Data.** The policy must name the developer entity and contact, data types, sharing,
  retention and deletion. Prominent disclosure and affirmative consent are required. Account deletion must be
  available in the app and on the web.

## 2. Processing inventory per purpose

Built from `store-privacy-data-map.md`, the 22/10 dossier, `ConsentPage.tsx` and the API domains. Processors and
regions:

- **Hetzner VPS, Germany**: API, web, workers, and the daily `pg_dump` backups on local disk (14 days).
- **Supabase PostgreSQL, Frankfurt**: all stored rows. Provider snapshots and point-in-time recovery follow the
  plan's own lifecycle, which this repo does not know.

"User" means the data subject entered it. "A-about-B" means user A entered person B's data.

| # | Purpose | Fields | Source | Stored as | Processor and region | Retention | Deletion path |
|---|---|---|---|---|---|---|---|
| 1 | Guest identity and session | guest ID, hashed device credential, CSRF token, HttpOnly cookie | system | DB rows; cookie on the device | Hetzner, Supabase (DE) | 30 days of inactivity (anonymous); device access 30 days | guest erase; expiry cleanup |
| 2 | Birth profile, basic (`birth-profile-v1`) | birth date | user | AES-GCM | Hetzner, Supabase | profile lifetime | guest erase |
| 3 | Birth profile, deep (`birth-profile-deep-v1`) | birth time, birthplace, coordinates | user | AES-GCM; legacy plaintext place columns NULLed on write (P06) | same | profile lifetime | supplement removal (`DELETE /v1/birth-profile/supplement`); guest erase |
| 4 | Chart and readings | derived natal/transit factors, astrology profile, reading plans and revisions | derived | AES-GCM | same | profile lifetime | recompute; guest erase |
| 5 | Daily note and mood | daily prose; mood enum (Rực, Chill, Đuối, Căng, Lạc trôi) | user + derived | prose AES-GCM; **mood plaintext enum** | same | visible ≤24 h, purge eligible from 18 h; saved notes keep the profile lifetime | history clear; unsave; cleanup |
| 6 | Tarot | **free-text question**, QuestionFrame, variants, reading | user + derived | one AES-GCM payload | same | 29 d 18 h | session delete; expiry cleanup |
| 7 | History policy (`history-retention-v1`) | policy activation record | system | DB row | same | profile lifetime | guest erase |
| 8 | Optional account (`account-storage-v1`; Google/email sign-in off) | Supabase subject UUID, masked email | user | DB row; identity held in Supabase Auth | Supabase (DE); Google when enabled | 365 days of inactivity | linked-account erasure (DELETING state, then provider delete) |
| 9 | Share links | encrypted snapshot, hashed capability token | user action | AES-GCM | Hetzner, Supabase | 14 days of access; then purged | revoke; cleanup |
| 10 | Experiments and resonance (`reading-resonance-v1`) | feedback, action experiment | user | AES-GCM | same | 29 d 18 h / 30 d | reset ("Tắt và xóa"); cleanup |
| 11 | Radar invite (`radar-pair-v1`) | B's own profile (through B's guest), nickname, result, receipt hash | user (B consents for B) | nickname/result AES-GCM; context/voice plaintext | same | 30 days from acceptance; receipt 30 days (D1) | A deletes; B withdraws (receipt, session or invite link, D2) |
| 12 | Radar `private_check` (`radar-authorized-input-v1`) | **B's birth date, time and place** (request memory only); A's nickname for B; result; attestation time; keyed HMAC request digests that include B's raw inputs | **A-about-B** | B's raw data not persisted; nickname/result AES-GCM; context/voice plaintext; HMAC digests | same | 24 h access; physical deletion by the 6-hourly cleanup, deferred by send fences (no hard bound) | A deletes; expiry; guest erase of A |
| 13 | Luna AI rewrite (`external-content-rewrite-v1`, opt-in) | M1 Daily payload: shared catalog wording plus closed labels; can reveal the Sun sign on a date-only reading; never raw birth data, IDs or the Tarot question | derived | encrypted rewrite queue (24 h) | **OpenAI, US** | OpenAI abuse-monitoring logs normally up to 30 days, longer when the law requires it or to protect the service or third parties from harm (canonical wording: `OPENAI_ABUSE_RETENTION_NOTICE`, data map; `store:false` is not ZDR) | consent toggle cancels queued jobs; data already sent cannot be recalled |
| 14 | Deletion journal (P07) | keyed HMAC of the root id, kind, scope, time | system | DB row and an hourly host copy (0600) | Hetzner, Supabase | 15 days | purge timer |
| 15 | Backups | everything in `public` (ciphertexts plus plaintext operational fields) | system | `pg_dump` custom format on the VPS disk; **no app-level encryption in `backup-database.sh`** | Hetzner (DE); Supabase snapshots | 14 days (app); provider snapshots unknown | age-out; journal replay on restore |
| 16 | Matching (deferred) | gender identity, intent, preference, age range, region | user (legacy rows) | encrypted display name; the rest plaintext | same | new writes return 410 (P02) | withdraw; guest erase |
| 17 | Device copies | offline mood/save/unsave intents (ids, mood) | user | localStorage | device only | 24 h / 30 days | clear device; guest erase |

Luna's state differs between code and production:

- **Code default:** off. `generation_enabled=False`, and only the surfaces `daily_home` and `tarot` are allowed.
  The Tarot payload never carries the question.
- **Production, per the runbook at 26/10:** Luna is on for `daily_home` only, as a pilot of at most 20 opted-in
  sessions for 14 days from 21/10/2026.

The team's own assessment (M1, 20/10) is that this payload cannot identify a reader. That is our assessment and has
not been confirmed by anyone outside the team.

## 3. P09: lawful basis and notice

### 3.1 Basis per purpose

| # | Purpose | Basis today | Comment against Law 91 |
|---|---|---|---|
| 2–4 | Birth profile, chart, readings | Consent `birth-profile-v1` / `-deep-v1`, stored per purpose with version and time | Matches Art. 9.3 and Decree 356 Art. 6.1–6.2 on form and record. Validity under Art. 9.2 depends on the notice gaps in 3.2. |
| 5, 6 | Daily mood, Tarot question | Covered by the basic consent and the act of submitting | Tarot questions can contain health, pregnancy, self-harm or abuse content. The code itself detects these (`tarot/voice.py` `_SENSITIVE_*`). That content plausibly falls under Decree 356 Art. 4.1(c)/(d)/(e). Art. 6.4 requires telling the person when data is sensitive, and the copy does not. |
| 7 | History policy | Recorded by the same "Đồng ý & bắt đầu" tap as #2 | It only shortens retention, so it is a retention rule rather than a separate purpose. Recording it as an acceptance in one tap with #2 reads like a bundled consent (Art. 9.4(a)–(b)). See decision 9. |
| 8 | Account | Separate first-link consent `account-storage-v1` | Separate, with its own record. |
| 10 | Resonance | Separate consent, withdrawable with deletion | Separate. |
| 11 | Radar invite | B's own consent `radar-pair-v1` | B is the data subject and consents for B. |
| **12** | **`private_check`** | **A's checkbox attestation** that B allowed the use | Art. 9.1 and 11.1 place consent with the data subject. A's statement is not B's consent, and the copy already says so ("Việc bạn đánh dấu xác nhận không thay thế sự cho phép của họ"). No provision covers user-entered third-party data, and none exempts the operator. Art. 19.1(d) covers the agreement of *the data subject*, not of A. Apple 5.1.1(viii) is a separate store risk. |
| 13 | Luna | Separate opt-in, off by default | Meets Decree 356 Art. 10.3 (disclosure plus opt-out) for AI. OpenAI is named as a US company processing outside Vietnam. |
| 14, 15 | Journal, backups | Not consent-based; they serve erasure and recovery | Should be disclosed. Backups are mentioned in "Xoá và bản sao lưu". |

### 3.2 What the notice says vs what Law 91 asks

Notice sources: `/consent` and `/privacy` (`apps/web/src/features/consent/ConsentPage.tsx`), the Radar private start
page, and the store tables in the data map.

| Requirement | Current notice | Gap |
|---|---|---|
| Data types and purpose (Art. 9.2(a)) | Birth data for the Sun sign and Lá Khai Sinh; history windows; Radar; AI; hosting | Mostly covered. Mood is mentioned only inside the history-retention paragraph ("kèm mood của ngày đó"), without its own purpose or data-type line; Tarot questions are not named as a data type. |
| **Controller (Art. 9.2(b))** | Only a contact email | **No controller named** (person or entity). Google Play also asks for the developer entity. |
| Rights and obligations (Art. 9.2(c); Decree 356 Art. 5.1) | "Xem, sửa, rút đồng ý hoặc xóa toàn bộ trong mục Mình" | **"Sửa" overclaims**: the birth date cannot be edited (only the time/place layer), see section 5. No export exists. No request procedure or response time is published. Restriction, objection and complaint are not mentioned. |
| Sensitive data flag (Decree 356 Art. 6.4) | None | Depends on decision 2. |
| Automated processing (Decree 356 Art. 10.3) | AI rewrite is explained and opt-in. The rule-based reading engine is not described as automated processing. | Add one plain paragraph on how readings are produced and that the user can stop at any time (delete or withdraw). Whether Art. 10.3 reaches a deterministic engine is an interpretation; the paragraph costs little. |
| Cross-border (no specific notice article; Art. 9.2(a) by purpose) | "dữ liệu được truyền từ Việt Nam ... Hetzner tại Đức ... Supabase tại Frankfurt"; OpenAI named in the AI section | Covered for hosting and AI. |
| Retention | 30 days / 365 days / 24 h / 30 days / 14-day backups mentioned in general terms | The physical delay (send fences, no hard bound) is not stated (P05 question). Supabase snapshot retention is unknown. |
| Age | "từ 18 tuổi"; server enforces 18+ from the declared birth date, for both the owner and B | A self-declared birth date is not age assurance. The rule is stated. |
| B (private check) | B is never contacted. A sees the attestation and "đừng nhập hộ". | B receives no notice at all (D4). Only A can pass it on. |

### 3.3 P09 D3 and D4: keep or change

Facts:

- B's raw data lives only in request memory. However, the keyed HMAC request digests are computed over B's
  date, time and place, and they are kept with the row.
- The result, labelled with A's nickname for B, is kept for 24 hours.
- B has no channel except the manual one in `radar-recipient-rights.md`.

The law gives no route by which A can consent for B. Options:

| Option | What changes | Effect |
|---|---|---|
| D3-a (current) | Keep the attestation and the 24 h result | Lowest product cost. Relies on A's statement, which the copy itself says does not replace B's permission. |
| **D3-b** | Make the invite the only path for new checks; existing private results expire within 24 h anyway | B consents for B (Art. 9). Removes the Apple 5.1.1(viii) exposure. Costs the "check kín" feature. |
| D3-c | Keep the private check but persist nothing derived from B: show the result once, drop the stored result and the B-input digests, keep only the attestation time | Shrinks storage to almost nothing, but B's data is still processed without B's consent. |

- **D4 (no automatic contact with B):** recommend **keep**. Contacting B would require collecting B's phone or
  email, which means more data about a person who has not agreed. If a private check survives (a or c), add a line
  asking A to show B the Radar section of `/privacy`.
- **R07** (manual-entry consent and Roast copy) follows whichever D3 option is chosen.

## 4. P10: cross-border transfer and impact assessments

### 4.1 Flows

| Flow | Destination | Personal data? | Art. 20 case | Exemption? |
|---|---|---|---|---|
| App traffic, processing, backups | Hetzner, Germany | yes | 20.1(c); Decree 356 Art. 17.1(a), (c) | none applies. "The person transfers their own data" (20.6(c)) does not describe an operator's hosting choice; we would not rely on it. |
| Database | Supabase, Frankfurt | yes | same | none |
| Luna `daily_home` pilot | OpenAI, US | team assessment (M1): not identifying | only if the payload is personal data (Art. 2.1) | none needed if it is truly not personal data, but the assessment is ours |
| Google/email sign-in | Supabase Auth (DE); Google when enabled | yes | 20.1(c) | none. Currently off. |

### 4.2 Is a transfer impact dossier required?

On the verified text: **yes**. Art. 20 has no small-business exemption, and none of the Art. 20.6 or Decree 356
Art. 17.3 cases fits.

Contents (Decree 356 Art. 18.2–18.3): a report on Form 09, the transfer contracts (Hetzner and Supabase DPAs), and
the privacy policies and procedures, filed with Form 01a/01b. The report covers:

- the parties and their contacts;
- the data-protection contact;
- purpose, data types and a data-flow diagram;
- consent, retention and deletion;
- security measures after transfer;
- the receiving system;
- onward transfers;
- a self-assessment of compliance;
- the recipient's protection level, risks and mitigations.

Most of the content exists in the data map and runbooks. Form 09 itself was not read here; its field layout is in
the Decree 356 annex.

Timing: within 60 days of the first transfer. The earliest production receipts in the repo are the Hetzner/Supabase
public beta of 26–27/09/2026 (`docs/plans/2026-09-26-...`, commit `527fbe5`). If real user data first reached them
then, the window would close around **25–26/11/2026**. The owner must confirm:

- the actual first date;
- whether any earlier deployment, such as the 26/09 GCP beta review, held real user data.

If so, that earlier date sets the clock.

### 4.3 Is a processing impact assessment (DPIA) required?

Art. 21 applies to controllers, including individuals. An exemption is possible only through Art. 38.2/38.3, and
that requires all of the following:

1. **The controller is a small enterprise, startup, micro-enterprise or household business.** The owner's legal
   form is not recorded anywhere in the repo. An unregistered individual operator is not in either clause.
2. **The controller does not directly process sensitive data.** As noted for purposes 5, 6 and 12, the Tarot free
   text visibly receives health and private-life content, and Radar results describe relationships. Treating these
   as non-sensitive would be a hard position to defend.
3. **The controller has fewer than 100,000 data subjects, cumulative.** The beta is far below this; no count was
   checked.

Conservative reading: **prepare and file a DPIA** on the same 60-day clock, counted from first processing.
Contents (Decree 356 Art. 19.2–19.3): a report on Form 10 with the contracts and policies, filed with Form
02a/02b. The report covers the parties, the data-protection contact, purposes, data types, the flow diagram,
consent and retention, the security design, a self-assessment, and risks with mitigations.

The DPIA and the transfer dossier overlap heavily, so one working pack can feed both.

### 4.4 Other P10 gaps

- **Cloud contracts (Decree 356 Art. 12.2).** The rule wants the contract to reference Vietnamese data-protection
  law, roles, flows, security and deletion. Standard Hetzner and Supabase DPAs are unlikely to mention Vietnamese
  law. DPA signature is tracked by the owner.
- **Encryption at rest (Art. 12.4).** App-level AES-GCM covers prose and birth data. Mood, Radar context/voice and
  matching eligibility fields are plaintext columns. Provider-level disk encryption at Supabase and on the Hetzner
  volume was not verified here. The backup dumps are written without app-level encryption.
- **Data-protection contact (Art. 33.2).** The text addresses "agencies and organisations". Both dossiers ask for a
  contact (Decree 356 Art. 18.3(b), 19.3(b)) whatever the answer.
- **Breach procedure (Law Art. 23, Decree 356 Art. 28).** No incident runbook with the 72 h notice to A05 exists.
  Only `chart-synthesis-release-runbook.md:108` points to "incident response".
- **Penalties (Decree 330/2026, in force 19/08/2026, per sub-agent reading).** It has fines for not filing either
  dossier (Art. 55–56) and for missing rights deadlines (Art. 44). Cited only to explain priority; not re-read by
  the author.

## 5. Data subject rights coverage

| Right (Law Art. 4.1; deadline Decree 356 Art. 5) | Current status | Gap / plan |
|---|---|---|
| Know (a) | `/privacy` page; store tables | Controller missing; no published procedure (3.2) |
| Withdraw consent (b), 15 days | **Basic birth:** only by deleting the profile. **Deep:** remove time/place. **AI:** toggle; queued jobs cancelled. **Resonance:** "Tắt và xóa". **Matching:** `DELETE /consent`. **Radar invite B:** receipt, session or invite link (D2). | No "withdraw basic consent but keep the account" path. That is acceptable if the notice says withdrawal means deletion. |
| View (c), 10 days | Profile, readings, history and Radar results are visible in the app | No single view of all data held |
| **Correct (c), 10 days** | Birth time/place can be edited ("Sửa lớp dữ liệu sinh"). **Birth date cannot be edited.** The only route is erasing and re-onboarding, which loses history. | Planned: US-23 birth-date edit, PR #113 (plan, open). The copy "Xem, sửa" overclaims until it ships. |
| Provide a copy (d), 10 days | **No export** | Planned: "Tải dữ liệu của tôi" export, built in parallel on another branch. Until then, manual by email within 10 days. |
| Delete (d), 20 days | In-app full erase (guest and linked account); history clear; per-item delete; Radar delete. Journal replay protects erasures across restores (P07). | Physical delay from send fences has no hard bound. Supabase snapshot retention is unknown. App backups (14 days) fall within 20 days. |
| Restrict / object (d), 15 days | No in-app path; contact email only | Needs a published manual procedure with the 2-working-day acknowledgement |
| Complain (đ) | Contact email | State the procedure |
| **B, private check** | No raw birth input and no B account are stored. What is stored is still potentially identifying derived data linked to A: A's nickname for B (which may be a real name, reversible AES-GCM), the relationship result and keyed retry digests. A can delete. Access ends after 24 h; physical deletion follows at the 6-hourly cleanup and can be deferred by send fences (no hard bound). Manual path in `radar-recipient-rights.md`. | That doc still calls the response deadline "a counsel question"; Decree 356 Art. 5 now answers it. Depends on D3. |
| B, invite | API paths released in `89ebdb0`. Session and invite-link screens #83 are on integration, not released. | Planned: further P09 D2 web screens on parallel branches; release pending |

Operational gap: every manual right is served by one person through one mailbox. The 2-working-day
acknowledgement and the 10/15/20-day deadlines need a dated log (no content, as `radar-recipient-rights.md`
already prescribes).

## 6. Decisions for the owner to confirm

Each item gives a recommended option. Nothing below has been implemented.

1. **Controller identity and legal form.** Record who the controller is (individual, household business or
   enterprise) and how `/privacy` names it.
   *Recommend:* name the controller in the notice (a trading name is acceptable if it is the registered or real
   operator) and record the legal form here. This also settles whether Art. 38 can apply at all.
2. **Sensitive-data classification.** Decide how to treat Tarot free-text questions, mood, and Radar relationship
   results.
   *Recommend:* treat them as possibly sensitive (Decree 356 Art. 4.1(c)/(d)), add the Art. 6.4 sentence to the
   consent copy, and do not rely on the Art. 38 exemption.
3. **Cross-border dossier (Art. 20; Form 09 + 01a/01b).**
   *Recommend:* prepare it from the data map and file it before the 60-day window closes (around 25–26/11/2026 if
   the first transfer was 26–27/09). Confirm the first date first.
4. **DPIA (Art. 21; Form 10 + 02a/02b).**
   *Recommend:* prepare it together with item 3 and file it on the same clock, unless items 1 and 2 clearly make
   the exemption available.
5. **Luna/OpenAI.**
   *Recommend:* let the `daily_home` pilot end on its scheduled date (14 days from 21/10). List OpenAI in the
   transfer dossier, or record the M1 "not personal data" assessment in it, before any new pilot.
6. **P09 D3 (private check).**
   *Recommend:* D3-b, invite-only for new checks. If the owner keeps "check kín" for product reasons, then D3-c:
   persist nothing derived from B. Record the reason either way.
7. **P09 D4 (no automatic contact).**
   *Recommend:* keep it. If a private check remains, ask A to show B the Radar section of `/privacy`.
8. **Notice rewrite (one pass).** Add:
   - the controller;
   - the rights list with the procedure and response times;
   - accurate "sửa" wording until US-23 ships;
   - a clearer purpose and data-type line for mood (already mentioned in the retention paragraph) and Tarot questions as a data type;
   - the sensitive flag (item 2);
   - an automated-processing paragraph;
   - the possible delay of physical deletion.

   *Recommend:* bump `birth-profile-v1` to `-v2` and re-show the consent once, because existing consents were given
   without a named controller (Art. 9.2(b)).
9. **History policy bundled with basic consent.**
   *Recommend:* present `history-retention-v1` as a disclosed retention rule that applies to everyone, not an
   acceptance in the same tap. Keep the activation record for audit.
10. **Rights procedure.**
    *Recommend:* adopt the Decree 356 Art. 5 deadlines in one short procedure (general requests plus
    `radar-recipient-rights.md`), with a content-free request log. Ship the export and the birth-date edit as
    planned.
11. **Cloud contracts and encryption.**
    *Recommend:* file the existing Hetzner/Supabase DPAs with the dossier and record the gap against Decree 356
    Art. 12.2. The operator should confirm provider-level disk encryption and Supabase snapshot retention, and
    decide whether to encrypt backup dumps.
12. **Breach procedure and data-protection contact.**
    *Recommend:* write a one-page incident runbook (72 h notice to A05 using the Decree 356 Art. 28 content) and
    name the owner as the data-protection contact in both dossiers.

## 7. Sources (all accessed 29/10/2026)

Official, Vietnam:

- Law 91/2025/QH15, Official Gazette entry and attachments:
  https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm (full text read from the linked .doc; the
  linked PDF failed TLS verification from this machine)
- Law 91/2025/QH15, government legal documents index: https://vanban.chinhphu.vn/?pageid=27160&docid=214590&classid=1&typegroupid=3
- Decree 356/2025/NĐ-CP, Official Gazette entry: https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-356-2025-nd-cp-468371.htm
  (full text read from the linked .docx)
- Decree 356/2025/NĐ-CP index (issue date 31/12/2025, effective 01/01/2026, signed PDF):
  https://vanban.chinhphu.vn/?pageid=27160&docid=216387 and https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf
- Decree 330/2026/NĐ-CP (penalties; signed scan, read by a sub-agent only):
  https://xdcs.cdnchinhphu.vn/446259493575335936/2026/8/24/330-2026-nd-cp-19082026-signed-17875667982992022144692.pdf
- vbpl.moj.gov.vn did not resolve from this machine and was not used. No article number here comes from a
  secondary site.

Platform:

- Apple App Store Review Guidelines (5.1.1, 5.1.2): https://developer.apple.com/app-store/review/guidelines/
- Google Play User Data policy: https://support.google.com/googleplay/android-developer/answer/10144311

Repo:

- `docs/reviews/2026-10-22-audit-v2-registry.md` (P09, P10, R07, D1–D4)
- `docs/legal/store-privacy-data-map.md`, `docs/legal/2026-10-22-privacy-counsel-dossier.md`
- `docs/operations/radar-recipient-rights.md`, `docs/operations/backup-restore-and-deletion-reconciliation.md`,
  `docs/operations/hetzner-supabase-release-runbook.md`
- Code: `apps/web/src/features/consent/ConsentPage.tsx`, `apps/web/src/features/radar/RadarPrivateStartPage.tsx`,
  `apps/web/src/features/profile/ProfilePage.tsx`, `apps/api/app/domains/radar/service.py`,
  `apps/api/app/domains/birth/service.py`, `apps/api/app/domains/tarot/voice.py`, `apps/api/app/config.py`,
  `infra/hetzner/backup-database.sh`

Not verified:

- Form 01a/01b, 02a/02b, 09 and 10 layouts (annex not read).
- Decree 330 general articles and transition provisions.
- The live production flags and row counts.
- Provider-level encryption and snapshot retention.
- Whether any pre-26/09 deployment held real user data.
- Whether an amending decree after 31/12/2025 changes the articles above. None was found, but no systematic
  search of the gazette was made.
