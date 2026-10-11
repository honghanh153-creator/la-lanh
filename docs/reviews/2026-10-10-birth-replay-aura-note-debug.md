# Birth replay, Aura label and stale Daily reading

Date: 2026-10-10, Asia/Ho_Chi_Minh. Local patch applied; public beta unchanged.
Branch: `feat/luna-content-rewrite-runtime`; pre-fix HEAD:
`99a3079a383a4cb529c1331a596bc47f75b5f07f`.

## Report versus evidence

The user reports an incorrect Sâu/Mộng label and a repeated Note. This is a bug report,
not a request for new concepts or a request to force an Aura label.
The exact expected label and the original beta input have not been independently verified.
Identical prose alone is not evidence that one account retrieved another account's records.

Three defects were reproduced using synthetic data and the real calculation engine:

1. A → B → A submission acknowledged the replayed snapshot A, while `find_current`
   remained B. The standalone reproduction returned submitted Sun Pisces, current Sun
   Scorpio, label Sâu, and different submitted/current snapshot IDs.
2. A → B switched Daily metadata but left the active reading projection on A, because
   the reading scope is stable for a profile/day and normally requires explicit cutover.
   Changing the birth date was incorrectly treated like an optional copy update.
3. After A → B → A → full chart A, removing precision selected the most recently created
   date-only snapshot B rather than the date-only snapshot for the current birth date A.

The replay early return is also present in committed HEAD. The dirty worktree was not stashed
or reset: that would disrupt unrelated work and the live review environment.

## Root repair

- `BirthChartService.create_date_only` routes a cached calculation through the same atomic
  repository write as a new calculation. A cached computation is not a completed activation.
- `PostgresBirthRepository.save_or_replay` holds the guest lock and compares decrypted dates
  only within that guest's scope. Same-date retries retain the current full chart and revision;
  a different date activates the requested date-only snapshot and clears prior supplement
  metadata. A new supplement must be explicitly provided for that date.
- Different-date activation detaches active/available reading pointers and Aura acknowledgments
  for this guest/profile. It does not delete immutable reading history, saved notes, shared
  artifacts or other guests' records. Same-date precision upgrades keep the existing explicit
  Aura/copy cutover contract.
- Precision erasure selects the date-only snapshot matching the current encrypted birth date.
  It cannot choose an unrelated date simply because it was created more recently.
- `_reveal` carries the repository profile revision. Existing stale-supplement fences remain
  intact; the patch does not bypass withdrawal or profile-change checks.
- The in-memory test repository models replay activation instead of masking the state change.

No Aura scoring weights, content matrix, rewrite prompts, public API schema, paid generation
configuration or deployment configuration were changed by this patch.

## Verification ledger

| Check | Result |
|---|---|
| Standalone A → B → A reproduction before patch | Failed: current Scorpio / submitted Pisces / Sâu |
| Same reproduction after patch | Passed: current Pisces / submitted Pisces / Mộng / same snapshot |
| New integrated regression cases before patch | Failed on replay/current mismatch and stale reading source |
| Birth suite after patch | 19 passed |
| Birth / Daily / Readings / Guest, excluding the legacy setup test below | 296 passed, 1 explicitly deselected |
| Full API suite | 1,048 passed, 1 failed, 23 skipped |
| Scoped Ruff lint | Passed |
| Scoped Ruff formatting | Applied only to fix-owned additions; re-check required at final handoff |
| Mypy, two production files | Passed |
| Diff whitespace | Passed |
| Local runtime | Backend 8030 reloaded in place; frontend 5310 and existing QA database retained |
| Browser after backend reload | Existing private profile loaded; no deletion/restart of the user's session |

New cases exercise date-only and full-chart A → B → A, the active revision's actual source
snapshot, precision withdrawal after replay, same-date retry without recomputation or loss
of the complete chart, and two independent guests whose readings remain isolated.
Generation and worker are explicitly disabled in local QA. No paid API call was made.

## Remaining test setup / release block

`tests/readings/test_api.py::test_precision_erasure_removes_derived_reading_even_without_retained_natal`
previously prepared legacy inconsistent state by changing the birth date through the API while
keeping the previous date's supplement. The repaired API correctly clears that supplement,
so the test now receives 409 for a deep reading rather than 200. Do not restore the defective
product behavior to make the fixture pass, delete the test, or weaken its erasure assertions.
The intended follow-up is to construct the legacy state directly inside the test, retain its
derived-reading deletion checks, and rerun the full suite. Permission to edit this overlapping
dirty test was requested; no edit was made while its response was pending.

The 23 skipped tests need isolated localhost PostgreSQL. SQLite integration does not prove
PostgreSQL locking under concurrent deployment traffic. No database repair or beta incident
forensics was performed on real users. The precise user's expected Aura label remains to be
compared against the original input rather than inferred from the synthetic fixture.
These limits block claiming a complete public-beta repair.

## Quality and privacy gates

Docs/product: changing a date is distinct from improving precision for the same date; same-date
retry cannot silently downgrade a complete chart. Ordinary precision updates retain explicit
cutover. The full state sequence, not just individual HTTP 200 responses, is the acceptance gate.

Security: all new persistence lookups/updates stay owner/profile scoped and use the existing
transaction/guest lock. Tested that A's replay and projection detachment cannot alter B.
Withdrawal and source-revision checks were retained. No credentials, ciphertext contents,
real birth inputs, tokens or session cookies were added to logs or this report.

Data privacy: no new collection, third-party transfer or provider request; encrypted dates are
compared in memory only. Current precision metadata cannot be reused for a different date.
Immutable history is not an active reading and is not purged by an ordinary edit.

Primary sources checked:
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Web Cache Security](https://cheatsheetseries.owasp.org/cheatsheets/Web_Cache_Security_Cheat_Sheet.html)
- [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [Vietnam Personal Data Protection Law 91/2025/QH15, official record](https://vanban.chinhphu.vn/?docid=214590&pageid=27160)

These sources inform scope and minimization checks; they are not a certification of legal compliance.

## Post-Fix Quality

Scope: fix-owned hunks only; pre-existing dirty edits preserved.
Simplify: skipped for overlapping pre-existing edits.
Review: targeted manual comparison with pre-fix copies, not the unrelated branch diff.
Residuals: legacy test setup awaiting permission; real PostgreSQL concurrency and beta verification
not run; original expected Aura not established.
Re-verification: birth and the targeted non-legacy suites passed after the erasure fix.
No commit, push or deployment was performed or authorized by this handoff.

Prevention: future releases must verify A → B → A across submitted/current snapshots, active Note
source, same-date precision retention, and precision withdrawal; a successful replay HTTP response
without correct active state is a failed acceptance test.
