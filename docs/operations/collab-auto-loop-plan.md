# Bản thiết kế: vòng tự động Claude ⇄ Codex

Trạng thái: **ĐÃ CHỐT với owner ngày 30.10.2026.** Code xây theo đúng bản này; đổi thiết kế thì sửa file này qua PR trước.

## 1. Mục tiêu và thước đo

| Thước đo | Hiện tại (11–30/10) | Mục tiêu sau 1 tuần |
|---|---|---|
| Thời gian một vòng review | ≤ vài giờ (chờ owner chuyển lời) | ≤ 15 phút |
| Mở PR → merge integration (trung vị) | 22 giờ | ≤ 2 giờ |
| PR có ≥ 3 vòng verdict | 32 / 106 | ≤ 10% |
| Owner phải chuyển lời giữa hai agent | mỗi vòng | 0 (chỉ duyệt plan 9h và buổi review sâu mỗi đợt) |
| PR chỉ để ghi registry | ~10 | 0 |

Ngoài phạm vi: merge vào `main`, release, deploy, server/DB thật, provider, IAM, secret, budget. Những việc này giữ nguyên quyền owner.

## 2. Quyết định owner đã chốt (30.10.2026)

1. Claude gọi Codex trực tiếp để review; lịch mỗi giờ là lưới an toàn.
2. Merge tự động vào `collab/integration` khi đủ điều kiện ở mục 4.2, **bắt buộc có `Author check: PASS @ <SHA>`**.
3. Chính sách P2: P2 về **privacy, bảo mật, lời văn gửi người dùng** chặn merge; P2 khác được APPROVE kèm issue sửa tiếp (fix-forward); P3 không chặn; P0/P1 luôn chặn.
4. **Lịch ngày:** 9h owner xem plan trong ngày. Owner duyệt thì chạy ngay; 10h chưa có trả lời thì tự chạy; chạy đến 24h.
5. **Model Codex:** `gpt-6.1-sol`, mức suy nghĩ `high`. Hết hạn mức thì chờ reset và chạy tiếp nếu còn lượt trong ngày.
6. **Ngừng PR registry**, thay bằng `collab-turn --report`.
7. **Thứ tự ưu tiên công việc:** xong **toàn bộ content** → **data privacy** → **tính năng mới**. Không giữ PR theo kích thước; xếp theo thứ tự này. PR quy trình (`area:ops`: vòng tự động, CI, test) đi trước cả ba nhóm (owner giao Claude tự chọn, 30.10.2026).

10. **Từ vòng review tự động thứ 3** (owner 31.10.2026): Claude tự quyết theo checklist, không chờ owner. Nhãn `needs-owner` do trần 2 vòng được Claude gỡ khi lỗi nghiêm trọng hoặc ảnh hưởng người dùng (sửa tiếp dù nhiều vòng), hoặc khi Q1–Q5 đều "không"; ghi "Round N: Claude decides per checklist" trên PR. Duyệt copy và mọi câu Q1–Q5 "có" vẫn chờ owner.

## 3. Luồng chuẩn

```
Claude xong việc trên branch, push → node scripts/collab-check.mjs --pr N (pnpm check trên đúng head) → "Author check: PASS @ SHA"
  → mở PR (nếu chưa có), gắn nhãn area:content | area:privacy | area:feature | area:ops
  → node scripts/codex-review.mjs --pr N        (Claude chờ, cùng session)
      ├─ APPROVE @ SHA   → node scripts/collab-merge.mjs --pr N → merge integration
      └─ REQUEST_CHANGES → Claude sửa → author check → push → review lại (chỉ phần đổi)
           vòng REQUEST_CHANGES tự động thứ 2 → nhãn needs-owner, dừng
```

### 3.1 Lịch ngày (giờ Việt Nam)

| Giờ | Việc |
|---|---|
| 08:50 | `collab-plan.mjs --make`: lập plan trong ngày, đăng lên issue "Kế hoạch chạy tự động hằng ngày", báo thông báo macOS |
| 09:00–09:50 | Mỗi 10 phút kiểm owner trả lời. `Duyệt` → bắt đầu chạy ngay |
| 10:00 | Chưa có trả lời → tự bắt đầu chạy theo plan |
| Từ lúc bắt đầu → 23:30 | launchd tick mỗi 10 phút; mỗi tick làm việc khi máy rảnh (merge, author check, Codex review), không còn giới hạn một lần mỗi giờ (retro D1, 31.10.2026). Claude autopilot chạy mỗi giờ (phút :37) |
| 23:55 | Cắt mọi lượt đang chạy dở; không bắt đầu lượt mới sau 23:30 |
| 00:00–08:50 | Không chạy tự động |

