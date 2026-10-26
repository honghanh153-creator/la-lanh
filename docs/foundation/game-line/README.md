# Dòng game Lá Lành — mục lục và nguyên tắc chung

> Trạng thái: **bản nháp tài liệu, giai đoạn 3 (game) chưa bắt đầu.** Theo kế hoạch owner ngày 23/10/2026 ([`docs/plans/2026-10-23-privacy-content-game-plan.md`](../../plans/2026-10-23-privacy-content-game-plan.md)), thứ tự là riêng tư → nội dung → game. Bộ tài liệu này chỉ là chuẩn bị, không đụng runtime. Không trò nào được dựng trước khi giai đoạn 1 và 2 đạt tiêu chí thoát.

## Năm trò đã chốt (owner, 26/10/2026)

| Trò | Hook | Hình thức | Nhà | PRD | SRS | User story |
|---|---|---|---|---|---|---|
| **Hết Cứu %** | "Mỗi tuần một sự kiện bựa. Bạn khai bao nhiêu phần trăm, cả hội đoán bao nhiêu." | Nhóm kín 4–12 người, thả thứ Hai, lật tối thứ Sáu | Lá Úp *(tên chờ owner)* | [PRD](het-cuu-phan-tram-prd.md) | [SRS](het-cuu-phan-tram-srs.md) | G10–G16 (khung G10–G19) |
| **Tam Sao Thất Bản** | "Chuyền một câu qua năm người, xem nó thất bản thành cái gì." | Phòng trực tiếp (chính) + nhóm chat (phụ) | Lá Úp | [PRD](tam-sao-that-ban-prd.md) | [SRS](tam-sao-that-ban-srs.md) | G20–G25 (khung G20–G29) |
| **Phiên Tòa Tủ Lạnh** | "Hộp xôi trong tủ lạnh đã biến mất. Thủ phạm đang ngồi trong phòng này." | Sự kiện trực tiếp 15–50 người | Lá Úp | [PRD](phien-toa-tu-lanh-prd.md) | [SRS](phien-toa-tu-lanh-srs.md) | G31–G37 (khung G30–G39) |
| **Sĩ Số +1** | "Lớp bạn có 30 người. Điểm danh ra 31." | Sự kiện trực tiếp 15–50 người | Lá Úp | [PRD](si-so-cong-1-prd.md) | [SRS](si-so-cong-1-srs.md) | G41–G47 (khung G40–G49) |
| **Tri Kỷ** + Hiểu Nhau Không? | "Tri kỷ là người hiểu mình. Xem hai đứa đồng điệu ở đâu, chỉ hai đứa thấy." | Từng cặp, theo yêu cầu | **Trong Lá Lành** | [PRD](tri-ky-prd.md) | [SRS](tri-ky-srs.md) | G50–G55 (khung G50–G59) |

Hạ tầng phòng trực tiếp dùng chung (Phiên Tòa, Sĩ Số +1, Tam Sao bản trực tiếp): [shared-room-platform-srs.md](shared-room-platform-srs.md), user story G01–G09 (khung G00–G09; G00 chưa dùng). Danh sách story: [`docs/user-stories/game/README.md`](../../user-stories/game/README.md).

Tài liệu đi kèm:

- DPIA bản nháp: [`docs/legal/2026-10-26-game-line-dpia.md`](../../legal/2026-10-26-game-line-dpia.md)
- Nhãn App Privacy, Data safety và nháp chính sách quyền riêng tư: [`docs/legal/2026-10-26-game-line-store-privacy-and-policy-draft.md`](../../legal/2026-10-26-game-line-store-privacy-and-policy-draft.md)
- Bộ chơi thử bằng giấy: [`docs/playtests/2026-11-game-line/`](../../playtests/2026-11-game-line/README.md)
- Nghiên cứu nền: báo cáo "Chốt năm trò, giữ trọn chữ Lành" và hai báo cáo trước (thư mục `reports/` của checkout làm việc, chưa đưa vào repo).

Bốc Lá và Dây Vô Hình nằm trong danh mục ý tưởng nhưng **chưa thuộc phạm vi bộ tài liệu này**.

## Ranh giới thương hiệu

- **Lá Úp** (tên đề xuất, chờ owner — D1): bốn trò ồn ào, không cần dữ liệu sinh, chạy trên web, ghi "một sản phẩm của Lá Lành". Người chơi không có tài khoản, chỉ biệt danh.
- **Lá Lành**: Tri Kỷ, vì cần hồ sơ sinh của cả hai người và phải đi qua cổng riêng tư của app chính.
- Mỗi trò Lá Úp có đúng một cầu nối tự nguyện về Lá Lành (lá tarot của tuần, chú thích Sao Thủy, lá Justice). Bước qua cầu nối cần đồng ý riêng và **không mang theo dữ liệu game**.

