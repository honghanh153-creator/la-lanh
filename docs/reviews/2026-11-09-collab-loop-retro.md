# Nhìn lại vòng tự động Claude ⇄ Codex: 09.11.2026

Tác giả: Claude (lượt retro tự động 09.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-09.log`, `state/2026-11-09.json`, `collab-turn --report` (09.11 23:37), `gh pr list --state merged`, comment `Review verdict` của Codex trên 20 PR được động tới hôm nay, `queue.md` của autopilot, danh sách cảnh báo Dependabot của repo.

## 1. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 19 | 10:01–16:12, thêm #371 (18:03) và #372 (22:03) |
| PR có giá trị cho người dùng | **3 / mục tiêu 20** | #362 (sửa API tổng quan khi giờ sinh gần đúng), #335 và #331 (nội dung Daily) |
| PR test | 2 | #339, #343 |
| PR tài liệu, phân loại, retro, vòng lặp | 14 | #341, #345–#348, #355–#361, #371, #372 |
| Lượt Codex review | 21, lỗi 0 | `state/2026-11-09.json` |
| PR sẵn sàng cuối ngày | 0 / 5 | `collab-turn --report` |
| Hàng chờ trống | **584 phút** (~9,7 giờ) | `collab-turn --report`; 9 lượt tick chạy không, đã báo "chạy không" |

Theo lệnh owner 09.11, chỉ PR có giá trị cho người dùng được tính vào mục tiêu 20. Hôm nay đạt 3.

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 2 (chặn merge) | #354 vòng 2: hook chặn lệnh nguy hiểm vẫn bỏ sót heredoc chạy qua `/bin/bash` và một dạng lệnh khác |
| P2 | 7 trên PR đã APPROVE + vài P2 trên #354 | #347, #348, #355, #359, #360, #361, #372 (mỗi cái 1); không chặn |

18/19 PR merge được APPROVE ngay vòng đầu. #331 cần 2 vòng (P2 câu "name-the-need.21" đảo nghĩa người giúp, đã sửa trưa nay).

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| Không có việc cho máy | 584 phút | Sau 16:12 hàng chỉ còn 2 PR vòng lặp (#371, #372); PR mở còn lại đều `needs-owner`, nháp hoặc xếp chồng | `collab-turn --report`; log từ 21:07 tới 23:28 chỉ `"done":[]` |
| Check phải chờ nhau | khoảng 16 lượt tick (mỗi lượt 10 phút) | Check chạy từng cái một (luật "checks one at a time"); tick gặp máy bận thì bỏ lượt, chờ tick sau | log: `"check":{"status":"busy","reason":"máy đang chạy check khác…"}` cho #331–#372, #155 |
| #354 dừng chờ owner | từ 12:13 | Vòng 2 vẫn còn 2 P1 trong bộ lọc lệnh shell; vòng tự động gắn `needs-owner` | verdict auto-2 @ 923259e |

## 4. PR từ 3 vòng review trở lên

Không có trong ngày. #354 đã qua 2 vòng (08.11 và 09.11), mỗi vòng Codex tìm thêm một cách viết lệnh shell mà regex bỏ sót. Đây là dấu hiệu giống #124 ngày 02.11: mỗi lần chỉ vá đúng ví dụ được nêu. Xem S14.

## 5. Tốt và chưa tốt

**Tốt**
- Review nhanh và chính xác: 18/19 APPROVE vòng đầu, 0 lỗi chạy Codex, 0 P0.
- S8 của retro 08.11 đã xong cả hai phần (#371 gộp ops-alert theo chủ đề, #372 tự đóng khi tác vụ chạy lại) — cùng ngày được giao.
- #362 sửa lỗi thật cho người dùng: phần tổng quan đi theo đúng mức dữ liệu khi giờ sinh chỉ gần đúng.

**Chưa tốt**
- 14/19 PR là tài liệu và phân loại PR cũ. Đúng loại việc owner bảo dừng tính từ 09.11. Kết quả: 3/20 PR có giá trị.
- Hàng chờ cạn từ chiều, máy đứng gần 10 giờ. Không ai đổ thêm việc nội dung hoặc bảo mật vào.
- GitHub báo **67 cảnh báo phụ thuộc** (4 nghiêm trọng, 25 cao) mỗi lần push. Đã kiểm: các gói nghiêm trọng/cao chính (certifi, cryptography, vite, shell-quote, zod, js-yaml, nanoid, postcss) **đã được nâng trên integration**. Cảnh báo vẫn còn vì GitHub chỉ quét nhánh `main`, mà `main` chưa nhận integration từ 26.10 (cách 643 commit).

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 09.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Cảnh báo bảo mật không tắt dù đã sửa | Dependabot chỉ quét nhánh mặc định: "Dependabot scans your repository's default branch" | [GitHub Docs — About Dependabot alerts](https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts) | Cảnh báo chỉ hết khi integration lên `main` (việc của owner, mục 8.1). Trước đó, retro so phiên bản trên integration để biết gói nào còn lỗi thật |
| Check bận thì bỏ lượt | Nhóm `concurrency`: lần chạy mới **chờ ở trạng thái pending** thay vì bị bỏ; `queue: max` giữ tới 100 lần chờ theo thứ tự | [GitHub Docs — Control the concurrency of workflows and jobs](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs) | S13: khi máy bận, tick ghi PR vào hàng chờ check theo thứ tự và chạy ngay khi check trước xong, không chờ 10 phút |
| Hook chặn lệnh bằng regex bị vượt mỗi vòng (#354) | Docs Claude Code: khớp lệnh Bash trong hook là "best-effort"; muốn chặn cứng thì dùng hệ thống quyền (deny rules), không dùng hook | [Claude Code docs — Hooks](https://code.claude.com/docs/en/hooks) | S14: giữ hook như lớp cảnh báo; chặn cứng bằng deny rules trong cấu hình quyền (cần owner, mục 8.2) |
| Hàng chờ cạn | Kéo việc theo hàng ưu tiên có sẵn; khi cột "sẵn sàng" dưới ngưỡng thì bổ sung từ backlog | Thực hành Kanban (giới hạn WIP + bổ sung theo ngưỡng); đã dùng ở retro 31.10 | S15: ngưỡng "PR sẵn sàng < 2" thì autopilot lấy việc từ danh sách giá trị người dùng (nội dung, bảo mật), không lấy việc phân loại |

## 7. Chống AI bị "rotten" — cập nhật 09.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và 08.11 mục 6. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Luật cũ và luật mới cùng nằm trong lời giao việc | Lời giao việc của tác vụ hẹn giờ vẫn có các bước cũ (mở PR phân loại, top-up) bên cạnh lệnh 09.11 "chỉ PR có giá trị"; 14/19 PR hôm nay là loại việc cũ |
| Vá theo ví dụ thay vì theo nguyên nhân | #354 vá đúng các lệnh Codex nêu, vòng sau Codex tìm ra lệnh khác |

**Điều học thêm:** docs Claude Code nói thẳng rằng phân tích lệnh Bash trong hook chỉ là best-effort. Luật quan trọng phải nằm ở chỗ máy thi hành chắc chắn (quyền, test), không nằm ở chữ hay regex.

**Biện pháp:** (1) khi owner ra luật mới, cập nhật luôn lời giao việc của các tác vụ hẹn giờ liên quan, xóa bước trái luật (việc của owner hoặc phiên có quyền sửa tác vụ); (2) S14.

## 8. Cần owner

1. **Đưa integration lên `main`** (643 commit, từ 26.10). Đây là cách duy nhất để 67 cảnh báo phụ thuộc của GitHub tắt; bản sửa đã có trên integration. Khuyến nghị: gộp vào bước "go-live" khi owner đồng ý.
2. **#354 (hook chặn lệnh nguy hiểm).** Khuyến nghị: đồng ý chuyển phần "chặn cứng" sang deny rules của cấu hình quyền, hook chỉ cảnh báo; như vậy không cần thêm vòng vá regex.
3. **Lời giao việc của tác vụ hẹn giờ** (retro, autopilot) còn bước mở PR phân loại/top-up trái lệnh 09.11. Khuyến nghị: cho phép xóa các bước đó.
4. Còn từ 08.11: 30 issue `ops-alert` đang mở (khuyến nghị đóng một lần các cái đã khỏi); S10 cổng hard-zero với câu mơ hồ.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude là #354 (đang chờ owner), nên theo WIP 1 các việc AUTO quy trình được ghi vào hàng đợi autopilot cho ngày mai.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S15 | Khi PR sẵn sàng < 2, autopilot lấy việc có giá trị cho người dùng (nội dung pending, sửa lỗi, bảo mật) thay vì phân loại PR cũ | Kanban bổ sung theo ngưỡng; lệnh owner 09.11 | cả 5 "không" | AUTO | Hàng đợi 10.11 |
| S16 | So từng cảnh báo Dependabot còn lại (brace-expansion, source-map-js, browserslist, tinypool) với lockfile integration; gói nào còn lỗi trên integration thì mở PR nâng phiên bản nhỏ (giá trị bảo mật) | GitHub Docs Dependabot | cả 5 "không"; mở lại được | AUTO | Hàng đợi 10.11 |
| S13 | Tick gặp máy bận thì xếp PR vào hàng check theo thứ tự, chạy ngay khi check trước xong | GitHub Actions `concurrency` (pending, `queue: max`) | cả 5 "không" | AUTO | Hàng đợi (sau #354, WIP 1) |
| S14 | #354: chặn cứng bằng deny rules, hook chỉ cảnh báo | Claude Code docs Hooks | đổi cấu hình quyền của agent | NEEDS OWNER | Mục 8.2 |

## 10. Bước bị chặn

Không có tới lúc viết file này.
