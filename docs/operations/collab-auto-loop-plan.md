# Bản thiết kế: vòng tự động Claude ⇄ Codex

Trạng thái: **ĐÃ CHỐT với owner ngày 30.10.2026.** Code xây theo đúng bản này; đổi thiết kế thì sửa file này qua PR trước.

## 1. Mục tiêu và thước đo

| Thước đo | Hiện tại (11–30/10) | Mục tiêu sau 1 tuần |
|---|---|---|
| Thời gian một vòng review | ≤ vài giờ (chờ owner chuyển lời) | ≤ 15 phút |
| Mở PR → merge integration (trung vị) | 22 giờ | ≤ 2 giờ |
| PR có ≥ 3 vòng verdict | 32 / 106 | ≤ 10% |
| Owner phải chuyển lời giữa hai agent | mỗi vòng | 0 (từ 16.11.2026 plan tự chạy khi đăng, owner chỉ `Giữ` khi muốn dừng; buổi review sâu mỗi đợt) |
| PR chỉ để ghi registry | ~10 | 0 |

Ngoài phạm vi: merge vào `main`, release, deploy, server/DB thật, provider, IAM, secret, budget. Những việc này giữ nguyên quyền owner.

## 2. Quyết định owner đã chốt (30.10.2026)

1. Claude gọi Codex trực tiếp để review; lịch mỗi giờ là lưới an toàn.
2. Merge tự động vào `collab/integration` khi đủ điều kiện ở mục 4.2, **bắt buộc có `Author check: PASS @ <SHA>`**.
3. Chính sách P2: P2 về **privacy, bảo mật, lời văn gửi người dùng** chặn merge; P2 khác được APPROVE kèm issue sửa tiếp (fix-forward); P3 không chặn; P0/P1 luôn chặn.
4. **Lịch ngày:** 9h owner xem plan trong ngày. Owner duyệt thì chạy ngay; 10h chưa có trả lời thì tự chạy; chạy đến 24h. *Đổi 14.11.2026:* plan 06:50, 08:00 tự chạy, không bắt đầu lượt mới từ 23:35, dừng 23:59 (§3.1). *Đổi 16.11.2026 (owner, gói 5 sửa luồng mục 2):* plan chạy ngay khi đăng lúc 06:50, không còn khung chờ owner; owner trả lời `Giữ` bất cứ lúc nào để dừng, `Duyệt` để chạy lại.
5. **Model Codex:** `gpt-6.1-sol`, mức suy nghĩ `high`. Hết hạn mức thì chờ reset và chạy tiếp nếu còn lượt trong ngày.
6. **Ngừng PR registry**, thay bằng `collab-turn --report`.
7. **Thứ tự ưu tiên công việc:** xong **toàn bộ content** → **data privacy** → **tính năng mới**. Không giữ PR theo kích thước; xếp theo thứ tự này. PR quy trình (`area:ops`: vòng tự động, CI, test) đi trước cả ba nhóm (owner giao Claude tự chọn, 30.10.2026).