## Nguyên tắc chung (áp cho mọi trò)

1. Ra mắt cho người từ 18 tuổi trước (đại học, văn phòng). Bản cho học sinh dưới 18 tuổi ngoài phạm vi.
2. Không chữ tự do ngoài biệt danh ở MVP. Không nhắn tin ẩn danh, không chat, không tải danh bạ, không tự mời, không phòng công khai, không ảnh hay giọng nói.
3. Không đoán sức khoẻ tinh thần, xu hướng tính dục, sang chấn, ngoại tình, danh tính crush, kết quả thi hay "ai toxic". Không xếp hạng người.
4. Phán xét luôn nhắm vào vai do game chia, không nhắm vào con người. Bản án tượng trưng, có "Miễn án".
5. Không AI ở MVP. Nội dung chạy bằng mẫu soạn sẵn và cây quyết định.
6. **Không streak, không coin/XP, không gây áp lực quay lại** — nguyên tắc sản phẩm đã có test (`apps/web/src/shared/ui/companion/growth.test.ts`). Chỉ Hết Cứu % có thông báo đẩy: người chơi tự bật, tối đa 1 thông báo mỗi tuần cho mỗi nhóm, câu cố định không có biệt danh hay con số (HC-FR-53–56). Tam Sao Thất Bản, Phiên Tòa Tủ Lạnh và Sĩ Số +1 không gửi thông báo nào. Tri Kỷ không tự gửi thông báo nhắc; khi có người nhận lời, push (nếu người dùng đã bật trong Lá Lành) chỉ là câu cố định (TK-12).
7. Link phòng, lời mời và thẻ lật là nhạy cảm theo năng lực: không lập chỉ mục, `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, token không vào log hay analytics, thu hồi được, hết hạn ngắn, giới hạn số lần đoán mã.
8. Dữ liệu tối thiểu, xoá sớm: phòng trực tiếp xoá dữ liệu người chơi khi kết thúc (màn "tiêu huỷ hồ sơ"); chỉ giữ số đếm tổng hợp không định danh.

## Xung đột cần owner quyết

**Hết Cứu % và nguyên tắc "không coin/XP".** Báo cáo nghiên cứu đề xuất "lá" đặt cược được cấp lại mỗi tháng và điểm cộng dồn cả mùa. Cách đó tạo một đơn vị tiền tệ và một bảng xếp hạng người, trái nguyên tắc 6. Bộ tài liệu này viết theo **mặc định an toàn**: lá chỉ tồn tại trong một sự kiện tuần (3 lá mỗi sự kiện, không cộng dồn, không cấp lại, không cửa hàng), điểm về 0 sau mỗi sự kiện, tổng kết mùa chỉ có danh hiệu và khoảnh khắc. Owner chốt ở D3.

## Quyết định chờ owner

| # | Câu hỏi | Mặc định trong tài liệu |
|---|---|---|
| D1 | Tên thương hiệu phụ | Lá Úp |
| D2 | Tên trò % hằng tuần | Hết Cứu % |
| D3 | Cơ chế "lá" của Hết Cứu % | Lá chỉ trong một sự kiện, không cộng dồn (xem phần xung đột) |
| D4 | Tam Sao bản chat có vào MVP | Chỉ khi chơi thử giấy đạt ngưỡng hoàn tất chuỗi |
| D5 | Tri Kỷ có con số độ hợp | Không. Chỉ có điểm x/7 của Hiểu Nhau Không? |
| D6 | Sĩ Số +1 ở văn phòng | Mặc định "bật đèn" |
| D7 | AI làm thẩm phán hoặc con ma ở MVP | Không |
| D8 | Nhân Vật Chính trong Hết Cứu % | Chỉ người tự nguyện, xoay vòng |

## Thứ tự đề xuất khi giai đoạn 3 mở

1. Chơi thử giấy (làm được ngay, không chạm runtime): Hết Cứu % → Tam Sao → Phiên Tòa (tất niên) → Sĩ Số +1 (lớp đại học) → kiểm tra chữ "tri kỷ".
2. Tri Kỷ đi theo nhịp giai đoạn riêng tư (cần câu trả lời của counsel về dữ liệu suy luận và luồng đồng ý hai chiều).
3. Dựng: Hết Cứu % → hạ tầng phòng + Tam Sao bản trực tiếp → Phiên Tòa → Sĩ Số +1 → Tam Sao bản chat.
