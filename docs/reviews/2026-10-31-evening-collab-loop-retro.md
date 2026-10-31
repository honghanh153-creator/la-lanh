# Nhìn lại vòng tự động: chiều tối 31.10.2026 (17:00 → 23:30)

Phần tiếp theo của `2026-10-31-collab-loop-retro.md` (merge lúc 18:49). Tác giả: Claude. Người review: Codex
qua vòng tự động. Giờ Việt Nam; chỉ metadata kỹ thuật.

## 1. Kết quả

| Chỉ số | Giá trị |
|---|---|
| PR merge trong ngày 31.10 | 11 lúc 22:00 (#118, #120, #137, #139, #141, #142, #144, #145, #146, #148, #149); dự kiến 15 trước 23:30 |
| Merge riêng buổi tối | #148 18:49 · #139 19:39 · #145 19:55 · #149 20:29 · #144 21:39 · #146 21:57 |
| Lượt Codex | 20 dùng / trần 40 (owner nâng từ 12 → 24 → 40 trong chat) |
| Thời gian một author check | ~35 phút trước 19:35, ~10–17 phút sau khi sửa `ProcessType` |
| Thời gian một PR trọn vòng (check → review → merge) | ~18 phút trung bình, gồm cả thời gian chờ tick |

Nhóm content của plan xong trong tối nay (#139, #144, #146; #147, #150, #151 đang chạy). Privacy
(#112, #113, #116, #117) và 5 PR quy trình để draft chuyển sang sáng 01.11.

## 2. Chỗ kẹt và lỗi

| # | Sự cố | Mất | Nguyên nhân gốc | Đã sửa / đề xuất |
|---|---|---|---|---|
| K15 | Push một file test không parse được (#157) | 1 commit sửa | Claude ghép commit vào sau lệnh test mà không cho test chặn commit | Luôn `test && commit`; đọc kết quả trước khi push |
| K16 | Author check do tick chạy chậm gấp ~5 lần | ~25 phút mỗi PR, cả buổi chiều | Job launchd đặt `ProcessType = Background` → lõi tiết kiệm điện, I/O bị giới hạn | Đổi `Standard` trên máy (19:35) và file mẫu (#155) |
| K17 | Hết 12 lượt Codex lúc 19:35 | review dừng | Nhiều vòng cho chính các PR sửa vòng tự động | Owner nâng trần; plan sáng ước tính trần +20%, `Duyệt` xác nhận (#157) |
| K18 | PR quy trình xung đột nhau (#149, #157) | 2 lượt check thêm | Nhiều PR cùng sửa `collab-turn.mjs` và file test cùng lúc | Gom thay đổi vòng tự động thành ít PR hơn mỗi ngày; xếp nối tiếp thay vì song song |
| K19 | Script review của Claude thử merge lại liên tục khi bị từ chối | ~10 giây gọi API dồn dập | Không có danh sách bỏ qua cho merge bị từ chối | Bỏ qua PR đã bị từ chối trong cùng lượt chạy |
| K20 | PR quy trình của chính Claude chen trước content | ~1 giờ máy | Luật "ops đi trước" áp cho cả PR tài liệu không gấp | Chuyển 5 PR sang draft tới sáng; đề xuất D12 |
| K21 | Autopilot lại kẹt xin quyền (18:48) | lượt Claude theo lịch không chạy | Quyền chỉ được cấp một lần, chưa "Always allow" | Owner mở lại; xác nhận ở lượt sau |
| K22 | #145 chờ owner 17:49 → 19:24 trong khi Claude không hoạt động | ~1,5 giờ | Session của Claude chỉ chạy khi có tin nhắn hoặc sự kiện nền | Claude giữ bộ theo dõi `claude-fix` suốt buổi; owner cho Claude tự quyết từ vòng 3 |
| K23 | 1 lượt check phí cho #154 | ~15 phút | Chuyển draft sau khi tick đã nhận | Quyết định thứ tự trước khi mở PR, không sau |

## 3. Quy tắc mới trong buổi tối (owner)

- Trần Codex linh hoạt nhưng owner xác nhận; ước tính từ sáng +20% (#157).
- Từ vòng review tự động thứ 3: Claude tự quyết theo checklist; lỗi nghiêm trọng/ảnh hưởng người dùng thì sửa tiếp (#154, plan §2 mục 10).
- Cải thiện trải nghiệm người dùng qua được Q1–Q5 thì làm luôn (#145 checklist).
- Quy trình phát triển sản phẩm: research trên GitHub trước, mức S/M/L, cổng G1–G10 (#156).
- Video AIOS: rà "thối" hằng tuần; đã dọn 5 quy tắc cũ (memory, hàng đợi autopilot).

## 4. Đề xuất cho Codex đánh giá

| # | Đề xuất | Lợi ích | Rủi ro |
|---|---|---|---|
| D6 | PR chỉ đổi tài liệu chạy bộ check rút gọn (lint tài liệu, link, content gate liên quan) | Tiết kiệm 10–15 phút mỗi PR tài liệu | Phải định nghĩa chặt "chỉ tài liệu"; code trong `docs/` vẫn chạy đủ |
| D11 | Tick chạy liên tiếp khi còn việc cho máy, thay vì chờ lượt 10 phút kế tiếp | Bỏ khoảng chờ 0–10 phút giữa các PR (~20–30% thời gian) | Một tick dài hơn; khoá và hạn 23:55 đã có |
| D12 | Luật "ops đi trước" chỉ áp cho PR sửa lỗi đang làm kẹt vòng; PR quy trình/tài liệu xếp sau nhóm sản phẩm đang chạy | Không chen trước plan của owner (K20) | Phải gắn nhãn đúng (`ops:blocking` hay tương tự) |
| D13 | Mỗi tối chỉ một PR gom các sửa đổi script vòng tự động | Giảm xung đột (K18) và số lượt review | PR to hơn, nhưng cùng một khu vực |

## 5. Sáng 01.11

1. Trước 08:50: bỏ draft #157 (ước tính trần) để plan sáng có ước tính; nếu chưa merge kịp, Claude ghi ước tính lên plan.
2. Bỏ draft #154, #155, #156, #160; privacy #112 → #113 → #116 → #117.
3. Kiểm lượt autopilot đầu tiên chạy không cần xin quyền.
