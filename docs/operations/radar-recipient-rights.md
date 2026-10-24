# Radar: B's rights without a receipt (P09 D2)

Operational procedure for a request from B, the other person in a Radar result. It applies the owner's
plan for P09 D2: verify possession of the invite link or receipt, or let A delete, and never collect B's
birth data again. **Counsel has not yet confirmed that this is enough (dossier P09 D2), and the response
deadline under Decree 356/2025 is a counsel question.** This document claims neither.

## What B can do alone

| B's situation | Path | What it opens |
|---|---|---|
| Has the receipt cookie (device that accepted) | `/radar/receipt` | view, withdraw |
| Lost the receipt, still has the guest session that accepted | `GET /v1/radar/received`, `GET /v1/radar/received/{id}`, `POST /v1/radar/received/{id}/withdraw` | view, withdraw |
| Lost receipt and session, still has the invite link | `POST /v1/public/radar/invite/withdraw` with `{token}` in the body (no request id: B on a new device cannot learn it) | withdraw only |
| Deleted B's own profile | birth-profile erase already deletes rows where B is recipient | nothing left |

All paths end with the result's 30-day window. Withdrawal clears the result for both people, cancels
both rewrite jobs and waits for any in-flight provider send. The web screens for the session and
invite-link paths need owner-approved copy and are not built yet.

## Manual requests (email or support channel)

1. **Never ask for B's birth date, time or place**, and never ask for a screenshot of the result.
2. Invite (consented) result: ask B to open the invite link on any device and use the withdraw path, or
   to use the device that accepted. Support staff must not handle the token: do not ask B to paste the
   link into email or chat.
3. Private check (A entered B's data): the system stores no identifier for B, only A's nickname for B
   and a derived result that expires 24 hours after creation. Tell B that the result is deleted
   automatically within 24 hours and that A can delete it at any time. Do not search for B by name.
4. Log only: request date, channel, which path was suggested, outcome. No name, nickname, email body,
   token, link or birth data in the log.
5. Questions about lawful basis or notice to B (D3/D4) go to counsel; do not answer them ad hoc.

## Not covered

- A data export (portability) endpoint does not exist for anyone yet; B's "export" today is the view.
- Backups keep deleted rows until they age out (P07); a restore must replay the erasure journal.