Trả lời của owner trên issue plan (comment mới hơn plan của ngày đó):
- `Duyệt` — chạy ngay.
- `Giữ` — hôm nay không chạy tự động (session owner tự mở vẫn chạy bình thường).
- `Bỏ #N` — bỏ PR N khỏi plan hôm nay (có thể nhiều dòng).

Session mà owner đang trực tiếp trò chuyện không bị lịch này chặn; lịch chỉ áp cho lượt tự động.

### 3.2 Cách làm hằng ngày (owner chốt 31.10.2026)

1. **Việc nặng nối tiếp, việc nhẹ song song.** Việc nặng là `pnpm check`, cài đặt hoặc build trong clone. Mỗi lúc chỉ một việc nặng trên cả máy (`check.lock`, từ chối khi máy đang có check). Trong lúc việc nặng chạy, Claude làm việc nhẹ của nhóm ưu tiên đang mở: sửa fix-forward, viết code, viết test, viết docs. Claude không ngồi chờ.
2. **Việc nặng đi qua vòng tự động.** Author check, review và merge chạy qua tick hoặc qua `collab-check` → `codex-review` → `collab-merge`. Không session nào tự chạy `pnpm check` bằng script riêng; `checkshas.sh` đã thay (§7.1).
3. **Fix-forward là việc kế tiếp.** Issue `fix-forward` mới thuộc cùng nhóm với PR gốc và được làm ngay trong ngày, qua PR riêng.
4. **Đầu ngày.** Mac tự thức 08:45 (`sudo pmset repeat wakeorpoweron MTWRFSU 08:45:00`, owner chạy một lần). Claude đọc `collab-turn --report`, dừng lượt autopilot còn treo từ hôm trước và kiểm tra plan #133 đã được đăng.
5. **Trong ngày.** Một quyết định mới của owner được ghi ngay vào file này hoặc vào issue hub #2, để mọi session đều đọc được (bài học từ #136).
6. **Cuối ngày.** Claude nhìn lại quy trình trong ngày, viết report ở `docs/reviews/YYYY-MM-DD-collab-loop-retro.md` (số liệu, chỗ kẹt, đã sửa, đề xuất) và mở PR `area:ops` để Codex review qua vòng tự động.

### 3.3 Plan trong ngày gồm

- Hàng đợi PR theo thứ tự ưu tiên: quy trình/ops (sửa vòng tự động, CI, test) → content → privacy → tính năng mới (owner giao Claude tự tối ưu, 30.10.2026); trong cùng nhóm, PR cũ trước.
- Lượt dự kiến cho từng PR (Claude check / Codex review / Claude sửa / merge / giữ).
- Việc trong backlog Claude sẽ làm khi hàng đợi review trống (theo cùng thứ tự ưu tiên, chỉ việc `auto: yes`).
- PR đang giữ và lý do (`needs-owner`, xếp chồng, draft).
- Hạn mức: lượt Codex còn trong ngày.

## 4. Thành phần

| File | Vai trò | Quyền |
|---|---|---|
| `scripts/collab-trust.mjs` | Hàm dùng chung: lọc comment tin cậy, đọc dòng verdict/author check, phân loại PR, giờ VN | — |
| `scripts/collab-turn.mjs` | Đến lượt ai cho từng PR; `--report` thay registry; `--run` thực hiện | Chỉ đọc, trừ khi `--run` |
| `scripts/codex-review.mjs` | Chạy Codex review một PR, kiểm JSON, áp chính sách, đăng verdict, mở issue fix-forward | `codex exec -s read-only`; comment/issue/nhãn GitHub |
| `scripts/codex-review-schema.json` | Khuôn JSON Codex phải trả | — |
| `docs/operations/codex-review-prompt.md` | Prompt review cố định | Đổi qua PR |
| `scripts/collab-merge.mjs` | Kiểm đủ điều kiện rồi `gh pr merge --merge --match-head-commit` | Chỉ base `collab/integration` |
| `scripts/collab-plan.mjs` | Lập plan 08:50, đọc trả lời owner, cho biết hôm nay đã được chạy chưa | Comment issue plan |
| `scripts/collab-check.mjs` | Author check: `CI=1 pnpm check` trên checkout sạch đúng head, đăng `Author check: PASS\|FAIL @ SHA`. `--clone` chạy trong clone riêng `~/.cache/la-lanh-collab/author`. Cả máy chỉ một check một lúc (`check.lock` + từ chối khi đang có `contracts:check`/vitest/pytest/playwright) | Comment PR |
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
2. Từ chối nếu: base là `main`; draft; nhãn `needs-owner`; **đã có verdict tự động cho đúng SHA**; chưa có `Author check: PASS @ head`; vượt trần lượt Codex trong ngày (lượt tự động).
3. Clone review riêng `~/.cache/la-lanh-collab/review`: fetch, `checkout --detach SHA`, `git clean -fdx`, kiểm `HEAD == SHA`.
4. Có verdict tự động trước cho SHA cũ là tổ tiên của SHA mới → truyền cả hai để Codex review `cũ..mới` và xác nhận lỗi cũ đã sửa.
5. `codex exec -s read-only --ephemeral -m gpt-6.1-sol -c model_reasoning_effort="high" -C <clone> --output-schema schema.json -o out.json`, prompt cố định, timeout 30 phút.
6. Lỗi hạn mức (usage/rate limit) → ghi `limit`, không tính vào trần, không đăng gì; lượt lưới sau thử lại.
7. Kiểm JSON: đúng khuôn, `sha` trùng head, mỗi finding có mức/loại/file/lý do.
8. Áp chính sách; script **chỉ nâng** verdict, không hạ.
9. Đăng comment PR: dòng đầu `Review verdict: … @ <SHA>`, `Reviewer: Codex (auto)`, bảng finding, SHA-256 của JSON, số vòng, đánh dấu ẩn `<!-- la-lanh-agent codex-auto-review sha=… -->`.
10. P2 không chặn → mở issue `fix-forward`, gắn link vào comment.
11. REQUEST_CHANGES tự động thứ 2 trên PR → gắn `needs-owner`.
12. JSON và log lưu ở `~/.cache/la-lanh-collab/logs/`, không vào repo.

