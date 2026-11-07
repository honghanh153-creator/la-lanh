# Hẹn ở Lá · bản thử quán cà phê mưa

Prototype độc lập cho một **buổi ghép đôi dạng sự kiện** trong thế giới pixel. Không phải tính năng production: không nối vào `apps/web` hay `apps/api`, không có tài khoản, mạng hay lưu trữ. Engine hình (sprite 12×16, chu kỳ bước, va chạm trượt, A*) lấy từ `../game-lab-14/engine.js`; bản đồ quán nằm ở `world.js`, luật của buổi ở `event.js`.

Ý tưởng và nguồn tham khảo: `docs/research/2026-11-07-format-ghep-doi-ngoai-doi.md`.

## Một buổi gồm những gì

10 người được mời: bạn và 9 khách hư cấu. Mọi người chỉ hiện tên Lá (Lá Me, Lá Phong…), món đồ mang theo và màu đèn:
- 🌸 tìm người thương
- 🍃 tìm bạn
- ☕ ghé chơi cho vui

Cô Lá là người dẫn chương trình, đứng sau quầy. Mỗi khi chuyển màn, Cô Lá thông báo trên dải chữ ở đầu khung game.

| Màn | Học từ | Chơi thế nào |
|---|---|---|
| Lối vào | Thư mời Timeleft | Chọn tên Lá, dáng, món đồ, màu đèn. Nhận **nửa lá tarot** (kiểu lock & key) |
| 1 · Tự do | Sự kiện im lặng/đọc sách | Đi lại, làm trò: nhảy, làm mặt hề, ngủ gật, vẫy tay. Ở đúng chỗ thì đọc sách, tưới cây, vuốt mèo, ngắm mưa, đánh đàn, gọi đồ. Nói thành **bong bóng trên đầu** (≤ 40 ký tự). Lại gần ai đó để **thả lá bí mật** (tối đa 5), **hỏi nửa lá tarot** hoặc vẫy tay |
| 2 · Xoay bàn | Tiệc ghép đôi Nhật | 4 lượt; hệ thống xếp cặp (không ai gặp lại người cũ). Mỗi bàn **cùng pha một ly**: mỗi người chọn một nguyên liệu, ra tên món. Có thẻ câu hỏi; trả lời bằng ô Nói |
| 3 · Thư giữa giờ | Thẻ ấn tượng giữa giờ | Gửi tối đa 3 thư **không ký tên**, chỉ khen một việc bạn **đã thật sự thấy** người đó làm. Mở hộp thư xem lá và thư mình nhận |
| 4 · Thả đèn | Bỏ phiếu cuối, *If You Are the One* (bản dịu) | Chọn kín tối đa 3 người theo thứ tự. Chỉ cặp nào **chọn nhau** mới được công bố; đèn đôi bay lên. Không ai bị tắt đèn công khai |
| 5 · Ly cuối | "Last Drink" của Timeleft | Có cặp: hai người ra bàn cạnh cửa sổ nói thêm. Không có cặp: nhận thư của Cô Lá, kèm số lá và thư đã nhận |

Hai cách ghép theo ý owner:
- **"Thấy rồi muốn":** thả lá, gửi thư, rồi chọn ở màn thả đèn.
- **"Tới giờ hệ thống tự ghép":** các lượt xoay bàn. Bàn chỉ là cơ hội gặp; cặp cuối cùng vẫn phải do cả hai cùng chọn.

## Khách hư cấu "cảm" bằng gì

Mỗi khách có việc hay làm, việc thích thấy người khác làm, và khẩu vị.
- **Thấy** (trong bán kính 6 ô) ai đó làm việc mình thích: +2. Việc khác: +0,5. Mỗi việc chỉ tính lần đầu.
- **Ghép nửa lá tarot** với nhau: +1,5 cho cả hai.
- **Ở bàn:**
  - Người kia chọn nguyên liệu mình thích: +2.
  - Hai người chọn trùng nguyên liệu: +1.
  - Người kia có trả lời thẻ câu hỏi: +1.
- **Lá và thư không ký tên không làm ai thích người gửi hơn**, vì người nhận không biết ai gửi. Test có kiểm điều này.
- **Thả đèn:** khách chọn tối đa 3 người có điểm ≥ 3. Khách ☕ cần ≥ 5.
- **Ghép cặp:** chỉ cặp chọn nhau mới thành; mỗi người tối đa một cặp, ưu tiên thứ tự chọn cao trên cả hai phía. Cả hai 🌸 thì là "đôi hẹn", còn lại là "tình bạn mới".

Đây là mô phỏng cho vui để cảm nhịp buổi, không phải mô hình khoa học. Nghiên cứu hiện có cho thấy không thuật toán nào đoán trước được ai hợp ai, nên bản thật không hiện "điểm hợp".

## Chạy

Mở `hen-o-la/index.html` qua một máy chủ tĩnh, phục vụ từ thư mục `prototype/` để `../game-lab-14/engine.js` tải được. Thêm `?nhanh` vào URL để rút ngắn các màn (45 s tự do, 25 s mỗi lượt bàn).

- **Đi:** W A S D, phím mũi tên, hoặc chạm/bấm vào sàn.
- **Tương tác:** E, hoặc nút dưới khung game. Bấm vào người hay đồ vật để tự đi tới.
- **Làm trò:** phím 1–6.
- **Nói:** T, hoặc ô Nói và các câu nói nhanh.
- **Cử động:** Đầy đủ / Giảm / Tắt. Mặc định theo `prefers-reduced-motion`. Không nhấp nháy, không rung, không âm thanh.

## Kiểm tra

```sh
node --test event.test.cjs world.test.cjs
```

20 test kiểm:
- Xoay bàn không lặp cặp.
- Nửa lá tarot ghép đúng hai người, chủ đề lá bài không đoán gì về ai.
- Lá và thư ẩn danh, có giới hạn, và không làm tăng cảm tình với người gửi.
- Thư chỉ nhắc việc người viết đã thấy.
- Cặp cuối luôn do hai bên cùng chọn.
- Bong bóng lời nói bị cắt sạch.
- Lời thoại khách không chứa số hay thông tin liên lạc.
- Mọi chỗ ngồi và đồ vật đều tới được.
- Sprite của lab 14 vẽ được mọi dáng.

Đã chơi trọn 5 màn trong pane trình duyệt Chromium của app desktop ở 800×600 và 375×812: cả nhánh có cặp lẫn không có cặp. Chưa thử Safari iOS hay Chrome Android thật, chưa có người chơi thật.

`window.__hen` (`hold`, `step`, `begin`, `next`…) chỉ để kiểm thử trong pane bị ẩn, không phải API sản phẩm.

## Ranh giới

Xem `AGENTS.md`. Đây là bản thử cảm giác cho owner chơi một mình với khách hư cấu. Một buổi thật với người thật cần làm rõ trước:
- Có phải mạng xã hội hoặc trò chơi điện tử theo Nghị định 147/2024 không.
- Đồng ý riêng cho dữ liệu nhạy cảm theo Nghị định 356/2025.
- Kiểm duyệt bong bóng lời nói.
- Kiểm tuổi.

Xem `docs/research/2026-11-07-the-gioi-pixel-ghep-doi.md`. KS-26 vẫn BLOCK.
