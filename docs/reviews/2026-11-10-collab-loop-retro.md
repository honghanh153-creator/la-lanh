# Nhìn lại vòng tự động Claude ⇄ Codex: 10.11.2026

Tác giả: Claude (lượt retro tự động 10.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-10.log`, `state/2026-11-10.json`, `collab-turn --report` (10.11 23:40), `gh pr list --state merged`, comment `Review verdict` của Codex trên 22 PR được động tới hôm nay, `queue.md` của autopilot.

## 1. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 18 | #374 (10:10) tới #402 (17:55) |
| PR có giá trị cho người dùng | **16** | nội dung Daily, sửa lỗi web/API, 3 PR quyền riêng tư (#392, #394, #395) |
| Việc thật (cách đếm từ 11.11) | **khoảng 15 / 20** | #380 và #382 cùng một nguyên nhân (không thử lại khi máy chủ từ chối nội dung) nên tính một việc |
| Việc đã lên bản chạy thật | **0** | `main` chưa nhận integration từ 26.10 (nay cách 692 commit) |
| PR không tính | 2 | #374 (retro 09.11), #376 (vòng lặp) |
| Lượt Codex review | 22, lỗi 0 | `state/2026-11-10.json` |
| PR sẵn sàng cuối ngày | 2 / 5 | `collab-turn --report` |
| Hàng chờ trống | 410 phút (~6,8 giờ) | `collab-turn --report`; hôm qua 584 phút |

So với 09.11 (3 PR có giá trị), hôm nay tăng lên 16. Việc S15 của retro 09.11 (lấy việc có giá trị khi hàng chờ thiếu) đã chạy đúng.

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 1 (chặn) | #407: câu theo bộ mới làm đổi nội dung Daily nhưng "dấu vân tay" nội dung không đổi, nên bản lưu cũ có thể được dùng lại |
| P2 trên PR bị chặn | 6 | #404 (2 vòng: 2 rồi 3), #406 (1), #407 (1) |
| P2 trên PR đã APPROVE | khoảng 15 | rải rác ở #378, #379, #386 (3 mỗi cái), #374, #380, #382, #394, #395, #396 (1 mỗi cái); không chặn |

18/18 PR merge được APPROVE ngay vòng đầu.

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| Không có việc cho máy | 410 phút | 10:13–12:14 sau #376 chưa có PR mới; 18:14–19:45 và 21:11–21:41 hàng chỉ còn PR chờ owner hoặc đang sửa | log `"done":[]` liên tiếp; `collab-turn --report` |
| Check phải chờ nhau | 25 lượt tick (mỗi lượt 10 phút) | Check chạy từng cái; tick gặp máy bận thì bỏ lượt (S13 chưa làm) | log `"check":{"status":"busy"…}` cho #374–#406 |
| Review dài | ~66 phút (#404), ~40 phút (#407) | Review vòng 2 của #404 và review #407 chạy lâu, tick chờ | log 19:55→21:01, 22:42→23:21 |
| Lỗi merge giả | 1 lượt tick | 13:05 GitHub trả "Merge already in progress" cho #380; thực ra merge đang chạy và đã xong 13:05:56. Vòng lặp ghi là lỗi | log 06:05:51Z |
| Hai phiên làm trùng một việc | ~2 giờ (19:48–21:55) | Hai phiên Claude cùng viết lại `changed-plan`; PR #406 lẫn câu của hai bên, phải chuyển nháp rồi gỡ | `queue.md` mục 19:48–21:55. Chưa rõ vì sao hai phiên chạy cùng lúc (file beat của autopilot chỉ giữ lượt mới nhất, nên không kiểm lại được) |

## 4. PR từ 3 vòng review trở lên

Không có. #404 đã 2 vòng và đang chờ owner. Vòng 2 Codex nói rõ: lần sửa trước "chưa kê hết các chỗ cùng loại" (câu hành động giả định người nhận cụ thể ở các tiêu đề dòng 2274, 2304, 2352). Đây vẫn là lỗi của #124 (02.11): luật S2 (bảng "mọi chỗ cùng lớp" từ vòng 2) đã có nhưng lần sửa này không làm đủ.

## 5. Tốt và chưa tốt

**Tốt**
- 16 PR có giá trị, gấp 5 lần hôm qua; 3 PR bảo vệ dữ liệu người dùng (xóa dữ liệu xóa luôn bản trên máy, giới hạn tần suất API, Daily v2 không gửi dữ liệu qua LLM).
- 18/18 APPROVE vòng đầu, 0 lỗi chạy Codex, 0 P0.
- S16 (cảnh báo Dependabot) đã kiểm xong, không cần PR.

**Chưa tốt**
- 0 việc lên bản chạy thật: mọi việc vẫn nằm trên integration.
- Hai phiên làm trùng một tình huống Daily (#406), mất khoảng 2 giờ.
- #404 lặp lại kiểu "sửa đúng chỗ được nêu" dù đã có luật S2.
- Check bận vẫn bỏ lượt 25 lần (S13 còn trong hàng đợi vì WIP 1 bị #354 giữ).

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 10.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Hai phiên làm trùng một việc | Mỗi phiên chạy song song có một worktree riêng trên nhánh riêng để "the edits" không va nhau | [Claude Code docs — Common workflows, Run parallel sessions with worktrees](https://code.claude.com/docs/en/common-workflows) | S17: trước khi nhận một việc, phiên ghi "đã nhận" (khóa theo tên việc) và kiểm nhánh `agent/claude/<slug>` đã có trên origin hay chưa; có rồi thì bỏ qua |
| Lỗi "Merge already in progress" | API merge trả 409 khi "another merge request is already pending" — tức merge đang chạy, không phải thất bại | [GitHub REST — Merge a pull request](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request) | S18: tick coi lỗi này là "đang merge", lượt sau kiểm lại trạng thái, không ghi lỗi |
| Check bận thì bỏ lượt | `concurrency` cho lần chạy mới chờ ở trạng thái pending thay vì bị bỏ | [GitHub Docs — concurrency](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs) (đã kiểm 09.11) | S13 giữ nguyên, vẫn trong hàng đợi |
| Sửa theo ví dụ (#404) | Đã học 03.11: sửa cả lớp lỗi, kèm test chung | retro 03.11 mục S2 | Không cần thêm nguồn; cần làm đúng luật đã có (xem mục 7) |

## 7. Chống AI bị "rotten" — cập nhật 10.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Luật có nhưng không được làm theo | #404 vòng 2: luật S2 (bảng "mọi chỗ cùng lớp") nằm trong prompt autopilot nhưng lần sửa vẫn bỏ sót 3 tiêu đề cùng loại |
| Hai phiên không thấy việc của nhau | #406: trạng thái "ai đang làm gì" chỉ nằm trong ngữ cảnh từng phiên, không nằm ở chỗ chung |

**Điều học thêm:** luật bằng chữ dễ bị bỏ qua khi phiên dài; trạng thái dùng chung phải nằm ngoài ngữ cảnh của phiên (nhánh trên origin, file khóa), giống cách docs Claude Code tách mỗi phiên vào một worktree.

**Biện pháp:** S17 (khóa nhận việc); với S2, đưa kiểm "mọi chỗ cùng lớp" thành bước máy làm (grep + test chung) trong lần sửa vòng 2, không chỉ là câu nhắc.

## 8. Cần owner

Các mục còn mở từ trước, không hỏi lại mục đã chốt:

1. **Đưa integration lên `main` và go-live** (692 commit). Khuyến nghị: duyệt khi owner sẵn sàng; đây là cách duy nhất để 16 việc hôm nay tới tay người dùng.
2. **#404 và #388** gắn `needs-owner` vì có câu mới cho người dùng. Khuyến nghị: duyệt câu ở hai PR này cùng lượt duyệt copy cuối.
3. **#354**: chuyển phần chặn cứng sang deny rules, hook chỉ cảnh báo (như 09.11). Khi #354 xong thì WIP 1 được giải phóng cho S13, S17, S18.
4. Lời giao việc của tác vụ hẹn giờ còn bước cũ (09.11 mục 8.3) — vẫn mở.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude là #354 (chờ owner), nên theo WIP 1 các việc AUTO quy trình được ghi vào hàng đợi autopilot.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S17 | Khóa nhận việc: trước khi top-up, kiểm nhánh `agent/claude/<slug>` trên origin + file khóa theo slug trong `~/.cache/la-lanh-collab`; có rồi thì chọn việc khác | Claude Code docs — worktrees | cả 5 "không"; chỉ đổi script/prompt cục bộ | AUTO | Hàng đợi (sau #354) |
| S18 | Tick coi "Merge already in progress" là đang merge, lượt sau kiểm lại | GitHub REST merge (409 pending) | cả 5 "không" | AUTO | Hàng đợi (sau #354) |
| S2b | Lần sửa vòng 2 chạy bước kê "mọi chỗ cùng lớp" bằng máy và ghi kết quả vào reply | retro 03.11 S2 | cả 5 "không" | AUTO | Hàng đợi |
| S13 | Check bận thì xếp hàng, không bỏ lượt | GitHub Actions concurrency | cả 5 "không" | AUTO | Hàng đợi (từ 09.11) |

## 10. Bước bị chặn

Không có tới lúc viết file này.
