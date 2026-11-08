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

## Quán ngày thường (`quan.html`)

Quán mở mọi ngày, không có buổi hẹn. Giống đi chùa online (Sansa) nhưng là quán cà phê mưa.

- **Vào là ngồi:** không phải đăng ký. Mỗi lần vào được đặt một tên Lá ngẫu nhiên, ví dụ "Lá Sen Hay Cười".
- **Khách:** khách hư cấu tự ra vào. Đông vào sáng sớm và buổi tối; từ 0 tới 4 giờ sáng thì vắng, chỉ có Cô Lá và mèo Mướp. Theo giờ của máy; thêm `?gio=21` để thử một giờ khác.
- **Làm gì:** chắp tay, vẫy tay, ngủ gật, ngồi vào bàn. Ở đúng chỗ thì tưới cây, vuốt mèo, ngắm mưa, đọc sách, đánh đàn. Ở quầy thì gọi một ly (ly đặt lên bàn khi bạn ngồi), xin lá bài hôm nay, hoặc nói chuyện với Cô Lá.
- **Nói:** chỉ có câu chào sẵn ("Chào bạn 🙏", "Bình yên nha"…), không gõ chữ tự do. Khách đi ngang thường chắp tay chào; bạn chào thì người gần nhất chào lại.
- **Đồ mang theo:** mỗi người có một túi (balo, túi vải, túi đeo chéo hoặc tay không), có khi kèm ô vì trời mưa, và một thứ để làm: laptop, sách, sổ vẽ, tai nghe, cuộn len, máy ảnh film. Đứng thì đeo túi, cầm ô; ngồi thì túi để cạnh ghế, đồ bày lên bàn. Bạn tự chọn đồ ở cột bên, ngồi xuống rồi bấm "Lấy đồ ra". Chỉ để nhìn, không mua bán hay xếp hạng.
- **Note cho chính mình:** tối đa 3 tờ, mỗi tờ 60 ký tự. Lúc về đọc lại; chỉ nằm trong tab.
- **Bảng ở quầy:** báo buổi hẹn sắp tới, có nút "Mình muốn hẹn" (bản thử chưa nhận đăng ký).
- **Lúc về mang theo:** ly của bạn (hình pixel), lá bài hôm nay kèm một việc nhỏ, một câu của Cô Lá, các note của bạn.
- **Không có:** điểm, chuỗi ngày, thời gian ngồi, thưởng khi quay lại. Lá bài giống nhau cho mọi người trong một ngày và chỉ gợi việc nhỏ.

Quán có bảng menu phấn, kệ lọ và ly, tranh hoàng hôn, đèn neon hình lá, chậu trầu bà treo, dây đèn nhỏ dọc tường, rèm cửa sổ, đèn thả trên từng bàn, ghế mây, bình hoa nhỏ, thảm dệt giữa lối đi và thảm chùi chân ở cửa. Ban ngày cửa sổ sáng hơn, neon tắt; ban đêm đèn ấm và góc phòng tối dần. Ly trên bàn bốc hơi nhẹ (chỉ khi cử động đầy đủ).

Hình quán (`room.js`) dùng chung cho cả buổi hẹn và quán ngày thường. Luật quán nằm ở `cafe.js`.

## Thử thách đôi (`doi.html`)

Level 1 "Sĩ số +1" của đội đôi (xem `docs/research/2026-11-08-hen-o-la-doi-pha-an.md`). Bạn và một đồng đội hư cấu ngồi chung bàn. **Mỗi người giữ một nửa thông tin và một nửa câu trả lời**, nên không ai giải một mình được.

- **Trước khi vào:** chọn màu chơi 😂 Hài (chiều ấm, Mướp nhảy vào ảnh) hoặc 👻 Hơi rợn (quán tối, đèn pin, bóng mờ sau hàng ghế). Ở mode rợn, mỗi người chọn mức gan; đội chơi ở mức nhẹ hơn.
- **Vòng 1:** sổ khách tối qua có 6 dòng nhưng ảnh chỉ có 5 ly.
  - Bạn cầm ảnh: đếm từng loại ly rồi dán note số ly.
  - Đồng đội cầm sổ: đọc sổ khi bạn bấm "Đọc giúp mình". Đọc note của bạn rồi điền tên dòng thừa. Đếm sai thì đồng đội nói "chưa khớp dòng nào", không đoán bừa.
  - Bạn điền loại ly bị thiếu.
- **Vòng 2 · đổi vai:** đồng đội cầm hai ảnh (ly và giá ô), bạn cầm sổ, gạch bớt dòng, điền tên. Mỗi ảnh riêng lẻ cho 3 khả năng; ghép cả hai mới ra đúng một dòng.
- **Chốt:** cả hai cùng bấm "Chốt" (hoặc cử chỉ 3-2-1). Nếu sai, cả đội nhận một câu chung, không nói ô nào sai hay ai sai, và chốt lại được.
- **Về đích:** mỗi vòng thắp một đèn trên mái quán, cạnh đèn của các đội khác. Không có bảng xếp hạng. Mode rợn kết thúc bằng một cú lộ hài.
- **Cử chỉ và note:** đọc giúp, đợi mình, 3-2-1, đập tay; note ≤ 60 ký tự dán lên bàn, không có trả lời qua lại.
- **"Mình sợ quá":** bật đèn cho cả đội, không ai phải giải thích. Phòng tối dần chậm tới một mức trần, không bao giờ nhấp nháy.
- **Góc nghỉ:** mỗi người hỏi một câu tuỳ chọn, rồi chọn kín "Đi tiếp cùng nhau?". Chỉ khi cả hai cùng muốn mới đi tiếp chung đội. Màn hình không nói ai đã chọn gì.
- Sổ khách là hồ sơ hư cấu, không bao giờ trỏ vào người trong buổi. L2, L3 làm sau.