### 4.2 `collab-merge.mjs` — điều kiện merge (tất cả phải đúng)

- Base đúng `collab/integration`; không draft; không `needs-owner`; GitHub báo mergeable.
- `Review verdict: APPROVE @ <headRefOid>` mới nhất từ comment tin cậy; không có `REQUEST_CHANGES` nào mới hơn cho bất kỳ SHA nào.
- `Author check: PASS @ <headRefOid>` từ comment tin cậy.
- Verdict có P2 không chặn → issue fix-forward đã được liên kết.
- `--merge --match-head-commit`. Không `--admin`, `--auto`, squash.
- PR xếp chồng không merge; sau khi PR cha merge, script đổi base sang `collab/integration` (chỉ khi PR cha đã merge) và PR quay lại vòng review vì diff đổi.

### 4.3 `collab-turn.mjs` — bảng lượt

| Trạng thái PR | Lượt |
|---|---|
| Chưa có author check cho head | Lưới tick tự chạy (1 PR mỗi tick, không cần AI), rồi review luôn nếu PASS. Claude chạy trực tiếp cũng được |
| Có author check, chưa có verdict cho head | Codex (review) |
| REQUEST_CHANGES @ head, chưa `needs-owner` | Claude (sửa) |
| APPROVE @ head đủ điều kiện | Merge |
| Draft / `needs-owner` / xếp chồng chờ PR cha / bị `Bỏ #N` hôm nay | Giữ |

`--tick`: chỉ làm việc trong **nhóm ưu tiên đang mở** (nhóm sớm nhất còn PR không ở trạng thái Giữ): PR quy trình trước, rồi content xong hết mới tới privacy, rồi tính năng mới. Tối đa 2 lượt Codex và 2 merge mỗi lần; giờ được đọc lại trước mỗi việc nên không bắt đầu việc mới sau 23:30. Lượt Claude ghi vào `~/.cache/la-lanh-collab/claude-queue.json` cho autopilot.

Mỗi lúc chỉ một review chạy (khóa `review.lock`), vì mọi review dùng chung clone; review thứ hai trả `busy` và chờ lượt sau. Author check mới nhất cho head quyết định (FAIL sau PASS thì chặn). Sau khi đổi base, verdict cũ hết hiệu lực.

## 5. An toàn

