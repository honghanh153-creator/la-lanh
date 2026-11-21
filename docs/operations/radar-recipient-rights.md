# Radar: B's rights without a receipt (P09 D2)

Operational procedure for a request from B, the other person in a Radar result. It applies the owner's
plan for P09 D2: verify possession of the invite link or receipt, or let A delete, and never collect B's
birth data again. **Counsel has not yet confirmed that this is enough (dossier P09 D2), and the response
deadline under Decree 356/2025 is a counsel question.** This document claims neither.

## What B can do alone

| B's situation | Path | What it opens |
|---|---|---|
| Has the receipt cookie (device that accepted) | `/radar/receipt` | view, withdraw |
| Lost the receipt, still has the guest session that accepted | `GET /v1/radar/received` (pages via `before`/`next_before`), `GET /v1/radar/received/{id}`, `POST /v1/radar/received/{id}/withdraw` | view, withdraw |
| Lost receipt and session, still has the invite link | `POST /v1/public/radar/invite/withdraw` with `{token}` in the body (no request id: B on a new device cannot learn it) | withdraw only |
| Deleted B's own profile | birth-profile erase already deletes rows where B is recipient | nothing left |

All paths end with the result's 30-day access window; physical deletion of the row follows the same
cleanup job and fence rules as above. Withdrawal clears the result for both people, cancels
both rewrite jobs and waits for any in-flight provider send. Web screens: `/radar/received` and
`/radar/received/:id` (session path) and the used-invite page `/radar/i/:token` (withdraw only) were
built in #83; Mình links B to `/radar/received`, which explains what is held about B (2026-10-29).
Their copy still needs owner approval.

## Manual requests (email or support channel)

1. **Never ask for B's birth date, time or place**, and never ask for a screenshot of the result.
2. Invite (consented) result: ask B to open the invite link on any device and use the withdraw path, or
   to use the device that accepted. Support staff must not handle the token: do not ask B to paste the
   link into email or chat.
3. Private check (A entered B's data): the system stores no identifier for B, only A's nickname for B
   and a derived result. Tell B what is true, without promising erasure by a date (Radar spec §6):
   - **Access ends at the stored expiry.** New checks: 24 hours after creation. Checks created before
     the 24-hour rule (2026-10-19) keep the expiry they were created with, at most 30 days. Expired
     rows are hidden at once.
   - **Physical deletion follows later** by the six-hour cleanup job, nominally within about 30 hours
     of creation for a new check. Each run that meets an active rewrite send fence or generation
     attempt for A defers it by one more run, with no hard upper bound. Backups expire separately (P07).
   - A can delete the result at any time. Do not search for B by name.
4. Log only: request date, channel, which path was suggested, outcome. No name, nickname, email body,
   token, link or birth data in the log.
5. Questions about lawful basis or notice to B (D3/D4) go to counsel; do not answer them ad hoc.

## Not covered

- Data export exists since 2026-10-29 (`POST /v1/session/data-export`, Mình > "Tải dữ liệu của tôi").
  B's file lists B's received results (context, B's consent version, accepted, expiry) and B's own
  profile, never the nickname A chose for B or the result prose; A's file lists only A's side. See
  [the plan](../plans/2026-10-29-privacy-export-and-b-rights.md). A request by email for a copy is
  answered by pointing to that button; support never builds an export by hand.
- Backups keep deleted rows until they age out (P07); a restore must replay the erasure journal.

## Lời mời một ô (AL1, 20.11.2026, mặc định tắt)

Khi `radar_invite_first_consent` bật và owner đã duyệt các câu `privacy.radar.invite-first.*`, B có thể chỉ nhập ngày sinh của mình trên trang lời mời, không cần phiên khách hay hồ sơ. Ngày sinh chỉ ở bộ nhớ một lần tính và không được lưu; hàng `radar_requests` có `recipient_guest_id = null`. Quyền của B: xem và rút bằng receipt HttpOnly trên thiết bị đã đồng ý (30 ngày), hoặc rút bằng link mời (`POST /v1/public/radar/invite/withdraw`). Không có đường "Kết quả bạn đã nhận" theo phiên cho trường hợp này vì B không có phiên.


## "Hai bạn tuần này" do B tự giữ (owner AR1, 21.11.2026)

Trên trang lời mời một ô có một ô riêng, mặc định không tick, chỉ B tick được ("Giữ ngày sinh của tôi, đã mã hoá, tối đa 90 ngày để hai bạn xem phần mỗi tuần. Tôi xoá được bất cứ lúc nào."). Không tick thì không lưu gì. Khi B đã tick:

- Lá giữ ngày sinh của B (chỉ ngày, mã hoá AES-GCM) và tên gọi A đặt (mã hoá), tối đa 90 ngày; A chỉ thấy chữ cái đầu và thẻ tuần, không thấy ngày.
- B xoá bằng cách rút kết quả (biên nhận, phiên hoặc link) trong 30 ngày đầu; sau đó, hoặc khi A đã xoá kết quả, **mở lại link mời và bấm "Rút chart khỏi kết quả"** vẫn xoá được cặp cho tới hết 90 ngày.
- B mất link và không còn biên nhận: hỗ trợ không tra được cặp theo ngày sinh (không có chỉ mục theo ngày). Cách xử lý: nhờ A tắt cặp trên Hôm nay, hoặc chờ cặp tự hết hạn; hàng hết hạn bị xoá hẳn mỗi giờ.
