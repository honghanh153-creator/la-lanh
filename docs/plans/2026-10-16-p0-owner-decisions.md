# P0: các điểm owner cần chốt (16/10/2026)

Tài liệu đi kèm:

- kế hoạch `2026-10-16-personalisation-variety-plan.md` (APPROVE @ 8574d72);
- US-20, US-21, US-22;
- `la-lanh-content-grammar-spec.md`, `la-lanh-personal-sky-events-spec.md`,
  `la-lanh-variety-measurement-spec.md`;
- `docs/fixtures/tarot-question-bank-v1.json`.

**Owner chốt ngày 16/10/2026: "chốt theo đề xuất"** cho A1–A12.

- A8 chọn 5 tình huống được đánh dấu **Chọn** ở mục B.
- A10 chốt hướng (Claude API hoặc OpenAI, sau khi kiểm điều khoản dùng output). Nhà cung cấp cụ thể và
  chi phí từng đợt vẫn do owner duyệt khi bắt đầu E.
- A9 vẫn chặn F cho tới khi rà luật, cập nhật consent, data map và khai báo store.

Các giá trị trong bảng dưới đây là giá trị đã chốt.

## A. Cần chốt trước bước triển khai tương ứng

| # | Quyết định | Đề xuất | Chặn bước |
|---|---|---|---|
| A1 | Ngưỡng "yếu tố riêng" theo nhóm | Có giờ + đã chọn mối quan tâm ≥ 3; có giờ, chưa chọn ≥ 2; chỉ ngày sinh + đã chọn ≥ 2; chỉ ngày sinh, chưa chọn ≥ 1 | P1 floor, G1 |
| A2 | Khoảng cách lặp câu | ≥ 90 ngày với ≥ 95% profile trong mỗi nhóm khả thi; L tối thiểu 90 | G0, G1 |
| A3 | Note giống hệt giữa hai người cùng cung cùng ngày | < 1% (cặp trùng ngày sinh và thiếu giờ báo riêng) | P1 floor |
| A4 | Giới hạn build | 200 000 tổ hợp mỗi khung × bucket; 48 bucket mỗi khung; 2 000 000 bước tìm mỗi biến thể; M = 4–8; CI ≤ 10 phút | G0 |
| A5 | Cỡ mẫu owner duyệt | Khoảng 30 tổ hợp mỗi khung (tất định, gồm tổ hợp biên), cả hai giọng | Mọi đợt nội dung |
| A6 | Bảng nhãn hành động đóng của Tarot | 30 nhãn ở US-20 | B2 |
| A7 | Quy tắc câu Tarot mơ hồ | Hỏi lại khi câu < 3 từ, hoặc không có động từ hay tình huống (hiện chỉ chặn < 8 ký tự) | B2 |
| A8 | 5 tình huống Astro mới (mục B) | Chọn 5 trong 10 | G1 |
| A9 | Danh sách "điều bạn đang quan tâm" | Học tập, công việc mới, tình cảm, gia đình, bạn bè, chăm mình, tiền bạc, một thay đổi lớn. Tránh nhãn nhạy cảm (sức khoẻ, tình trạng hôn nhân cụ thể) | F (sau rà luật) |
| A10 | Nhà cung cấp cho AI lúc soạn | (1) Anthropic Claude API; (2) OpenAI bằng tài khoản đang có cho Luna; (3) chưa dùng AI lúc soạn, chỉ viết tay. Đề xuất (1) hoặc (2), sau khi kiểm điều khoản dùng output làm nội dung. Mỗi đợt owner duyệt chi phí trước | E |
| A11 | "Hỏi Tarot lại cùng câu trong 24 giờ thì mở lại bài cũ" | Để sau B2. Nếu làm thì so bằng hash có khoá trong payload đã mã hoá | Không chặn B2 |
| A12 | Múi giờ của "ngày lịch" | Giữ `MVP_TIMEZONE = Asia/Ho_Chi_Minh`. Đổi sang múi giờ người dùng là quyết định riêng, phải bump `catalog_version` | Không chặn |

## B. Ứng viên 5 tình huống Astro mới

Không trùng 15 tình huống hiện có (`missing-context`, `too-many-open-loops`, `changed-plan`,
`comparison-loop`, `automatic-caretaking`, `decision-fatigue`, `perfect-before-start`, `group-pressure`,
`avoid-small-conflict`, `defend-old-choice`, `capacity-before-agreement`, `quick-reply`, `repair-reply`,
`specific-feedback`, `name-the-need`).

| Mã | Tình huống quan sát được | Hướng việc nhỏ | Đề xuất |
|---|---|---|---|
| `waiting-for-reply` | Cứ mở điện thoại xem người kia trả lời chưa | Đặt điện thoại xuống và làm một việc của mình trong 20 phút | **Chọn** |
| `rest-guilt` | Được nghỉ mà vẫn thấy có lỗi, mở việc ra xem | Chọn một khoảng nghỉ có giờ bắt đầu và kết thúc | **Chọn** |
| `feedback-sting` | Bị góp ý thấy nhói, muốn giải thích ngay | Ghi lại một ý đúng trong góp ý trước khi trả lời | **Chọn** |
| `new-environment` | Chỗ mới (lớp, việc, nhóm) chưa quen ai | Hỏi một người một câu cụ thể về công việc chung | **Chọn** |
| `skipped-small-win` | Xong một việc nhưng nhảy ngay sang việc khác, không ghi nhận | Viết một dòng về việc vừa xong | **Chọn** |
| `late-night-scroll` | Lướt điện thoại tới khuya dù đã mệt | Để điện thoại ngoài tầm tay trước giờ ngủ | Dự phòng |
| `small-task-pileup` | Việc nhỏ (mail, dọn bàn) dồn lại | Làm ba việc nhỏ nhất trong 15 phút | Dự phòng |
| `plan-cancel-urge` | Đã nhận lời đi chơi nhưng muốn huỷ phút cuối | Nhắn rõ: đi ngắn hơn, hay dời sang ngày khác | Dự phòng |
| `morning-rush` | Buổi sáng vội, quên điều quan trọng | Chuẩn bị một thứ cho sáng mai từ tối nay | Dự phòng |
| `spending-on-mood` | Mua món nhỏ khi mệt hoặc buồn | Chờ một ngày rồi mới quyết món không gấp | Dự phòng (chạm chủ đề tiền, cần cẩn trọng ngôn từ) |

Mỗi tình huống chọn cần: meaning brief, anchor/contrary cho lời của Lá, khung và ô theo
`la-lanh-content-grammar-spec.md`, và luật chart dẫn tới tình huống (natal và transit).

## C. Đã chốt trước đây (không mở lại)

- §8 của kế hoạch: bậc thang S1 → S3 → S2; A2 (A1 sớm); T2 (3 mức hướng nghiêng, bỏ tên tiếng Anh khỏi
  nội dung, "khi nào" đổi thành "sẵn sàng trước"); R2; thứ tự Tarot → Astro → Hợp gu; mood, phản hồi và
  nhật ký ở chặng 2, người dùng tự bật; checklist tâm lý; bản triệt để.
- Nội dung 76 câu ngày 16/10 và copy sheet Radar (đã live).
