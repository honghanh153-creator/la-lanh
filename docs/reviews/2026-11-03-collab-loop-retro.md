# Nhìn lại vòng tự động Claude ⇄ Codex: 01–03.11.2026

Tác giả: Claude (lượt retro tự động 03.11, 21:43). Người review: Codex, qua vòng tự động.
Báo cáo gộp ba ngày: lượt retro 01.11 và 02.11 không chạy (kẹt chờ quyền, xem K30), nên không có file riêng.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-0{1,2,3}.log`, `state/2026-11-0{1,2,3}.json`, `collab-turn --report`, `gh pr list --state merged`, comment `Review verdict` của Codex, `queue.md` của autopilot.

## 1. Kết quả theo ngày

| Ngày | PR merge vào `collab/integration` | Lượt Codex | APPROVE / REQUEST_CHANGES | P0 | P1 chặn | P2 chặn | P2 không chặn |
|---|---|---|---|---|---|---|---|
| 01.11 | 8 | 23 | 9 / 14 | 0 | 6 | 17 | 5 |
| 02.11 | 7 | 12 (chạm trần 12) | 7 / 5 | 0 | 4 | 2 | 6 |
| 03.11 (tới 21:43) | 17 | 24 | 17 / 7 | 1 | 6 | 4 | 14 |

PR đã merge:

- **01.11:** #113 kế hoạch sửa ngày sinh, #122 + #123 US-23 U1/U2, #152 checklist Tarot người thật, #116 đánh giá P09/P10, #150 giờ sinh khoảng (E1), #162 CI `pr-check` (gói A phần 1), #93 hồ sơ 5 game.
- **02.11:** #124 US-23 U3, #125 + #126 US-24 spec và API (flag tắt), #108 game lab 14, #165 kế hoạch Nơi bình yên, #166 sửa K24/K25, #171 cam kết 6–8 PR/ngày.
- **03.11:** #172 Alembic một head, #181 `/metrics` trả 404, #174 Dependabot, #175 CodeQL, #177 kế hoạch Daily v2, #186 watchdog, #182 Jyotish hết rơi về note cũ, #184 + #178 sự kiện bầu trời Daily v2, #191 fixture ngày tổng hợp riêng, #179 thước đo ngôn ngữ dễ hiểu, #183 + #185 sửa giờ sinh, #117 tải dữ liệu của tôi (P09), #173 luật hoàn tiền 2 giờ, #192 12 nhà theo bộ ý nghĩa, #197 cam kết 16–20 PR và trần 32 lượt Codex.

Ngày 03.11 là ngày nhiều PR nhất từ khi có vòng tự động (17), và **không có lượt merge nào bị từ chối vì xung đột** (01.11: 14 lần, 02.11: 21 lần).

## 2. Thời gian mất và nguyên nhân

| # | Ngày, giờ | Sự cố | Mất | Nguyên nhân gốc | Trạng thái |
|---|---|---|---|---|---|
| K24a | 01.11 16:14–17:25 | #150 đã APPROVE nhưng xung đột, tick thử merge 7 lần | ~1 giờ 10 | Lượt của PR đã APPROVE luôn là "merge", kể cả khi GitHub báo `CONFLICTING`; nhóm nội dung đứng yên | Sửa ở #166 (02.11) |
| K24b | 01.11 21:57–23:26 | #117 như trên, 7 lần | ~1 giờ 30 | Cùng lỗi | Sửa ở #166 |
| **K24c** | **02.11 10:09–13:42** | #117 bị từ chối merge 21 lần liên tiếp; nhóm feature không được chạy | **~3 giờ 30** | Cùng lỗi. **K24 đã được ghi vào hàng đợi tối 01.11 nhưng không ai sửa trước lượt sáng 02.11**: hàng đợi ghi "gộp vào PR vòng tự động hằng tuần (WIP ≤1)" | #166 merge 18:01; 03.11 không còn lần từ chối nào |
| K25 | 02.11 13:42 | Re-review #117 sau khi merge integration đọc cả file của integration, báo `complete=false` | 1 vòng review + ~1 ngày chờ | Phạm vi re-review lấy theo diff integration, không theo file của PR | Sửa ở #166 |
| K26 | 02.11 18:23–20:34 | Tick chạy nhưng không có PR nào cho máy | ~2 giờ | Mọi PR còn lại chờ Claude sửa hoặc chờ owner; Claude không bổ sung PR | **Chưa sửa** (S1) |
| K27 | 02.11 21:24 → 03.11 10:06 | #172, #174, #175 đã check PASS nhưng chờ review qua đêm | 3 PR sang ngày sau | Chạm trần 12 lượt Codex/ngày lúc 21:24 | Owner nâng trần lên 32 (#197) |
| K28 | 02.11 17:07, 20:44–21:04 | Author check báo "máy bận" 4 lần | ~40 phút | Có `pytest` khác đang chạy cùng lúc (lặp lại K11 ngày 31.10) | Khóa `check.lock` đã chặn đúng; còn phải giữ việc nhẹ thật sự nhẹ |
| K29 | 03.11 12:46–15:37 | #179 có **P0 privacy** (chi tiết giữ riêng), thêm 1 lần check FAIL | ~3 giờ cho một PR | Subagent viết fixture không theo luật "chỉ dữ liệu tổng hợp" | Đã sửa trước khi merge; kiểm tra cứng đang ở #198 |
| K30 | 26.10 → 03.11 | Autopilot (từ 31.10), kiểm tra server (từ 26.10) và retro 01–02.11 kẹt chờ quyền, **owner tự phát hiện** | nhiều ngày | Tác vụ hẹn giờ dừng ở hộp thoại quyền, không ai báo | Watchdog #186 (merge 12:23); đã mở #193 (14:42) và #196 (20:33) |
| K31 | 03.11 18:29–20:43 | Lại không có PR cho máy; không có tick 19:30–20:33 | ~2 giờ 15 | #189 chờ Claude sửa từ 16:33 tới 21:00; PR mới chỉ mở sau 20:58. Khoảng không có tick: chưa rõ (có thể máy ngủ) | **Chưa sửa** (S1) |

Mỗi sáng tick chờ cổng plan khoảng 1 giờ (08:50–10:00). Đây là thiết kế, không tính là mất.

## 3. PR cần từ 3 vòng review trở lên

| PR | Số vòng (01–03.11) | Diễn biến | Nguyên nhân gốc |
|---|---|---|---|
| #124 US-23 U3 | 7 | Vòng 1–6 mỗi vòng 1–3 P2 chặn (một lần có P1), mỗi lần một đường đọc dữ liệu khác | **Mỗi bản sửa chỉ đóng đúng phát hiện được nêu.** Chỉ tới vòng 7 Claude mới rà mọi đường đọc cùng lúc, và Codex APPROVE ngay |
| #117 tải dữ liệu (P09) | 7 | Vòng 1–2 có P1 thật; vòng 3–4 cần owner; APPROVE 21:47 01.11; rồi kẹt K24 28 lần, K25 một vòng; merge 17:06 03.11 | PR lớn sống lâu (mở trước 30.10) nên càng để lâu càng xung đột; hai lỗi của vòng tự động (K24, K25) cộng dồn |
| #150 giờ sinh khoảng | 4 | Hai vòng cùng một P1 (cần owner), APPROVE, kẹt K24, review lại sau khi gỡ xung đột | Một P1 cần owner quyết; sau đó K24 |

## 4. Tốt và chưa tốt

**Tốt (có bằng chứng):**
- #166 sửa K24/K25 có hiệu lực: 03.11 không còn lượt merge nào bị từ chối vì xung đột.
- 03.11 merge 17 PR, xong cam kết 6–8 PR từ giữa chiều.
- Codex chặn được P0 privacy ở #179 và các P1 thật ở #126, #127, #166, #178, #186, #198 trước khi merge.
- Watchdog #186 chạy đúng: tự mở ops-alert #193, #196 cho tác vụ kẹt, không cần owner nhắc.
- Một chu kỳ check → review → merge khi máy rảnh vẫn khoảng 20 phút.

**Chưa tốt:**
- Một lỗi làm vòng đứng (K24) được ghi lại rồi để qua đêm vì quy tắc WIP 1, mất 3 giờ 30 sáng hôm sau.
- Hai buổi tối liền (K26, K31) vòng chạy không, mỗi lần khoảng 2 giờ.
- Owner là người phát hiện tác vụ hẹn giờ kẹt nhiều ngày (K30).
- Sửa theo từng phát hiện thay vì theo cả lớp lỗi (#124).
- Việc trong hàng đợi bị bỏ quên: "sáng 01.11 gỡ draft #154, #155, #156, #160" chưa làm; 7 PR ops nháp vẫn mở từ 31.10.

## 5. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 03.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| PR đã duyệt bị xung đột / tụt sau nhánh gốc (K24, #117) | Merge queue của GitHub | [GitHub Docs — merge queue](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue) | **Không dùng được**: chỉ có cho repo thuộc organization; repo của mình thuộc tài khoản cá nhân (`owner.type = User`, đã kiểm). Cần chuyển repo sang organization, là việc của owner |
| | Bot tự cập nhật nhánh khi tụt sau base; khi xung đột thì bình luận và gỡ nhãn automerge, không thử lại mãi | [Kodiak config](https://kodiakhq.com/docs/config-reference) (`update.always`, `merge.notify_on_conflict`) | K24 đã làm phần "xung đột → giao Claude". Còn thiếu phần "tụt sau base thì tự cập nhật" (S3) |
| | API cập nhật nhánh có khóa SHA | [REST — update a pull request branch](https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request-branch) (`expected_head_sha`) | Dùng cho S3: chỉ cập nhật khi head đúng SHA đã duyệt, không force-push |
| Nhiều vòng review (#124) | PR nhỏ, một thay đổi tự đứng được; tách refactor khỏi sửa lỗi | [Google eng-practices — Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html) | Đã có (PR nhỏ). Bổ sung: khi sửa, sửa cả lớp lỗi (S2) |
| | Nhận xét review lặp lại → biến thành test/lint hoặc hook bắt buộc | [Claude Code best practices](https://code.claude.com/docs/en/best-practices) (dòng nhấn mạnh mãi vẫn bị bỏ qua "belongs in a hook") | S2: vòng ≥2 phải có bảng "mọi chỗ cùng lớp" + test chung |
| Tác vụ kẹt không ai báo (K30) | Kiểm tra quyết định cứng (hook, deny rule, CI) thay cho lời dặn | Như trên ("If something has to happen every time, make it a hook…") | Đã có watchdog beat #186; S1 mở rộng cho "vòng chạy không" |
| Dữ liệu nhạy cảm vào repo public (K29) | Viết lại lịch sử chưa đủ: commit cũ vẫn xem được qua SHA, `refs/pull/*`; phải nhờ GitHub Support dọn cache và chạy GC | [GitHub Docs — removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) | Owner gửi yêu cầu Support (mục 7). Kiểm tra cứng trước push ở #198 |

## 6. Chống AI bị "rotten"

Owner hỏi 02.11: làm sao để AI không bị "thối" dần.

### 6.1 Triệu chứng đã thấy ở đây

| Triệu chứng | Bằng chứng |
|---|---|
| Quy tắc chồng nhau làm việc gấp bị hoãn | K24 ghi "gộp vào PR hằng tuần (WIP ≤1)" trong khi memory nói "lỗi vòng phải sửa trước sáng hôm sau" → mất 3 giờ 30 |
| Hàng đợi cũ không ai dọn | Đầu `queue.md` vẫn ghi SHA integration và bảng PR của 29.10; mục "gỡ draft sáng 01.11" chưa làm |
| Luật mềm bị quên khi giao việc | Subagent của #179 không theo luật "chỉ dữ liệu tổng hợp" (P0) |
| Session dài đọc dữ liệu cũ | Lỗi đọc nhầm ngày UTC (K13, 31.10) — cùng loại với rủi ro khi session kéo dài nhiều giờ |
| Không có ai kiểm tra tác vụ hẹn giờ | K30: kẹt nhiều ngày |

File hướng dẫn **không** phải nguyên nhân chính: `CLAUDE.md` 13 dòng, `AGENTS.md` 34 dòng (3,7 KB), `MEMORY.md` 29 dòng — đều dưới ngưỡng khuyến nghị.

### 6.2 Điều học được (nguồn chính, kiểm tra 03.11.2026)

| Bài học | Nguồn |
|---|---|
| "Context rot": càng nhiều token trong ngữ cảnh, mô hình nhớ càng kém. Cách chống: tóm tắt/compact, ghi chú có cấu trúc ra ngoài (to-do, NOTES), subagent làm việc trong ngữ cảnh sạch và trả về tóm tắt ngắn, chỉ giữ chỉ dẫn ít mà đắt | [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (29.09.2025) |
| `CLAUDE.md` nên dưới 200 dòng; hai chỉ dẫn mâu thuẫn thì Claude có thể chọn bừa một; rà định kỳ để bỏ chỗ cũ/mâu thuẫn; `MEMORY.md` chỉ nạp 200 dòng hoặc 25 KB đầu | [Claude Code docs — memory](https://code.claude.com/docs/en/memory) |
| Luật phải luôn đúng thì đặt vào hook/deny rule/CI; `CLAUDE.md` chỉ là hướng dẫn | [Claude Code best practices](https://code.claude.com/docs/en/best-practices) |
| `AGENTS.md` là "tài liệu sống"; file gần thư mục đang sửa được ưu tiên | [agents.md](https://agents.md/) |
| Codex ghép các `AGENTS.md` từ gốc xuống, dừng khi đủ 32 KiB (`project_doc_max_bytes`); phần vượt bị cắt | [OpenAI Codex — AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |
| Copilot: hướng dẫn repo "không dài quá 2 trang", không theo từng việc; hướng dẫn theo đường dẫn để trong `.github/instructions` | [GitHub Docs — repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions) |

### 6.3 Biện pháp cụ thể

1. **Mỗi sự cố kết thúc bằng một kiểm tra cứng** (đã là quy tắc 03.11): watchdog #186, kiểm tra dữ liệu riêng tư #198, S1 cho "vòng chạy không".
2. **Kiểm tra kích thước file hướng dẫn trong `pnpm collab:test`** (S5): `CLAUDE.md` ≤ 200 dòng, tổng `AGENTS.md` ≤ 32 KiB, để Codex không bị cắt mất luật.
3. **Dọn `queue.md` ngay hôm nay** (đã làm, mục 7): phần lịch sử 29–31.10 chuyển sang file lưu trữ, chỉ giữ việc còn mở.
4. **Rà "thối" hằng tuần** (D8 ngày 31.10) vẫn giữ: so memory, `queue.md`, SKILL của tác vụ hẹn giờ với plan hiện hành.
5. **Mỗi việc một ngữ cảnh mới**: tác vụ hẹn giờ đã chạy session riêng; việc dò/rà nhiều file giao subagent, brief luôn có câu "chỉ dữ liệu tổng hợp".

## 7. Giải pháp, xếp theo tác động

Đang có PR quy trình mở của Claude (#198, khác phạm vi), nên theo luật WIP 1 các việc AUTO được ghi vào hàng đợi autopilot để làm ngay sau khi #198 merge.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S1 | Tick thấy ≥3 lượt liền không có PR cho máy (30 phút) → báo Claude bổ sung PR từ backlog và ghi ops-alert nếu kéo dài 1 giờ | Kiểm tra cứng thay lời dặn; watchdog #186 | cả 5 "không" | AUTO | Hàng đợi (sau #198) |
| S2 | Từ vòng review thứ 2: bản sửa phải kèm bảng "mọi chỗ cùng lớp lỗi" (tìm bằng grep) và một test chung; prompt Codex yêu cầu nêu mọi chỗ cùng lớp | Small CLs; review lặp → test | cả 5 "không" | AUTO | Hàng đợi |
| S3 | PR đã APPROVE mà tụt sau `collab/integration` và không xung đột → tick tự cập nhật nhánh bằng API `update-branch` với `expected_head_sha`, rồi review lại phần PR (K25) | Kodiak `update.always`; REST update-branch | cả 5 "không" | AUTO | Hàng đợi |
| S4 | Lỗi làm vòng đứng được sửa ngay trong đêm, không chờ WIP 1 | Bài học K24c | Đổi luật WIP 1 của owner | NEEDS OWNER | Xem dưới |
| S5 | `collab:test` kiểm kích thước `CLAUDE.md`/`AGENTS.md` | Claude Code memory docs; Codex 32 KiB | cả 5 "không" | AUTO | Hàng đợi |
| S6 | Dọn `queue.md`: chuyển lịch sử 29–31.10 sang file lưu trữ cạnh nó | Rà file định kỳ | cả 5 "không"; không đổi luật | AUTO (local) | **Đã làm** |
| S7 | Sửa 4 phát hiện của Codex ở #198 (2 P1) | — | — | AUTO | Đã có trong vòng (`claude-fix`) |

## 8. Cần owner

1. **GitHub Support dọn commit cũ của #179.** Khuyến nghị: gửi yêu cầu (repo, số PR, commit đầu tiên bị đổi). Claude soạn nội dung riêng, không đăng public.
2. **Hai tác vụ hẹn giờ đang kẹt** (#193 autopilot, #196 kiểm tra server). Khuyến nghị: mở Claude → Scheduled, dừng lượt treo; sau đó cho phép sẵn các lệnh chỉ đọc mà tác vụ dùng để không kẹt lại.
3. **S4: ngoại lệ WIP 1 cho lỗi làm vòng đứng.** Khuyến nghị: đồng ý.
4. **Merge queue.** Chỉ có khi chuyển repo sang organization. Khuyến nghị: chưa chuyển; S3 đủ cho quy mô hiện nay.

## 9. Bước bị chặn

Không có tới lúc viết file này.