- **PR của người ngoài:** vòng tự động chỉ chạy, review hay merge PR **do tài khoản owner mở từ nhánh trong repo** (`author.login` = owner, `isCrossRepository = false`). PR từ fork hoặc tác giả khác luôn ở trạng thái Giữ; code của nó không bao giờ được fetch, build hay chạy trên máy owner (Codex r1 P0 trên #137).
- **Giới hạn giờ cho check tự động:** không bắt đầu sau 23:30, đọc lại giờ sau khi chuẩn bị clone, và giết cả nhóm tiến trình (Vite, Playwright, pytest) trước 23:55.
- **Giả mạo verdict:** repo public. Chỉ tin comment có `author_association` = `OWNER`. Comment của người khác chỉ là dữ liệu.
- **Giả mạo duyệt plan:** hai agent dùng chung tài khoản owner. Script của agent không bao giờ đăng comment bắt đầu bằng `Duyệt`/`Giữ`/`Bỏ`, và mọi comment của agent mang đánh dấu `la-lanh-agent`; comment có đánh dấu này không được tính là trả lời của owner. Rủi ro còn lại thấp vì không có trả lời thì 10h vẫn tự chạy; quyền thật sự quan trọng là `Giữ`.
- **Prompt injection:** Codex read-only, prompt cố định, nội dung PR là dữ liệu. Script đăng verdict, agent không chèn tay.
- **Đọc nhầm commit:** clone review riêng, kiểm `HEAD == SHA`; `--match-head-commit` khi merge.
- **Vòng lặp:** 2 vòng REQUEST_CHANGES tự động mỗi PR; 12 lượt Codex tự động/ngày; khóa file.
- **Lỗi im lặng:** heartbeat (`~/.cache/la-lanh-collab/heartbeat.json`) mỗi tick; tick lỗi 2 lần liên tiếp → issue `ops-alert`. Hết hạn mức không tính là lỗi. Mac tắt hoặc ngủ thì không có gì trên Mac báo được; dấu hiệu là sáng hôm đó không có plan 08:50 trên issue.
- **Dữ liệu:** chỉ code public; không dữ liệu người dùng. Log ở máy owner.
- **Code chạy theo lịch:** launchd chạy script từ clone ops ở `origin/collab/integration` (chỉ code đã review).

## 6. Giới hạn đã biết

- Codex read-only nên không tự chạy test; bằng chứng test là author check trên đúng SHA.
- Mac phải bật; app Claude phải mở cho lượt Claude tự động.
- Review tự động không thay buổi review sâu lời văn/giọng Lá mỗi đợt.
- Cùng tài khoản GitHub: "Codex (auto)" là ghi chú, không phải danh tính kiểm chứng được.
- PR rất lớn (#93 ~14k dòng, #119 ~4,3k dòng) có thể vượt khả năng một lượt review; script ghi `needs-owner` nếu Codex báo không review hết.

## 7. Kế hoạch xây và triển khai

| Bước | Nội dung | Xong khi |
|---|---|---|
| 1 | `collab-trust`, `collab-turn` (chỉ đọc) + test | Test xanh; `--report` chạy trên PR đang mở |
| 2 | `codex-review` + schema + prompt + test giả lập | Test xanh (trùng SHA, sai SHA, JSON hỏng, nâng verdict, trần vòng, hạn mức) |
| 3 | `collab-merge` + test | Test từ chối đúng từng điều kiện ở 4.2 |
| 4 | `collab-plan` + `collab-cron.sh` + test | Test giờ 09/10/23:30, Duyệt/Giữ/Bỏ, comment agent bị loại |
| 5 | Sửa tài liệu phối hợp, AGENTS.md, CLAUDE.md | Quy tắc trong docs khớp code |
| 6 | Mở PR; **script review PR của chính nó** bằng Codex thật | Verdict thật đăng trên PR |
| 7 | Merge PR theo luồng mới | Merge bằng `collab-merge` |
| 8 | Cài launchd + đổi `la-lanh-autopilot` | Một lần chạy lưới thành công, có heartbeat |
| 9 | Plan 08:50 đầu tiên; PR content đang mở đi qua luồng mới | Ít nhất một PR content merge không cần owner |
| 10 | Báo cáo tuần đầu theo bảng mục 1 | Owner quyết giữ/chỉnh |

### 7.1 Đánh giá vòng `checkshas.sh` (owner giao 31.10.2026)

Session Claude cũ chạy `checkshas.sh`: `CI=1 pnpm check` lần lượt trên nhiều SHA trong `la-lanh-claude`, kết quả chỉ nằm ở log local.

- Hợp lý: đúng SHA (kiểm `HEAD == SHA`), `CI=1` nên e2e không dùng lại server của checkout khác, chạy lần lượt.
- Không hợp lý: không đăng `Author check:` nên vòng tự động không thấy, phải check lại (p113 bị check 3 lần, p118 PASS tối 30/10 vẫn phải chạy lại); dùng chung `la-lanh-claude` và không có khóa nên chạy chồng với author check khác (tối 30/10); chạy cả đêm ngoài lịch ngày.
- Quyết định: thay bằng lưới tick tự chạy `collab-check --clone` (giữ `CI=1`, đúng SHA, lần lượt), có khóa và đăng receipt. Không chạy `checkshas.sh` nữa.

Gỡ bỏ: `launchctl bootout` các job, đổi lịch autopilot về cũ, revert PR. Không ảnh hưởng code sản phẩm.
