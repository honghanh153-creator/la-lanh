# Nhìn lại vòng tự động Claude ⇄ Codex: 12.11.2026

Tác giả: Claude (lượt retro tự động 12.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-12.log`, `state/2026-11-12.json`, `collab-turn --report` (12.11 23:40), `gh pr list --state merged`, 21 comment `Review verdict` của Codex trên PR được động tới hôm nay, `queue.md` của autopilot. Mọi ngày trước đều đã có file retro.

Từ hôm nay owner đã duyệt Autopilot v2: bỏ mục tiêu 20 PR/ngày, báo theo việc có giá trị. Vì vậy bảng dưới chỉ ghi số việc thật, không ghi "/20".

## 1. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 15 | #433 (10:24) tới #440 (23:15) |
| Việc thật đã merge | **11** | xem bảng dưới |
| Việc đã lên bản chạy thật | **0** | `main` không đổi hôm nay. Integration cách `main` 797 commit |
| PR không tính | 4 | #433 (chỉ thêm test), #441 (tài liệu), #443 (công cụ vòng), #452 (CI chụp màn) |
| Lượt Codex review | 21, lỗi 0 | `state/2026-11-12.json` |
| Hàng chờ trống | **5 phút** | hôm qua 318 phút |
| PR chưa có author check ở head cuối ngày | 7 | #428, #431, #432, #448, #449, #450, #454 |

| Việc | Loại | PR |
|---|---|---|
| Tâm trạng lưu dạng mã hóa (bật dần qua hai bản phát hành) | Quyền riêng tư | #412 |
| Trang chia sẻ và trang mời công khai không bị lưu đệm, lập chỉ mục hay lộ qua referrer | Bảo mật | #438 |
| Lời mời và lời đồng ý Radar dễ hiểu (owner chốt câu) | Nội dung | #442 |
| Daily `automatic-caretaking` thành bộ | Nội dung | #426 |
| Daily `perfect-before-start` thành bộ | Nội dung | #429 |
| Daily `group-pressure` thành bộ | Nội dung | #434 |
| Daily `name-the-need` thành bộ | Nội dung | #435 |
| Daily `repair-reply` thành bộ | Nội dung | #436 |
| Daily `quick-reply` thành bộ | Nội dung | #437 |
| Daily `specific-feedback` thành bộ | Nội dung | #439 |
| Daily `avoid-small-conflict` thành bộ | Nội dung | #440 |

Các bộ Daily vẫn ở trạng thái chờ duyệt câu nên người dùng chưa thấy, kể cả sau go-live.

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 4 | #443: 2 (chế độ đọc CI vẫn chạy công cụ Python của PR trên máy; kết quả CI chưa gắn với đúng workflow `pr-check`), đã sửa ở vòng 2. #451: 2 (lô duyệt câu chữ kẹt mãi ở 200 câu đã bị từ chối; merge bằng lệnh tay không vào thông báo owner), đã sửa 22:50, chờ review lại |
| P2 trên PR bị chặn | 11 | #451 (4), #431 (3), #432 (2), #426 (1), #436 (1) |
| P2 trên PR đã APPROVE | 6 | #441 (2), #438, #442, #443, #452 (mỗi PR 1); không chặn |

15/15 PR merge đều được APPROVE; 12 ở vòng đầu, 3 ở vòng 2 (#426, #436, #443).

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| PR bị đồng bộ lại nhiều lần | 22 lượt "đã đồng bộ, check lại ở tick sau", 9 lượt chờ CI | Từ #443 (05:17), author check đọc kết quả CI. Mỗi lần integration nhận một merge, PR đang chờ bị merge integration vào rồi phải chờ CI chạy lại. #441 bị đồng bộ 5 lần trước khi merge | log tick; `collab-turn --report` |
| 7 PR chưa được check cuối ngày | tới hết ngày | Cùng nguyên nhân trên: vòng chỉ xử lý một PR mỗi nhóm mỗi tick, các PR sau cứ phải đồng bộ lại | `collab-turn --report` 23:40 |
| Preflight trượt vì body PR | 3 PR | #431 và #442 thiếu cổng G1–G10 (đã sửa body 10:50 và 15:50); #451 quá 400 dòng mã | log 03:34Z, 04:07Z, 15:52Z |
| Lỗi lint trong preflight | #428 | ruff E501 (dòng dài 102 ký tự) | log tick |
| Thiết kế spec 1b qua 7 vòng Codex | khoảng một buổi + ~60 phút owner | Mỗi vòng Codex nâng mô hình đe dọa, Claude sửa từng phát hiện mà không hỏi có cân xứng không. Owner hỏi "có đang làm quá phức tạp không?" và chọn bản đơn giản | ghi nhận của phiên owner 12.11 |

## 4. PR từ 3 vòng review trở lên

Không có PR nào. Thiết kế spec 1b (không phải PR) qua 7 vòng; nguyên nhân gốc ở mục 3. Luật mới: sau 2 vòng mà thiết kế cứ phình ra thì dừng và hỏi owner về phạm vi.

## 5. Tốt và chưa tốt

**Tốt**
- Hàng chờ trống chỉ 5 phút (hôm qua 318 phút). S21 đã làm: ưu tiên việc không đụng `copy_registry.json`, nên #412 (P1 tồn từ hôm qua) và #438 merge được trong khi các bộ Daily chờ nhau.
- 11 việc thật, trong đó 2 việc bảo vệ dữ liệu người dùng (#412, #438).
- 0 P0, 0 lỗi chạy Codex. P1 của #443 sửa trong 34 phút.
- Author check không còn chạy mã PR trên Mac (#443), nên hết cảnh "check bận" (0 lượt hôm nay, hôm qua 40).

**Chưa tốt**
- 0 việc lên bản chạy thật; khoảng cách integration → `main` tăng lên 797 commit.
- Cách mới đọc CI sinh ra vòng đồng bộ lại liên tục; 7 PR kẹt cuối ngày.
- Body PR vẫn thiếu cổng ở 2 PR, dù S22 (luôn dùng template) đã ghi từ hôm qua: luật mềm không đủ.
- Owner chỉ ra hai việc "đã quyết nhưng chưa chạy": phần Codex duyệt câu chữ (quyết 06.11) có code và test nhưng không có chỗ nào gọi, nên mọi câu vẫn chờ duyệt; `collab:metrics` chưa có.
- File giao việc của chính lượt retro này vẫn ghi "Báo %: … / 20" dù owner đã bỏ mục tiêu 20 hôm nay.

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 12.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| PR phải cập nhật nhánh rồi chờ CI lại mỗi khi base đổi | Merge queue cho cùng lợi ích như "Require branches to be up to date" nhưng không bắt tác giả cập nhật nhánh; hàng đợi tự kiểm PR với base mới nhất ngay trước khi merge | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Merge queue không dùng được ở repo tài khoản cá nhân (đã kiểm ở retro 02.11). Làm theo ý tưởng: S25 chỉ đồng bộ PR đứng đầu hàng của nhóm, ngay trước review/merge; PR phía sau giữ nguyên đến lượt |
| Code có nhưng không ai gọi | Công cụ tìm file, export và dependency không dùng, chạy trong CI | [Knip](https://knip.dev/) | S26: test "mỗi quyết định owner có chỗ gọi": danh sách lệnh trong `package.json`/tick phải được gọi ở tick hoặc scheduled task; thêm Knip là việc sau (thêm dependency) |
| Body PR thiếu cổng dù đã có template | Template chỉ điền sẵn khi tạo PR qua giao diện; công cụ tạo PR bằng lệnh phải tự đọc template | [GitHub Docs — Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) (đã kiểm 09.11) | S27: mọi lệnh mở PR của vòng gọi `gh pr create --body-file` dựng từ template; preflight giữ nguyên làm lưới cuối |

## 7. Chống AI bị "rotten" — cập nhật 12.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11–11.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Quyết định nằm trên giấy, không chạy | Codex duyệt câu chữ: có code, không có chỗ gọi; `collab:metrics` chưa có |
| Lời giao việc cũ hơn luật mới | File tác vụ retro còn "/ 20" sau khi owner bỏ mục tiêu 20 |
| Vòng review phình dần | Spec 1b: 7 vòng, thiết kế lớn dần |

**Điều học thêm:** mỗi quyết định phải có một kiểm tra máy chứng minh nó chạy (có chỗ gọi, có test tick, có số đếm thật). Khi luật đổi, mọi file giao việc phải đổi cùng lúc, và cần một kiểm tra tìm chữ cũ trong các file đó.

**Biện pháp:** S26 (kiểm có chỗ gọi); S28 (kiểm chữ cũ "20 PR", "/ 20" trong file tác vụ hẹn giờ, báo nếu còn); luật "sau 2 vòng phình thì hỏi owner" đã ghi trong bộ nhớ của Claude.

## 8. Cần owner

Không hỏi lại mục đã chốt. Mục còn mở:

1. **Đưa integration lên `main` và go-live** (797 commit). Khuyến nghị: duyệt khi owner sẵn sàng; 11 việc hôm nay chỉ tới người dùng qua bước này.
2. **Sửa file tác vụ retro**: thay dòng "Báo %: … / 20" bằng "báo số việc thật theo Autopilot v2". Khuyến nghị: đồng ý (chỉ đưa file về khớp quyết định 12.11).
3. **WIP 1 cho PR quy trình:** PR chờ owner (#354, #134) không chiếm chỗ. Khuyến nghị: đồng ý; #451 (v2) cũng đang giữ chỗ.
4. **Việc owner của Autopilot v2** (từ phiên 12.11): để Mac thức khi cắm điện; bật "Include your own updates" trên GitHub; chọn 5 người thử.
5. **#404, #388, #411** chờ duyệt câu; **#430** base `main` chỉ owner merge.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude: #451 (Autopilot v2, phạm vi khác), #354 và #134 (chờ owner). Theo WIP 1, việc AUTO quy trình vào hàng đợi autopilot.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S25 | Chỉ đồng bộ PR đứng đầu hàng của nhóm, ngay trước review/merge; không merge integration vào mọi PR chờ ở mỗi tick | GitHub merge queue | cả 5 "không" | AUTO | Hàng đợi (sau #451) |
| S26 | Test: mỗi lệnh quyết định của owner có chỗ gọi trong tick hoặc tác vụ hẹn giờ | Knip | cả 5 "không" | AUTO | Hàng đợi |
| S27 | Lệnh mở PR của vòng luôn dựng body từ template | GitHub PR template | cả 5 "không" | AUTO | Hàng đợi |
| S28 | Kiểm chữ cũ trong file tác vụ hẹn giờ, báo trong retro | quyết định 12.11 | cả 5 "không" | AUTO | Hàng đợi |
| S13, S17, S18, S19, S20, S2b, S23, S24 | Như các retro trước | — | — | AUTO | Hàng đợi |

## 10. Bước bị chặn

Không có tới lúc viết file này.