**Owner không còn là bước duyệt bắt buộc** (owner 15.11.2026, khoảng 17:00–18:00; ghi ở hub #2). Owner nói: "do tôi không muốn luồng bị stuck ở chỗ tôi" và "tôi sẽ đi kiểm soát QA random, chứ không phải là 1 bước bắt buộc (trừ các action chi phí ...)". Owner xác nhận: "claude làm, claude và codex phản biện, codex duyệt". Khi được hỏi kế hoạch và thời điểm áp dụng, owner trả lời "Giao và bắt đầu".
   - **Cách chạy:** Claude làm, Claude và Codex phản biện nhau, Codex duyệt. Máy merge vào `collab/integration` qua **đúng cổng hiện có** (mục 4.2): `Author check: PASS` và `Review verdict: APPROVE` có biên nhận, cả hai đúng head. Cổng này không đổi. Bất đồng vẫn theo luật L25.
   - **`needs-owner` chỉ còn cho 4 loại việc:**
     1. việc tốn chi phí, dịch vụ mới hoặc quyền truy cập mới;
     2. phát hành cho người dùng thật;
     3. chữ về quyền riêng tư, sự đồng ý, khủng hoảng, an toàn; phần chữ này chặn lúc phát hành, không chặn merge;
     4. bật một tính năng thu thêm dữ liệu cá nhân.
   - **Bài đầu mỗi khóa Học và danh sách lằn ranh đỏ:** giao Codex duyệt; owner xem ngẫu nhiên.
   - **Ràng buộc Codex đặt ra khi phản biện kế hoạch (15.11):**
     - gỡ nhãn `needs-owner` từng PR một, mỗi PR một dòng lý do, không gỡ hàng loạt;
     - chữ đang chờ duyệt chỉ được merge khi app vẫn dùng câu đã duyệt;
     - tính năng thu dữ liệu mới phải tắt cả đường thu lẫn đường lưu, không chỉ ẩn trên giao diện.
   - **Trước khi gỡ nhãn ở PR nào**, phải có một bài kiểm bằng máy chạy xuyên suốt:
     - PR không có nhãn nhưng còn chữ chờ duyệt hoặc tính năng đang tắt: app vẫn dùng bản cũ và không thu thêm dữ liệu;
     - head bị đổi hoặc có APPROVE giả: `collab-merge` từ chối.
   - **Báo cáo:**
     - báo cáo 07:00 có ảnh 360 và 390 px, dạng HTML trên máy owner, kèm commit;
     - bỏ báo cáo cuối tuần;
     - việc có đụng tính năng app: cuối ngày chạy 200 người giả chọn ngẫu nhiên trong 1000, giữ cố định hai bản code, cùng hồ sơ và cùng cách chấm. Lỗi an toàn hoặc lộ dữ liệu thì báo ngay.

8. **Checklist quyết định** (owner yêu cầu 31.10.2026): việc nào agent tự quyết, việc nào hỏi owner, tiêu chí và input cần có ở `docs/operations/decision-checklist.md`.
9. **Bảng trạng thái** (owner yêu cầu 31.10.2026): mỗi tick sửa tại chỗ một comment "Trạng thái vòng tự động" trên issue plan, ghi đang chạy gì, giờ cập nhật, lý do dừng, hàng đợi và việc chờ owner. Giờ cập nhật cũ hơn 20 phút trong giờ chạy nghĩa là Mac ngủ/tắt hoặc vòng bị kẹt.
10. **Báo owner bằng comment mới** (owner 12.11.2026). Sửa bảng trạng thái không gửi thông báo, nên tick đăng comment MỚI trên issue plan chỉ khi: có PR merge vào integration (mỗi PR một dòng, gộp theo tick), vòng lỗi 2 tick liền, một PR mới cần owner (`needs-owner`), và (tới 16.11.2026) bản tóm tắt khoảng 14:00 và 22:00. **Từ 16.11.2026 (owner, gói 5 mục 4) tick không đăng bản tóm tắt nữa:** báo cáo 07:00 là bản chính, báo cáo owner lúc 14:00 và 22:00 (tác vụ hẹn giờ, đọc bản chụp của khung giờ) là bản tóm tắt duy nhất của khung đó; số đo kết quả vẫn ở bảng trạng thái. Từ 14.11.2026 (L11) phần "xong" đếm **việc đạt đủ tiêu chí**, không đếm PR. Mỗi việc là một issue task, gắn qua dòng `Việc: #N` trong PR. Tiêu chí lấy từ mục "Tiêu chí đạt" của issue. Việc tính đạt khi mọi tiêu chí đều được các PR đã merge với Codex APPROVE nhận (dòng `Tiêu chí đạt:`), và tính vào đúng ngày đạt. Hai tiêu chí cùng mã (một dòng ghi `TC2`, dòng thứ hai không ghi mã cũng thành TC2) làm việc đó "chưa đo được", không bao giờ tính đạt. Lịch sử PR của một việc đọc chạm giới hạn 50 PR thì cả bản tóm tắt ghi "chưa đo được". Danh sách việc chốt lúc lập plan. PR chưa gắn việc ghi riêng và không tính. Số PR đã gộp ghi trên dòng riêng. Từ 14.11.2026 (L19), mọi con số trong bản tóm tắt, báo cáo 08/14/22 và retro lấy từ **một bản chụp nguồn cho mỗi khung giờ** (`node scripts/collab-snapshot.mjs --slot 08|14|22|retro`; wrapper có bước `ops-run.sh snapshot <khung>` để tác vụ báo cáo owner và retro gọi, **đã nối** từ 15.11.2026: cả hai prompt tác vụ (nằm ngoài repo) gọi bước này, tick kiểm việc đó (#552). L19 đóng ngày 16.11 (#572) với hai biên nhận: báo cáo 14:00 ngày 15.11 (snapshot `336e56277e1e`) và retro ngày 15.11 (snapshot `4ee95dcdc33b`); file `~/.cache/la-lanh-collab/snapshots/<ngày>-<khung>.json`, chỉ ghi một lần). Dòng cuối của khối số ghi mã `snapshot`. Nguồn nào đọc lỗi thì ghi "chưa đo được", không ghi 0. Bảng trạng thái liệt kê các issue `ops-alert` đang mở, đọc từ GitHub, nên một tick sạch không làm sự cố biến mất. Sự cố chỉ hết khi issue được đóng có bằng chứng phục hồi. Mỗi sự kiện có khoá trong marker agent `owner-note keys=…` và trong `~/.cache/la-lanh-collab/owner-notes.json`, nên chạy lại tick không đăng trùng. Lưu ý: comment do chính tài khoản owner đăng (tài khoản dùng chung với agent) chỉ gửi email khi owner bật mục "Your own updates" (Settings → Notifications → email) trên GitHub.
11. **Số đo** (owner 12.11.2026, `scripts/collab-metrics.mjs`): bộ Daily phục vụ được / tổng bộ và câu đã duyệt / tổng câu (đọc `copy_registry.json` ở integration, cùng luật `copy_approval.py`), số commit ở integration chưa lên main và số ngày từ commit cuối của main (`git`), trung vị giờ từ mở PR tới merge vào integration trong 7 ngày (`gh`), và WIP 1 + 1. Hiện trên bảng trạng thái và trong bản tóm tắt; nguồn nào không đọc được thì ghi "chưa đo được (lý do)", không ước lượng.

## 3. Luồng chuẩn

```
Claude xong việc trên branch, push (hook trước push: quét dữ liệu riêng tư + ruff/mypy) → CI pr-check chạy trên đúng head
  → tick: node scripts/collab-check.mjs --pr N đọc kết quả job `check` của pr-check ở head đó → "Author check: PASS @ SHA"
  → mở PR (nếu chưa có), gắn nhãn area:content | area:privacy | area:feature | area:ops
  → node scripts/codex-review.mjs --pr N        (Claude chờ, cùng session)
      ├─ APPROVE @ SHA   → node scripts/collab-merge.mjs --pr N → merge integration
      └─ REQUEST_CHANGES → Claude sửa → author check → push → review lại (chỉ phần đổi)
           vòng thứ 2 trở đi: vẫn về Claude sửa và Codex review lại, không gắn needs-owner (owner 16.11.2026)
```

### 3.1 Lịch ngày (giờ Việt Nam)

Owner đổi giờ ngày 14.11.2026: bắt đầu chạy PR lúc 08:00 thay 10:00, kết thúc 23:59; các bước khác dời sớm theo. Giờ nằm ở một chỗ: `planOpensAt`, `autoStartAt`, `lastStartAt`, `cutoffAt` trong `scripts/collab-trust.mjs`. Từ 16.11.2026 `autoStartAt = planOpensAt` (plan chạy ngay khi đăng); lô duyệt câu chữ hằng ngày giữ giờ riêng 08:00 (`copyBatchAt`).

| Giờ | Việc |
|---|---|
| 05:40 | Tác vụ Claude `la-lanh-morning-prep` chuẩn bị 3–5 việc trong ngày |
| 06:50 | `collab-plan.mjs --make`: lập plan trong ngày, đăng lên issue "Kế hoạch chạy tự động hằng ngày", báo thông báo macOS |
| 06:50 | Plan đăng và chạy ngay (từ 16.11.2026). Mỗi 10 phút tick đọc trả lời của owner: `Giữ` dừng, `Bỏ #N` bỏ việc, `Duyệt` chạy lại, bất cứ lúc nào |
| 08:00 | Lô duyệt câu chữ hằng ngày của Codex (`copyBatchAt`), tách khỏi giờ chạy plan |
| Từ lúc bắt đầu → 23:35 | launchd tick mỗi 10 phút; mỗi tick làm việc khi máy rảnh (merge, author check, Codex review), không còn giới hạn một lần mỗi giờ (retro D1, 31.10.2026). Claude autopilot chạy mỗi giờ (phút :37, từ 7 đến 23 giờ) |
| 23:59 | Cắt mọi lượt đang chạy dở; không bắt đầu lượt mới từ 23:35 (24 phút để lượt cuối kịp đăng kết quả) |
| 00:00–06:50 | Không chạy tự động |

Trả lời của owner trên issue plan (comment mới hơn plan của ngày đó):
- `Duyệt` — chạy ngay.
- `Giữ` — hôm nay không chạy tự động (session owner tự mở vẫn chạy bình thường).
- `Bỏ #N` — bỏ PR N khỏi plan hôm nay (có thể nhiều dòng).

Session mà owner đang trực tiếp trò chuyện không bị lịch này chặn; lịch chỉ áp cho lượt tự động.

### 3.2 Cách làm hằng ngày (owner chốt 31.10.2026)

1. **Việc nặng nối tiếp, việc nhẹ song song.** Việc nặng là `pnpm check`, cài đặt hoặc build trong clone. Mỗi lúc chỉ một việc nặng trên cả máy (`check.lock`, từ chối khi máy đang có check). Trong lúc việc nặng chạy, Claude làm việc nhẹ của nhóm ưu tiên đang mở: sửa fix-forward, viết code, viết test, viết docs. Claude không ngồi chờ.
2. **Việc nặng đi qua vòng tự động.** Author check, review và merge chạy qua tick hoặc qua `collab-check` → `codex-review` → `collab-merge`. Không session nào tự chạy `pnpm check` bằng script riêng; `checkshas.sh` đã thay (§7.1).
3. **Fix-forward là việc kế tiếp.** Issue `fix-forward` mới thuộc cùng nhóm với PR gốc và được làm ngay trong ngày, qua PR riêng.
4. **Đầu ngày.** Mac phải thức trước 05:40, lúc tác vụ chuẩn bị buổi sáng chạy. Plan đăng 06:50 và chạy ngay (từ 16.11.2026).
   - Nếu Mac ngủ ban đêm, owner chạy một lần `sudo pmset repeat wakeorpoweron MTWRFSU 05:30:00`. Lệnh này thay giờ thức 08:45 cũ; agent không tự đổi thiết lập hệ thống.
   - Ngày 14.11 kiểm tra thấy máy không có lịch thức lặp lại, nhưng tick vẫn chạy suốt đêm 13–14.11. Máy hiện không ngủ, nên chưa cần lệnh này. Claude đọc `collab-turn --report`, dừng lượt autopilot còn treo từ hôm trước và kiểm tra plan #133 đã được đăng.
5. **Trong ngày.** Một quyết định mới của owner được ghi ngay vào file này hoặc vào issue hub #2, để mọi session đều đọc được (bài học từ #136).
6. **Cuối ngày.** Claude nhìn lại quy trình trong ngày, viết report ở `docs/reviews/YYYY-MM-DD-collab-loop-retro.md` (số liệu, chỗ kẹt, đã sửa, đề xuất) và mở PR `area:ops` để Codex review qua vòng tự động.

7. **Bổ sung plan khi còn chỗ** (owner 31.10.2026; WIP 1 + 1 từ 12.11.2026). **Từ 16.11.2026 (owner, gói 5 mục 5): hai làn chạy song song.** Làn kế hoạch 7 tuần gồm PR có nhãn `ke-hoach-7-tuan` và PR của việc 7 tuần đã chọn hôm nay; mọi PR khác thuộc làn quy trình. Mỗi làn có WIP 1 + 1 riêng và tự bổ sung việc; làn quy trình bận không chặn làn 7 tuần. `claude-queue.json` ghi `topUpLanes` (làn được mở việc mới, làn 7 tuần trước) và `lanes`. Hàng chờ Codex và merge dùng chung, theo thứ tự: sự cố, rồi việc 7 tuần, rồi phần còn lại (#544). Từ 17.11.2026 (#633), PR đã tới lượt merge được merge ngay, bất kể nhóm (content, privacy, feature). Check và review vẫn theo thứ tự nhóm. Việc quy trình không bị giới hạn một việc mỗi ngày. Câu cũ, giữ để tra: Tick đếm PR mở của agent (nhánh `agent/*` vào integration, không tính `needs-owner`): PR đang tới lượt máy (check, review, merge) là "đang review", PR còn lại là "đang làm". Tick chỉ ghi `topUp: true` (`topUpCount` luôn là 1) khi không có việc nào đang làm, tối đa 1 PR đang review và chưa tới 23:35 (giờ chạy từ 14.11.2026). Claude lấy việc kế tiếp theo thứ tự ưu tiên: issue task mở có nhãn `area:*` và không `needs-owner` trước, rồi việc `auto: yes` trong backlog. Mỗi việc đi qua checklist quyết định (Q1–Q5). Claude đăng một comment "Bổ sung plan HH:MM" trên issue plan (mang marker agent, không dùng cú pháp trả lời của owner), ghi việc gì, nguồn / AC, dòng "Người dùng thấy gì", và mở PR để máy chạy tiếp. Việc cần owner (copy mới, dữ liệu cá nhân, hướng sản phẩm) vẫn mở PR nhưng gắn `needs-owner`.

### 3.3 Plan trong ngày gồm

- Hàng đợi PR theo thứ tự ưu tiên: quy trình/ops (sửa vòng tự động, CI, test) → content → privacy → tính năng mới (owner giao Claude tự tối ưu, 30.10.2026); trong cùng nhóm, PR cũ trước.
- Lượt dự kiến cho từng PR (Claude check / Codex review / Claude sửa / merge / giữ).
- Việc trong backlog Claude sẽ làm khi hàng đợi review trống (theo cùng thứ tự ưu tiên, chỉ việc `auto: yes`).
- PR đang giữ và lý do (`needs-owner`, xếp chồng, draft).
- Hạn mức: lượt Codex còn trong ngày.
- **3–5 việc, không đếm PR** (owner 12.11.2026, thay mức 16–20 PR của 03.11). Plan chọn 3–5 việc không bị giữ theo thứ tự ưu tiên trên; mỗi việc ghi nguồn / AC (dòng G1 của PR) và dòng "Người dùng thấy gì". Tiến độ trong ngày = việc xong / việc đã chọn (xong là đã merge vào integration). Mọi PR body phải có dòng bắt đầu bằng `Người dùng thấy gì:`; PR docs hoặc vận hành ghi `Người dùng thấy gì: không trực tiếp (vận hành)` (preflight chặn nếu thiếu). Trần Codex 80 lượt/ngày (owner 15–16.11.2026; trước đó 60 từ 14.11.2026; lượt chạy tay cũng tính, §5).
- **Ít nhất 2 việc của kế hoạch 7 tuần mỗi ngày, một danh sách mỗi ngày** (owner 15.11.2026, "Bắt đầu"; `scripts/collab-quota.mjs`, Codex phản biện kế hoạch 15.11):
  - Việc thuộc kế hoạch 7 tuần khi PR hoặc issue việc (`Việc: #N`) có nhãn `ke-hoach-7-tuan`. Nhãn do vòng tự đọc trên GitHub; danh sách nào tự khai cũng không được tính. Issue tổng hợp tuần (không có mục `## Tiêu chí đạt`) không phải một việc.
  - Chỗ được tính theo việc: hai PR cùng `Việc: #N` chỉ chiếm một chỗ. Ứng viên gồm PR làm được (không draft, không `needs-owner`, không bị giữ) và issue việc 7 tuần chưa có PR. Với issue chưa có PR, Claude mở PR khi còn chỗ.
  - Plan 06:50 giữ `min(2, số việc 7 tuần sẵn sàng)` chỗ. Hai là mức sàn: còn chỗ thì nhận thêm. Không đủ việc sẵn sàng thì plan ghi thiếu bao nhiêu chỗ. Đọc nhãn lỗi thì plan ghi "chưa xác định được", không coi như không có việc.
  - Sự cố nghiêm trọng (issue `incident` + `severity:P0|P1`, hoặc PR làm issue đó) đứng đầu, nằm ngoài 3–5 việc và không chiếm chỗ đã giữ. Tổng vượt 5 thì plan báo quá tải để owner quyết.
  - Danh sách buổi sáng của Claude có dòng máy đọc được trong marker: `morning-prep date=D items=pr:N,item:M`. Vòng kiểm danh sách đó bằng đúng luật trên: không đạt thì máy chọn lại và ghi lý do. Comment plan và `plannedItems` lấy từ cùng một kết quả.
  - Trong ngày, owner `Bỏ #N` một việc đã chọn thì vòng chọn bù một lần bằng cùng luật. Bản chọn bù là một comment cập nhật, không phải plan mới, nên lệnh `Giữ`/`Bỏ` trước đó vẫn có hiệu lực.
  - Khi plan mở, vòng làm các PR 7 tuần đã chọn trước, rồi mới tới nhóm ưu tiên đang chạy.
  - Báo cáo có thêm dòng `Việc kế hoạch 7 tuần: đã chọn N, đạt M`, theo cách phân loại lúc lập plan.

## 4. Thành phần

| File | Vai trò | Quyền |
|---|---|---|
| `scripts/collab-trust.mjs` | Hàm dùng chung: lọc comment tin cậy, đọc dòng verdict/author check, phân loại PR, giờ VN | — |
| `scripts/collab-turn.mjs` | Đến lượt ai cho từng PR; `--report` thay registry; `--run` thực hiện | Chỉ đọc, trừ khi `--run` |
| `scripts/codex-review.mjs` | Chạy Codex review một PR, kiểm JSON, áp chính sách, đăng verdict, mở issue fix-forward | `codex exec -s read-only`; comment/issue/nhãn GitHub |
| `scripts/codex-review-schema.json` | Khuôn JSON Codex phải trả | — |
| `docs/operations/codex-review-prompt.md` | Prompt review cố định | Đổi qua PR |
| `scripts/collab-merge.mjs` | Kiểm đủ điều kiện rồi `gh pr merge --merge --match-head-commit` | Chỉ base `collab/integration` |
| `scripts/collab-plan.mjs` | Lập plan 06:50, đọc trả lời owner, cho biết hôm nay đã được chạy chưa | Comment issue plan |
| `scripts/collab-check.mjs` | Author check: từ 12.11.2026 (`LA_LANH_CHECK_SOURCE=ci` trong `collab-cron.sh`) đọc job `check` của workflow `pr-check.yml` ở đúng head, không chạy mã PR trên Mac; job sai workflow, sai commit, đang chạy hoặc bị hủy không cho PASS. Bỏ dòng env đó thì quay về cách cũ: `CI=1 pnpm check` trên checkout sạch đúng head. Đăng `Author check: PASS\|FAIL @ SHA`. `--clone` chạy trong clone riêng `~/.cache/la-lanh-collab/author`. Cả máy chỉ một check một lúc (`check.lock` + từ chối khi đang có `contracts:check`/vitest/pytest/playwright) | Comment PR |
| `scripts/collab-cron.sh` | Điểm vào cho launchd: cập nhật clone ops về `origin/collab/integration`, gọi `collab-tick.mjs` | — |
| `scripts/collab-tick.mjs` | Điểm vào một tick (tách khỏi `collab-turn` để không import vòng) | — |
| `scripts/launchd/com.lalanh.collab-tick.plist` | Mẫu job launchd (mỗi 10 phút) | — |
| Test `scripts/collab-loop.test.mjs` (`pnpm collab:test`, nằm trong `pnpm check`) | `node --test`, giả lập `gh`/`git`/`codex` | — |
| `~/Library/LaunchAgents/com.lalanh.collab-*.plist` | Lịch | User-level, gỡ được |
| `~/.cache/la-lanh-collab/` | Clone ops, clone review dùng một lần, khóa, trạng thái ngày, log, heartbeat | Ngoài repo |
| `docs/operations/codex-claude-collaboration.md`, `AGENTS.md`, `CLAUDE.md` | Cập nhật quy tắc mới | — |
| Lịch `la-lanh-autopilot` (Claude) | Mỗi giờ :37 trong khung đã mở; hỏi `collab-turn` trước khi làm | — |

### 4.1 `codex-review.mjs`

1. Đọc PR bằng `gh`: head SHA, base, nhãn, comment.
2. Từ chối nếu: base là `main`; draft; nhãn `needs-owner`; **đã có verdict tự động cho đúng SHA**; chưa có `Author check: PASS @ head`; vượt trần lượt Codex trong ngày. Từ 16.11.2026 (#571), lượt chạy tay cũng tính chung trần này. Chỉ được vượt trần khi có `--over-cap "<lời owner>"`; lời owner được ghi vào `overCapLog` trong state ngày.
3. Clone review riêng `~/.cache/la-lanh-collab/review`: fetch, `checkout --detach SHA`, `git clean -fdx`, kiểm `HEAD == SHA`.
4. Có verdict tự động trước cho SHA cũ là tổ tiên của SHA mới → truyền cả hai để Codex review `cũ..mới` và xác nhận lỗi cũ đã sửa.
5. `codex exec -s read-only --ephemeral -m gpt-6.1-sol -c model_reasoning_effort="high" -C <clone> --output-schema schema.json -o out.json`, prompt cố định, timeout 30 phút.
6. Lỗi hạn mức (usage/rate limit) → ghi `limit`, không tính vào trần, không đăng gì; lượt lưới sau thử lại.
7. Kiểm JSON: đúng khuôn, `sha` trùng head, mỗi finding có mức/loại/file/lý do.
8. Áp chính sách; script **chỉ nâng** verdict, không hạ.
9. Đăng comment PR: dòng đầu `Review verdict: … @ <SHA>`, `Reviewer: Codex (auto)`, bảng finding, SHA-256 của JSON, số vòng, đánh dấu ẩn `<!-- la-lanh-agent codex-auto-review sha=… p2=… base=… receipt=… -->` (dòng cuối; biên nhận cục bộ ghi trước khi đăng, §4.2).
10. P2 không chặn → mở issue `fix-forward`, gắn link vào comment.
11. **Từ 16.11.2026 (owner, gói 5 sửa luồng mục 1)** review không tự gắn `needs-owner` nữa: REQUEST_CHANGES ở vòng nào cũng về Claude sửa, author check, Codex review lại; review chưa đủ (PR quá lớn) là REQUEST_CHANGES để Claude tách PR. Dừng theo tỷ lệ (vòng sau dài thêm mà không còn lỗi chặn) là hoãn, tách hoặc đóng việc, không bao giờ bỏ qua một lỗi chặn. Bốn loại việc của owner do Codex ghi trong trường `owner_actions` của verdict (A2). Loại phải chờ owner trước merge thì gắn `needs-owner`, và cổng merge từ chối PR đó. Chữ privacy/consent/crisis/safety còn để cờ chờ duyệt thì gắn `owner-release-check`: PR vẫn merge được, nhưng phải chờ owner duyệt trước khi phát hành. Mỗi lần như vậy được ghi vào log review trên máy (`ownerActions`). **Từ 17.11.2026 (#611)** câu trả lời của owner được ghi trên PR bằng `node scripts/collab-owner-answer.mjs --record N --kinds <loại> --answer "<mã>" --quote "<lời owner nguyên văn>"`. Comment có dấu máy và biên nhận ký trên máy owner; biên nhận ký cả loại, mã và lời owner, nên bản chép hay bản sửa không được tính. Review sau không gắn lại nhãn cho loại đã trả lời, miễn là file của PR không đổi so với head lúc ghi; đồng bộ integration không làm mất câu trả lời. Loại chưa trả lời vẫn gắn nhãn. Verdict ghi "đã có câu trả lời của owner", log review ghi `answered`. Lệnh này chỉ gỡ `needs-owner` khi review cuối ở đúng head đã gắn nhãn, mọi loại giữ merge đã được trả lời, nhãn không bị đổi và owner không viết gì sau review đó. Chỉ ghi khi có lời owner nguyên văn, và chỉ cho loại owner đã trả lời. Câu trả lời là đồng ý; owner rút lại thì gắn lại nhãn. Luật cũ, giữ để tra: REQUEST_CHANGES tự động thứ 2 trên PR → gắn `needs-owner`. **Từ vòng thứ 3, Claude quyết** (owner 31.10.2026: "kể cả có ping pong qua lại nếu bạn đánh giá rất critical thì có thể sửa, và ảnh hưởng tới người dùng. còn không thì cứ dựa trên check list để quyết định cho việc review lần >=3. ko cần chờ tôi"):
    - phát hiện nghiêm trọng hoặc ảnh hưởng người dùng → Claude sửa, gỡ `needs-owner`, review lại, bao nhiêu vòng cũng được;
    - còn lại thì đi qua checklist Q1–Q5 (`decision-checklist.md`): cả năm câu "không" thì sửa và đi tiếp; có câu "có" (câu chữ mới, dữ liệu cá nhân, hướng sản phẩm) thì vẫn chờ owner;
    - quyết định ghi trên PR, kèm lý do gỡ nhãn.
    Nhãn `needs-owner` sau vòng 2 vì thế không có nghĩa là luôn chờ owner. Từ 15.11.2026 owner cũng không còn là bước duyệt bắt buộc (§2): nhãn chỉ giữ ý nghĩa "chờ owner" khi PR thuộc 4 loại việc chỉ owner quyết.
11a. **Mỗi PR chỉ một phiên (owner 16.11.2026, gói 5 mục 3a; `scripts/collab-pr-claim.mjs`).** Phiên nào muốn sửa một PR thì giữ PR đó trước bằng `node scripts/collab-pr-claim.mjs --claim N`, với `LA_LANH_SESSION=<id phiên>`. Bản giữ là một file trên máy owner, tạo nguyên tử. Comment hay nhãn trên PR công khai không có giá trị giữ. Khi một phiên đang giữ PR:
    - máy không đồng bộ PR đó với integration; PR chờ như PR không ở đầu hàng;
    - autopilot (id `autopilot`) không nhận việc sửa của PR đó;
    - lệnh check chạy tay của phiên khác cũng không đồng bộ PR đó.
    Bản giữ không hết hạn theo thời gian, vì không có commit chưa chứng minh phiên đã dừng. Bản giữ chỉ hết khi phiên nhả (`--release N`), khi PR merge hoặc đóng (tick tự bỏ), hoặc khi có lệnh nhả ép kèm lý do (`--force-release N --reason "…"`, ghi vào `pr-claims/releases.jsonl`).
11b. **Tối đa 2 việc nặng cùng lúc (owner 16.11.2026, gói 5 mục 3b).** Việc này làm theo hai bước, đúng như Codex phản biện.
    - **D1 (bước này):** mỗi chỗ chạy có tài nguyên riêng (`scripts/collab-heavy-slots.mjs`):
      - cổng e2e Playwright: 4173, hoặc 4273 cho chỗ thứ hai (`LA_LANH_E2E_PORT`); một việc chạy trong một chỗ không bao giờ dùng lại server mà nó không tự bật;
      - cổng verify, cổng QA API và web;
      - project Docker Compose và cổng Postgres.
      Chỗ 0 giữ đúng giá trị mặc định hiện nay.
    - **D2 (đã bật, 16.11.2026):** `collab-test-guard.mjs` có 2 chỗ: `test-guard.lock` và `test-guard-1.lock`.
      - Hai lượt test của agent được chạy cùng lúc. Mỗi lượt chạy với biến môi trường của chỗ mình; lượt thứ ba phải chờ.
      - Khi kiểm máy bận, một lượt không tính các tiến trình con của chỗ kia, nhưng vẫn tính mọi việc nặng khác.
      - Author check và lượt người giả đêm vẫn chạy một mình: author check chờ cả hai chỗ trống, và guard lùi lại khi có `check.lock`.
      - Chỗ có chủ đã chết thì không bị lấy lại; guard dùng chỗ còn lại.
      - Còn lại: chạy qa:journey, verify và script chụp ảnh buổi sáng qua guard. Script chụp ảnh nằm ngoài repo, do phiên khác giữ.
11c. **Mã ops cố định cho mỗi lượt chạy (owner 16.11.2026, gói 5 mục 3c).**
    - Tick (`collab-cron.sh`) và các bước `status`, `report`, `snapshot` của `ops-run.sh` không còn checkout lại cây `ops` dùng chung.
    - Mỗi lượt tạo một worktree tách riêng, đúng commit đã review vừa fetch (`ops-runs/<bước>-<giờ>-<pid>`), chạy ở đó rồi xóa khi xong. Báo cáo chạy giữa chừng vì vậy không đổi được mã mà tick đang chạy.
    - Worktree sót lại chỉ bị dọn khi tiến trình của nó đã dừng.
    - Cây `ops` vẫn được tick cập nhật để git hook và cổng dev con đọc.
    - **Sau merge:** cài lại bản `ops-run.sh` (`collab-ops-wrapper.mjs --install`) và bản `collab-cron.sh` ở `~/.cache/la-lanh-collab/bin/`. Bản cron đang cài có thêm một bước "cap-override" chưa qua review; từ khi trần cố định 80 thì bước này không cần nữa.
12. JSON và log lưu ở `~/.cache/la-lanh-collab/logs/`, không vào repo.

### 4.2 `collab-merge.mjs` — điều kiện merge (tất cả phải đúng)

- Base đúng `collab/integration`; không draft; không `needs-owner`; GitHub báo mergeable.
- `Review verdict: APPROVE @ <headRefOid>` mới nhất **có biên nhận cục bộ**; không có `REQUEST_CHANGES` nào mới hơn cho bất kỳ SHA nào (REQUEST_CHANGES không có biên nhận vẫn chặn, vì chỉ làm chặt hơn).
- `Author check: PASS @ <headRefOid>` mới nhất **có biên nhận** và đã thử **đúng SHA hiện tại** của `collab/integration` (đọc trực tiếp từ nhánh; `baseRefOid` của PR bị trễ nên không dùng). Một FAIL cho head ở base nào cũng chặn.
- Base đã đổi kể từ lúc review: APPROVE vẫn dùng được khi không file nào đổi trên base kể từ đó trùng file của PR (chỉ cần author check PASS mới trên base mới). Trùng file, không đọc được danh sách file (lỗi API, từ 300 file, base không đi tiếp) hoặc không biết base lúc review: phải review lại.
- Verdict có P2 không chặn → issue fix-forward đã được liên kết (số P2 lấy từ dòng niêm có biên nhận).
- `--merge --match-head-commit`. Không `--admin`, `--auto`, squash.
- PR xếp chồng không merge; sau khi PR cha merge, script đổi base sang `collab/integration` (chỉ khi PR cha đã merge). Dấu `retarget` chỉ để người đọc: chính việc đổi base làm bằng chứng cũ hết khớp.

**Biên nhận (12.11.2026, P1-B).** Claude và Codex đăng bằng chung tài khoản owner, nên comment một mình có thể bị giả. Đường review tự động (`codex-review.mjs`) và author check (`collab-check.mjs`) ghi thêm một biên nhận cục bộ ở `~/.cache/la-lanh-collab/state/receipts/`: HMAC-SHA256 trên (loại, PR, head, base, kết quả, số P2) bằng khóa `~/.cache/la-lanh-collab/keys/verdict.key` (tạo tự động, quyền 600, thư mục 700, nằm ngoài mọi checkout). Dòng cuối của comment ghi `base=` và `receipt=`; gate chỉ đếm comment có biên nhận khớp, không có đường lui. Ngay sau khi đăng, script gắn biên nhận vào id cố định của chính comment đó (`#issuecomment-…`, ghi một lần, cùng khóa HMAC); một comment chỉ được đếm khi id của nó là id đã gắn. Vì thế chép lại nội dung một PASS/APPROVE cũ (kể cả mã biên nhận công khai) sau một FAIL hay REQUEST_CHANGES mới hơn, hoặc sửa một comment khác thành nội dung đó, không bao giờ được đếm, và audit hằng ngày liệt kê merge như vậy (Codex auto-1 trên #456, 13.11.2026). Mỗi ngày một lần tick liệt kê các merge trong 24 giờ qua thiếu biên nhận và mở `[ops-alert] merge thiếu biên nhận`. Đây là phát hiện và nâng rào, chưa phải cách ly: tiến trình cùng user macOS (kể cả `pnpm check` chạy mã PR ở chế độ local) vẫn đọc được khóa; cách ly thật cần phiên Claude trong sandbox cấm đọc `~/.cache/la-lanh-collab/keys` hoặc một broker giữ khóa.

**Base đã thử (P1-A).** Chế độ local: check chỉ chạy khi `collab/integration` đã nằm trong head (tự đồng bộ cho nhánh `agent/*`; nhánh khác sang Claude merge vào), base ghi là SHA đó. Chế độ CI: job `check` của `pr-check` ghi annotation `pr-check-tested-base` từ parent đầu của merge commit nó thật sự thử; không có annotation hoặc khác SHA hiện tại thì không đăng PASS, chờ lượt CI mới.

### 4.3 `collab-turn.mjs` — bảng lượt

| Trạng thái PR | Lượt |
|---|---|
| Chưa có author check cho head | Lưới tick chạy preflight nhanh trước (thiếu G1–G10, mức S/M/L, G7 hoặc lỗi ruff/mypy thì ghi lý do, PR sang Claude sửa, không tốn lượt check; sửa mô tả PR hoặc đẩy head mới thì preflight chạy lại). Qua preflight thì tick chạy tối đa 3 author check liên tiếp (`checksPerTick`), không bắt đầu check mới sau 60 phút (`drainMinutes`), rồi review luôn nếu PASS. Claude chạy trực tiếp cũng được |
| Có author check, chưa có verdict cho head | Codex (review) |
| REQUEST_CHANGES @ head | Claude (sửa) |
| APPROVE @ head đủ điều kiện | Merge |
| Draft / `needs-owner` / xếp chồng chờ PR cha / bị `Bỏ #N` hôm nay | Giữ |
| Codex đã sửa thay Claude, chưa có phản biện thứ hai @ head | Giữ (chờ Antigravity, Claude hoặc Gemini) |

### 4.4 Chế độ chuyển sang Codex và phản biện thứ hai (owner 22.11.2026)

Owner: "chuyển qua codex khi claude gần hết. giữ 5% claude để duy trì nếu cần" và "tôi cần có phản biện nên ko muốn codex làm 1 mình".

- Bảng vòng có khối năng suất (owner 22.11 "okie 1-2-3"; L72; `scripts/collab-throughput.mjs`), chỉ điểm phần trăm và số đếm (R14): Claude hôm nay so với ngân sách ngày ((100 − 5 − đã dùng) ÷ số ngày tới lúc đặt lại; cần `resetsAt` trong `state/claude-usage.json`); PR Lá Lành merge hôm nay và điểm Claude mỗi PR; Gỡ Vướng theo luồng từ `state/go-vuong-status.json` (`{"at","streams":[{"name","passedToday","backlog","missedSchedules"}]}`, do điều phối Gỡ Vướng ghi); tỉ lệ đạt ngay lần đầu 7 ngày của Codex sửa và Antigravity phản biện; phần chi Claude hôm nay do việc nền xong và do tin phiên khác.
- Chuyển việc sớm theo giới hạn tuần Claude (owner 22.11 "okie 1-2-3"; L71; `scripts/collab-usage.mjs`, R1/R8):
  - Từ 75% (chuyển bớt): lượt Claude sửa chuyển sang Codex, phản biện do Antigravity, bỏ lượt Claude kiểm mẫu. PR có nhãn `incident` vẫn do Claude.
  - Từ 85% (tiết kiệm): Claude chỉ làm sự cố; mọi lượt sửa khác sang Codex.
  - Từ 95% (chuyển sang Codex, giữ 5%): không dùng Claude; Codex sửa cả sự cố, Antigravity phản biện, máy kiểm và merge PR nhỏ ops/test; lịch và hàng việc vẫn chạy.
  - Codex sửa (`scripts/codex-fallback.mjs`) ghi file trong clone riêng, không mạng, test trước khi push, không force.
- **Codex không bao giờ vừa sửa vừa duyệt một mình.** PR có dấu `fallback pr=` (Codex đã sửa) cần thêm một dòng `Phản biện: APPROVE @ <head>` với `Reviewer: Antigravity`, `Reviewer: Claude` hoặc `Reviewer: Gemini`, có biên nhận cục bộ (`Second-receipt:`), trước khi merge. Thiếu thì PR giữ; `REQUEST_CHANGES` thì quay lại lượt sửa.
- **Antigravity trước** (owner 22.11: "ưu tiên anti hơn gemini"; L70). Antigravity là ứng dụng agent của Google trên máy owner, không tốn lượt Claude, nên vòng tự động tự chạy: mỗi lượt tick một bước (`scripts/collab-antigravity.mjs`, cả khi không ở chế độ chuyển sang Codex). Bước 1 mở một cuộc trò chuyện (`agentapi new-conversation --model=pro`) với diff PR công khai; các lượt sau đọc câu trả lời qua cổng nội bộ của ứng dụng (token lấy từ file daemon vào env, không in, không ghi log). Câu trả lời chỉ được tính khi Antigravity không dùng công cụ nào (lệnh, file, trình duyệt), dòng đầu đúng mẫu `Kết luận: ...` và có trong 20 phút; sai thì bỏ, PR vẫn giữ, lượt sau mở lại. Kết quả đăng như các phản biện khác (`Reviewer: Antigravity`, có biên nhận). Ứng dụng tắt thì bước này báo lỗi trong log và người phản biện dự phòng dưới đây làm thay. Rủi ro còn lại (đã chấp nhận, ghi 22.11): Antigravity để chế độ chạy lệnh tự động và vòng không khóa được chế độ đó (`--profile` bị bỏ qua). Nếu diff có câu dụ chạy lệnh, lệnh vẫn chạy trong hộp cát mặc định của máy owner (không mạng, đọc được thư mục tạm) và kết quả vào ngữ cảnh của mô hình, dù câu trả lời đó bị bỏ, không đăng. Vì vậy chỉ PR của chính owner (không fork) mới được gửi, và owner không được đổi hộp cát mặc định của Antigravity. Từ 22.11 (L71) Antigravity phản biện mọi PR đang chờ Codex review hoặc merge, mỗi head một lần, PR Codex sửa đi trước. `REQUEST_CHANGES` của Antigravity đưa bất kỳ PR nào về lượt sửa; `APPROVE` chỉ bắt buộc với PR Codex sửa. Owner cho phép Antigravity cả sửa PR (R1), nhưng vai trò này chưa bật: thăm dò 22.11 cho thấy vòng chưa khóa được thư mục, lệnh và mạng như Codex. Chỉ bật khi một lần thăm dò mới đạt các giới hạn đó.
- Dự phòng khi Antigravity không chạy: một phiên Claude điều khiển (dùng phần 5% giữ lại, nhẹ nhất có thể):
  1. `node scripts/collab-second-review.mjs --list` xem PR đang chờ.
  2. Gemini trên web (owner cho Claude điều khiển 22.11): `node scripts/collab-second-review.mjs --brief N | pbcopy`, mở `gemini.google.com` trong trình duyệt tích hợp (tài khoản owner tự đăng nhập), dán bằng phím, gửi, đọc câu trả lời bằng đọc chữ của trang (không chụp màn hình). Chỉ gửi diff và văn bản PR công khai; không gửi trí nhớ, transcript, file riêng (R14).
  3. Lưu câu trả lời vào file tạm, rồi `--post N --reviewer Gemini --verdict <theo dòng "Kết luận"> --head <SHA> --notes <file>`. Phiên Claude không tự đổi kết luận của Gemini. Sau một `REQUEST_CHANGES` cho head, head đó không được duyệt nữa: phải có bản sửa mới (head mới) rồi phản biện lại (Gemini tìm ra lỗ này ở lần phản biện đầu, 22.11). Bất đồng kéo dài đi theo R4.
  4. Còn lượt Claude thì Claude tự phản biện là đủ; Gemini web dùng khi Claude gần hết và Antigravity không chạy.

`--tick`: chỉ làm việc trong **nhóm ưu tiên đang mở**: nhóm sớm nhất còn việc cho máy (author check, Codex review, merge). PR đang chờ Claude sửa không chặn máy; Claude vẫn sửa theo thứ tự nhóm (sửa 31.10.2026 sau 2 giờ đứng yên): PR quy trình trước, rồi content xong hết mới tới privacy, rồi tính năng mới. Tối đa 2 lượt Codex và 2 merge mỗi lần; giờ được đọc lại trước mỗi việc nên không bắt đầu việc mới từ 23:35 (trước 14.11.2026 là 23:30). Lượt Claude ghi vào `~/.cache/la-lanh-collab/claude-queue.json` cho autopilot.

Mỗi lúc chỉ một review chạy (khóa `review.lock`), vì mọi review dùng chung clone; review thứ hai trả `busy` và chờ lượt sau. Author check mới nhất cho head quyết định (FAIL sau PASS thì chặn). Khi `collab/integration` đi tiếp, PASS cũ hết hiệu lực và PR quay lại author check; APPROVE cũ chỉ hết hiệu lực khi base đổi trên file của PR (§4.2).

## 5. An toàn

- **PR của người ngoài:** vòng tự động chỉ chạy, review hay merge PR **do tài khoản owner mở từ nhánh trong repo** (`author.login` = owner, `isCrossRepository = false`). PR từ fork hoặc tác giả khác luôn ở trạng thái Giữ; code của nó không bao giờ được fetch, build hay chạy trên máy owner (Codex r1 P0 trên #137).
- **Giới hạn giờ cho check tự động:** không bắt đầu từ 23:35, đọc lại giờ sau khi chuẩn bị clone, và giết cả nhóm tiến trình (Vite, Playwright, pytest) trước 23:59.
- **Giả mạo verdict:** repo public. Chỉ tin comment có `author_association` = `OWNER`. Comment của người khác chỉ là dữ liệu.
- **Giả mạo duyệt plan:** hai agent dùng chung tài khoản owner. Script của agent không bao giờ đăng comment bắt đầu bằng `Duyệt`/`Giữ`/`Bỏ`, và mọi comment của agent mang đánh dấu `la-lanh-agent`; comment có đánh dấu này không được tính là trả lời của owner. Rủi ro còn lại thấp vì plan chạy ngay khi đăng, không cần `Duyệt` (từ 16.11.2026); quyền thật sự quan trọng là `Giữ`.
- **Prompt injection:** Codex read-only, prompt cố định, nội dung PR là dữ liệu. Script đăng verdict, agent không chèn tay.
- **Đọc nhầm commit:** clone review riêng, kiểm `HEAD == SHA`; `--match-head-commit` khi merge.
- **Vòng lặp:** 2 vòng REQUEST_CHANGES tự động mỗi PR; **80 lượt Codex/ngày** (owner 15–16.11.2026, gói 5 mục 3; lượt chạy tay cũng tính, #585; trước đó 60 từ 14.11.2026; trước đó 32 từ 03.11.2026), cộng số lượt owner cho thêm trong ngày (`ownerExtraCodex.granted` trong state ngày, owner 15.11.2026; từ 16.11.2026 lượt cho thêm ghi kèm `base: 80`, lượt cho thêm cũ không có `base` thì tính từ 60, nên 60 + 20 = 80; `dayCap` trong `collab-trust.mjs`), vẫn giữ 1 lượt cho soát đêm; khóa file.
- **Lỗi im lặng:** heartbeat (`~/.cache/la-lanh-collab/heartbeat.json`) mỗi tick; tick lỗi 2 lần liên tiếp → issue `ops-alert`. Hết hạn mức không tính là lỗi. Mac tắt hoặc ngủ thì không có gì trên Mac báo được; dấu hiệu là sáng hôm đó không có plan 06:50 trên issue.
- **Dữ liệu riêng tư lọt vào repo công khai (sửa 03.11.2026):** một subagent ghi một mốc dữ liệu thật vào fixture của PR công khai. Danh sách mục cấm nằm **chỉ trên máy owner** ở `~/.cache/la-lanh-collab/private-guard.txt` (không vào git; mã băm của một ngày sinh cũng lộ như chính ngày đó vì thử hết mọi ngày chỉ mất vài mili giây). Mỗi dòng một mục; `date:YYYY-MM-DD` tự khớp các cách viết ISO, `dd/mm/yyyy`, `d/m/yyyy`, `dd.mm.yyyy` và `yyyymmdd`. Author check quét patch của **từng commit** chưa có trên `collab/integration` (một giá trị thêm ở commit này rồi xoá ở commit sau vẫn bị bắt, vì commit đầu vẫn lên GitHub; commit merge được quét theo từng parent vì phần xử lý xung đột có thể thêm chữ mới), tên file kể cả file chỉ đổi tên hoặc file rỗng, commit message, tiêu đề và mô tả PR, trước khi chạy `pnpm check`. **Thiếu file danh sách (hoặc file không có mục nào) không phải "ok"** (L30, 15.11.2026: file thiếu mà không ai biết): bước quét in `private-guard: list missing`, push không bị chặn (owner quyết), bảng trạng thái của tick ghi ⚠️ cho tới khi owner tạo file. Hook `pre-push` v3 chấp nhận dòng này. Trúng thì receipt `FAIL` ghi file:dòng, không bao giờ ghi giá trị; tên file chứa mục cấm được che thành `[ẩn]`. Không đọc được lịch sử nhánh, hoặc file danh sách tồn tại mà không đọc được (sai quyền, là thư mục), cũng `FAIL`; chỉ khi chưa có file thì bỏ qua. `node scripts/collab-check.mjs --guard` chạy cùng phép quét làm hook `pre-push` trong clone của Claude: đọc từng ref Git sắp push và quét mọi commit remote chưa có, để mục cấm không lên remote công khai. Tới 13.11.2026 hook này chưa từng được cài; từ đó `node scripts/collab-hooks.mjs --install` cài hook (chạy script của clone ops, nên nhánh đang push không tắt được kiểm của chính nó; hook gồm cả `collab-preflight.mjs --lint` với `uv run --locked`), và bảng trạng thái của tick ghi ⚠️ khi hook thiếu, bị sửa hoặc mất quyền chạy.
- **Tác vụ hẹn giờ của Claude bị treo (sửa 03.11.2026):** một lượt chạy không người trông mà dừng ở hộp hỏi quyền thì treo mãi, và mọi lượt sau không chạy (autopilot treo 2,5 ngày, kiểm tra server treo 1 tuần mà không ai biết). Mỗi tác vụ ghi nhịp `start` và `done` bằng `node scripts/collab-watchdog.mjs --beat <task> start|done` (lệnh đầu tiên và lệnh cuối cùng của lượt chạy). Tick 10 phút, vốn không dùng AI nên không bị hỏi quyền, kiểm nhịp `done`: autopilot quá 2 giờ (chỉ tính từ 09:00 tới 24:00), kiểm tra server quá 7 giờ, báo cáo cuối ngày quá 26 giờ thì coi là treo. Khi đó tick gửi thông báo trên Mac và mở issue `ops-alert`, mỗi lần treo chỉ báo một lần. Có nhịp `start` mà không có `done` nghĩa là đang chờ bấm cho phép. Từ 04.11.2026 (fix D) một nhịp `start` quá 30 phút chưa có `done` là lượt treo: báo ngay ở mọi giờ, không chờ ngưỡng lịch, ghi nhịp `stuck` để lượt sau không bị chặn; không bao giờ giết tiến trình. Lượt treo được so với nhịp `done`, kể cả khi watchdog mới thấy tác vụ lần đầu (#229). Plan buổi sáng có mục **Tác vụ hẹn giờ** ghi lần xong cuối của từng tác vụ, nên owner thấy tình trạng mỗi sáng dù không có cảnh báo.
- **Author check FAIL không còn log (sửa 05.11.2026):** check của #248 FAIL sau 509 giây nhưng không giữ log, lần chạy lại PASS; nghi có test của subagent chạy cùng lúc. Nay toàn bộ output `pnpm check` ghi vào `~/.cache/la-lanh-collab/logs/check-<pr>-<sha12>.log` (quyền 0600, giữ 30 file mới nhất; PASS thì xoá). Receipt `FAIL` công khai chỉ ghi bước `pnpm <bước>` bị lỗi và tên file log; không đăng dòng log nào, vì không bộ lọc nào chắc chắn bắt hết secret (`scripts/collab-check-log.mjs`).
- **Không chạy test của agent trong lúc author check (sửa 05.11.2026):** `node scripts/collab-test-guard.mjs -- <lệnh>` chờ tới khi `collab-check.mjs --busy` rảnh, giữ `test-guard.lock` khi lệnh chạy, và từ chối (mã 75) khi author check đang giữ `check.lock`. Khóa của tiến trình đã chết không bao giờ tự xóa: guard từ chối và chỉ đường dẫn để owner tự xóa; author check bỏ qua khóa chết quá 30 phút cho lượt chờ của mình nhưng không xóa. Author check chờ tối đa 5 phút cho `test-guard.lock`, quá thì trả `busy` và thử lượt sau. Quy tắc một dòng cho mọi brief subagent:

  > Chỉ chạy test qua `node scripts/collab-test-guard.mjs -- <lệnh test>`; không chạy test trực tiếp, không chạy `pnpm check`.

- **Cổng dev con (L06, 15.11.2026):** dev con mở bằng Agent tool không do chương trình mở, nên việc kiểm nằm ở chính lần ghi.
  - **Cách kiểm:** hook `PreToolUse` (Edit/Write/NotebookEdit/Bash) chạy `scripts/collab-agent-gate.mjs` từ clone ops, `onFailure: "block"`. Hook chỉ áp cho tool call có `agent_id` (dev con); phiên chính không bị kiểm.
  - **Ghi vào clone của repo Lá Lành:** nơi ghi được tính theo đường dẫn thật. Lần ghi đầu phải qua preflight đầy đủ: worktree riêng, nhánh `agent/claude/*` hoặc `worktree-agent-*`, cây sạch, `git` và `node` có trên máy, hook `pre-push` chặn được mục giả. Qua thì dev con được nhận workspace (claim). Các lần ghi sau kiểm lại nhánh và chủ claim mỗi lần.
  - **Claim:** nằm cạnh khóa của `collab-dispatch.mjs`, nên hai bên loại trừ nhau. Claim chỉ hết khi dev con đã dừng (`SubagentStop`) và không còn tiến trình nào có thư mục làm việc trong workspace. Quá 6 giờ chỉ đánh dấu nghi bỏ dở, không tự mở khóa.
  - **Được phép:** Bash chỉ đọc chạy ở đâu cũng được. "Chỉ đọc" là danh sách cho phép: mỗi lệnh và mỗi lệnh con của git chỉ nhận đúng các tùy chọn đã liệt kê, so khớp nguyên chữ; tùy chọn khác (kể cả viết tắt) bị coi là ghi. Git chỉ được miễn với các lệnh không thể chạy chương trình theo cấu hình (`rev-parse`, `merge-base`, `rev-list --count`, `branch --show-current`, `config --get`). `diff`, `log`, `show`, `status`, `grep`, `blame`, `ls-files` và `find` phải qua kiểm workspace, vì cấu hình có thể làm chúng chạy diff.external, textconv, gpg, fsmonitor, hoặc `-exec`. Lệnh dựng workspace (`git -C <clone> fetch`, `git -C <clone> worktree add <đường> -b agent/claude/...`) được chạy trên clone dùng chung.
  - **Cài và kiểm:** cài bằng `node scripts/collab-ops-wrapper.mjs --install-agent-gate`. `--verify` và tick kiểm mục hook, kiểm `onFailure` và kiểm `disableAllHooks`. Lệch thì mở `ops-alert` mỗi ngày một lần, sửa xong thì tự đóng.
  - **Giới hạn** (cùng quyền máy như L24):
    - Claude vẫn gỡ được hook; kiểm tra chỉ phát hiện, không ngăn được.
    - Bash được kiểm theo thư mục làm việc của từng phần lệnh (kể cả sau `cd`), các đường dẫn tuyệt đối, các đường dẫn tương đối có dấu `/`, thư mục sau `git -C` (nhiều `-C` nối tiếp được tính như Git), tên không có `/` nhưng đang tồn tại trên đĩa (kể cả symlink), giá trị dính trong tùy chọn (`--output=link`, `-olink`), và mọi đích chuyển hướng `>`. Cổng không kiểm được mọi dạng lệnh: đường dẫn chỉ sinh ra lúc chạy thì không thấy. Đường dẫn chỉ sinh ra lúc lệnh chạy (biến, `$(…)`) thì không thấy được.
    - Cổng chống ghi nhầm do vô tình. Một lệnh được soạn có chủ ý để chạy chương trình qua một công cụ đọc được phép không nằm trong phạm vi chặn; danh sách cho phép chặn mặc định giúp giảm rủi ro này.
    - Worktree của checkout cũ `la-lanh` chưa có hook `pre-push`, nên dev con phải làm trong worktree của `la-lanh-claude`.
- **Dữ liệu:** chỉ code public; không dữ liệu người dùng. Log ở máy owner.
- **Code chạy theo lịch:** launchd chạy script từ clone ops ở `origin/collab/integration` (chỉ code đã review).

## 6. Giới hạn đã biết

- Codex read-only nên không tự chạy test; bằng chứng test là author check trên đúng SHA.
- Mac phải bật; app Claude phải mở cho lượt Claude tự động.
- Review tự động không thay buổi review sâu lời văn/giọng Lá mỗi đợt.
- Cùng tài khoản GitHub: "Codex (auto)" là ghi chú, không phải danh tính kiểm chứng được.
- PR rất lớn (#93 ~14k dòng, #119 ~4,3k dòng) có thể vượt khả năng một lượt review; nếu Codex báo không review hết thì verdict là REQUEST_CHANGES để Claude tách PR (từ 16.11.2026; trước đó script gắn `needs-owner`).

## 7. Kế hoạch xây và triển khai

| Bước | Nội dung | Xong khi |
|---|---|---|
| 1 | `collab-trust`, `collab-turn` (chỉ đọc) + test | Test xanh; `--report` chạy trên PR đang mở |
| 2 | `codex-review` + schema + prompt + test giả lập | Test xanh (trùng SHA, sai SHA, JSON hỏng, nâng verdict, trần vòng, hạn mức) |
| 3 | `collab-merge` + test | Test từ chối đúng từng điều kiện ở 4.2 |
| 4 | `collab-plan` + `collab-cron.sh` + test | Test giờ 09/10/23:30 (từ 14.11.2026: 06:50/08:00/23:35), Duyệt/Giữ/Bỏ, comment agent bị loại |
| 5 | Sửa tài liệu phối hợp, AGENTS.md, CLAUDE.md | Quy tắc trong docs khớp code |
| 6 | Mở PR; **script review PR của chính nó** bằng Codex thật | Verdict thật đăng trên PR |
| 7 | Merge PR theo luồng mới | Merge bằng `collab-merge` |
| 8 | Cài launchd + đổi `la-lanh-autopilot` | Một lần chạy lưới thành công, có heartbeat |
| 9 | Plan đầu tiên (giờ lúc đó 08:50; nay 06:50, chạy ngay khi đăng); PR content đang mở đi qua luồng mới | Ít nhất một PR content merge không cần owner |
| 10 | Báo cáo tuần đầu theo bảng mục 1 | Owner quyết giữ/chỉnh |

### 7.1 Đánh giá vòng `checkshas.sh` (owner giao 31.10.2026)

Session Claude cũ chạy `checkshas.sh`: `CI=1 pnpm check` lần lượt trên nhiều SHA trong `la-lanh-claude`, kết quả chỉ nằm ở log local.

- Hợp lý: đúng SHA (kiểm `HEAD == SHA`), `CI=1` nên e2e không dùng lại server của checkout khác, chạy lần lượt.
- Không hợp lý: không đăng `Author check:` nên vòng tự động không thấy, phải check lại (p113 bị check 3 lần, p118 PASS tối 30/10 vẫn phải chạy lại); dùng chung `la-lanh-claude` và không có khóa nên chạy chồng với author check khác (tối 30/10); chạy cả đêm ngoài lịch ngày.
- Quyết định: thay bằng lưới tick tự chạy `collab-check --clone` (giữ `CI=1`, đúng SHA, lần lượt), có khóa và đăng receipt. Không chạy `checkshas.sh` nữa.

Gỡ bỏ: `launchctl bootout` các job, đổi lịch autopilot về cũ, revert PR. Không ảnh hưởng code sản phẩm.
