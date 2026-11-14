# Game lab 13

Prototype độc lập để duyệt tính cách, tương tác, hai hướng hình và cách lên màn. Không phải tính năng production.

Mở `index.html`. Chọn Sĩ số +1 hoặc Vụ cà phê ở đầu trang. Không cài package, không đăng nhập, không cần API hoặc DB. Các script là classic script nên bản file cục bộ cũng chạy được.

## Chốt mặc định cho bản thử

- Profile toàn bộ là nhân vật hư cấu 18+. Cung và lá tarot là archetype tác giả gán, không lấy ngày sinh. Tính cách/tendency đổi câu trả lời theo Hỏi nhẹ, Hỏi thẳng hoặc Trêu nhẹ. Không đổi chứng cứ hoặc đáp án.
- Sĩ số +1 mặc định mở option ảnh điểm danh. Có thể chuyển sang option hành trình ngay, hai option giữ tiến độ riêng trong tab.
- Bật đèn, không âm thanh tự phát, không hù bất ngờ; có dừng cử động và hỗ trợ reduced motion.
- Hình A là màn hiển thị đầu tiên, không phải phương án đồ họa cuối đã được owner chọn. B có căn phòng và sprite riêng.

## Hai option, sáu vụ chơi được

| Option | Vụ 1 | Vụ 2 | Vụ 3 |
|---|---|---|---|
| Ảnh điểm danh | Đếm huy hiệu, tìm vật dư | Giao hai bảng huy hiệu và bìa sổ | Thử bỏ hồ sơ để cả ba bảng khớp |
| Hành trình | Thời gian tối thiểu trên bản đồ | Phải ghé checkpoint, có thể quay lại | Cổng có giờ đóng/mở, cần tính chờ |

Mỗi vụ có một fixture, mã nguồn và thời điểm riêng. Huy hiệu, sổ và phiếu của từng vụ ghi trong popup, không suy từ màu áo hay bàn ghế trong tranh. Sáu avatar trên phòng là sáu hồ sơ do máy xuất, không phải chứng cứ sáu người đang đứng trong phòng.

Bấm nguồn trên hiện trường hoặc thẻ Khám xét, xem dữ liệu mô phỏng và hoàn thành câu kiểm quan sát. Nguồn được kiếm và ghim. Chọn hồ sơ để thử bỏ; bảng chỉ so với nguồn đã kiếm. Nộp khi đủ nguồn đã ghim. Đúng mới mở vụ kế tiếp, sai có thể thử lại không mất lượt. Tiến độ chỉ là quyền mở vụ trong phiên, không XP/coin/streak.

Bấm avatar để xem tính cách/tendency và thử ba giọng đối đáp. Bấm tarot để gợi cách kiểm. Câu trả lời của NPC và lá gợi ý không phải nguồn chứng cứ.

## Khác bản Sĩ số +1 gốc

PR93 đang đề xuất Ma Sói cho 15–50 người; người thứ N+1 là bản ghép hệ thống, không có một người thật để tìm và loại. Bản lab này là nhánh khám phá solo/NPC, tìm một hồ sơ ghép sai trong sáu hồ sơ của năm vai hư cấu. Không tuyên bố đáp ứng G41–G47 hoặc thay PRD/SRS gốc. Không loại ai khỏi tập thể, không triển khai phòng nhóm.

## Coffee

`coffee/index.html` giữ 11 điểm bấm, Nhìn kỹ/Khám xét, hai bộ hình và ba lớp nhân vật của bản 12. Đã chốt default tính cách Hạnh, Quân, Minh và ba kiểu đối đáp. Cốc không đổ lại, vị trí T2 không đổi, không thêm nội dung riêng hoặc chấm lời giải. T0/T1 và challenge kiếm EV01–EV04 vẫn chưa triển khai.

## Kiểm tra

```sh
node --test model.test.cjs
node ui-check.cjs
node coffee/check.cjs
```

`model.test.cjs` kiểm số nghiệm, nguồn thiếu/ghim thiếu, thử sai, progression, checkpoint, lịch cổng, chờ và personality không đổi solver. `ui-check.cjs` thực thi model/app thật trong DOM mô phỏng, đi hết sáu vụ, 14 challenge, hai bộ hình, profile, thử sai và reset. Coffee có 22 vòng Nhìn kỹ/Khám xét/đóng. Đây không phải test layout hoặc animation trong browser.

Đã xem trực tiếp bốn ảnh mới. Chưa có browser visual QA, mobile QA, test người chơi hoặc bằng chứng viral. Khả năng click/animation thật cần người dùng duyệt; bộ kiểm DOM không thay thế bước đó. Prototype dùng fixture client-side nên không có khả năng giữ bí mật chống người đọc source, không dùng cho multiplayer thật.

## Nguồn, hình và handoff

- [Brief Claude và AC riêng](../../docs/research/2026-10-27-game-lab-13-handoff.md).
- [Prompt hình](art-prompts.json). Ảnh tạo bằng image generation tích hợp, không dùng API trong prototype. Bộ hình coffee giữ từ bản 12, prompt nguồn kèm trong cùng file JSON.
- Tài liệu coffee 05–09 được lưu trong thư mục nguồn cạnh brief, không đổi GT/EV.
- Tất cả quyết định production, counsel, nhãn kho, KS-19 và KS-26 còn nguyên trạng thái pending/BLOCK của nguồn tương ứng. PR không phải release Go.