## Khách quán (`khach.html`)

Cho người chưa muốn ghép đôi, chỉ muốn ngồi cho có không khí. Bạn ngồi trên **tầng lửng** nhìn xuống buổi hẹn.

- **Vào quán:** tầng lửng có 40 chỗ. Hết chỗ thì xếp hàng; hàng ngắn, tự lên khi có người về. Mỗi người được một tên Lá ngẫu nhiên.
- **Xem ba khoảnh khắc chung:**
  - Tự do: người hẹn đi lại, làm trò.
  - Thả đèn: các đôi đèn bay lên, chỉ biết có mấy đôi, không biết ai chọn ai.
  - Tái hiện: Cô Lá kể lại vụ án.
- **Không xem được:** bàn xoay, thư, thử thách đôi, ly cuối. Người hẹn không hiện tên, không bấm vào hay đi theo được.
- **Làm gì:**
  - 👏 Vỗ tay hoặc 🍃 thả lá cổ vũ cho cả khoảnh khắc. Hàm cổ vũ không nhận tên ai.
  - Gọi ly, xin lá bài tối nay, chào khách bên cạnh bằng câu sẵn.
  - Viết note cho chính mình.
- **Mang về:**
  - Ảnh kỷ niệm của quán lúc thả đèn (chỉ nằm trong tab).
  - Ly của tối nay và lá bài.
  - **Ghi chép của Cô Lá:** 3 khoảnh khắc dễ thương, không nói ai là ai, để học cách làm quen mà không nhìn trộm.
  - Note của bạn và nút "Lần sau mình muốn hẹn".
- Người hẹn chỉ thấy tầng lửng là một hàng dáng ngồi. Không có bộ đếm người xem.

## Kiểm tra

```sh
node --test event.test.cjs world.test.cjs cafe.test.cjs duo.test.cjs spectate.test.cjs
```

44 test. `event.test.cjs` và `world.test.cjs` (20) kiểm:
- Xoay bàn không lặp cặp.
- Nửa lá tarot ghép đúng hai người, chủ đề lá bài không đoán gì về ai.
- Lá và thư ẩn danh, có giới hạn, và không làm tăng cảm tình với người gửi.
- Thư chỉ nhắc việc người viết đã thấy.
- Cặp cuối luôn do hai bên cùng chọn.
- Bong bóng lời nói bị cắt sạch.
- Lời thoại khách không chứa số hay thông tin liên lạc.
- Mọi chỗ ngồi và đồ vật đều tới được.
- Sprite của lab 14 vẽ được mọi dáng.

`cafe.test.cjs` (10) kiểm:
- Tên ngẫu nhiên đúng dạng.
- Giờ vắng và giờ đông.
- Lá bài giữ nguyên trong ngày.
- Lá bài và lời Cô Lá không đoán hay phán gì.
- Chỉ có câu chào sẵn.
- Note bị cắt sạch.
- Module quán không có thứ gì giữ điểm.
- Đồ mang theo chỉ là hình và một việc để làm.

`duo.test.cjs` (9) kiểm:
- Mỗi vòng có đúng một dòng thừa; ở vòng 2, một ảnh riêng lẻ không đủ.
- Ảnh khớp sổ trừ dòng thừa.
- Dòng thừa không trùng tên khách hay người chơi.
- Đổi vai giữa hai vòng; mỗi chỗ trống thuộc về một người.
- Cần cả hai chốt; câu báo sai giống nhau dù sai chỗ nào.
- Đồng đội chỉ kết luận từ note của bạn.
- Đội chơi ở mức gan nhẹ hơn.
- "Đi tiếp cùng nhau" cần hai lần đồng ý, không lộ ai từ chối.
- Không có gì giữ điểm, không có chữ máu me.

`spectate.test.cjs` (5) kiểm:
- Hàng chờ ngắn.
- Chỉ xem khoảnh khắc chung.
- Cổ vũ không có đích.
- Ghi chép của Cô Lá không lộ tên hay số.
- Đèn chỉ là con số.

Đã chơi trọn 5 màn trong pane trình duyệt Chromium của app desktop ở 800×600 và 375×812: cả nhánh có cặp lẫn không có cặp. Quán ngày thường đã thử lúc 3 giờ, 7 giờ, 20 giờ và 21 giờ (giả lập bằng `?gio`): gọi ly, ngồi, xin lá bài, cất note, ra về; ở 1100×820 và 375×812. Thử thách đôi đã chơi trọn hai vòng và góc nghỉ ở cả hai mode, trả lời sai và đếm sai, ở 1100×820 và 375×812. Khách quán đã xem trọn ba khoảnh khắc, vỗ tay, thả lá, gọi ly, nhận đồ mang về, ở 1100×820 và 375×812. Chưa thử Safari iOS hay Chrome Android thật, chưa có người chơi thật.

`window.__hen` (`hold`, `step`, `begin`, `next`…) chỉ để kiểm thử trong pane bị ẩn, không phải API sản phẩm.

## Ranh giới

Xem `AGENTS.md`. Đây là bản thử cảm giác cho owner chơi một mình với khách hư cấu. Một buổi thật với người thật cần làm rõ trước:
- Có phải mạng xã hội hoặc trò chơi điện tử theo Nghị định 147/2024 không.
- Đồng ý riêng cho dữ liệu nhạy cảm theo Nghị định 356/2025.
- Kiểm duyệt bong bóng lời nói.
- Kiểm tuổi.

Xem `docs/research/2026-11-07-the-gioi-pixel-ghep-doi.md`. KS-26 vẫn BLOCK.
