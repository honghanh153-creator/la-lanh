# Game lab 14 · Sĩ số +1 có di chuyển

Prototype độc lập, làm lại game lab 13 theo hướng game hơn: người chơi điều khiển một thám tử pixel đi quanh lớp học, lại gần đồ vật hoặc nhân vật để khám nguồn và nói chuyện, rồi nộp lập luận ở máy điểm danh. Không phải tính năng production và không nối vào `apps/web` hay `apps/api`.

Mở `index.html` qua một máy chủ tĩnh bất kỳ. Không cài package, không đăng nhập, không API, không DB, không lưu trữ lâu dài.

## Chơi

- **Đi:** W A S D hoặc phím mũi tên; hoặc chạm/bấm vào sàn, nhân vật tự tìm đường. Trên máy cảm ứng có thể bật D-pad (tuỳ chọn).
- **Khám / nói chuyện:** đứng cạnh rồi nhấn E, hoặc chạm thẳng vào đồ vật hay nhân vật (nhân vật tự đi tới rồi mở). Trên điện thoại có nút hành động lớn ở cạnh dưới.
- **Sổ tay:** luôn hiện (cột phải trên máy tính, ngay dưới khung game trên điện thoại). Tab *Nguồn*, *Tự suy luận*, *Đi tới*. Phím N nhảy tới sổ tay.
- **Cử động:** Đầy đủ / Giảm / Tắt. Mặc định là *Giảm* nếu hệ điều hành bật giảm chuyển động.

## Bảy vụ, mỗi vụ một kỹ năng

| # | Vụ | Kỹ năng | Nguồn |
|---|---|---|---|
| 1 | P1 Chiếc huy hiệu lạc lớp | Đếm một loại vật | Máy ảnh |
| 2 | R1 Hành lang không có lối tắt | Cộng thời gian trên bản đồ | Sơ đồ, máy quét |
| 3 | P2 Hai ảnh, một giao điểm | Đối chiếu hai nguồn | Máy ảnh, bàn giáo viên |
| 4 | R2 Phải ghé phòng máy | Đi vòng qua checkpoint | Sơ đồ, máy quét, sổ phòng máy |
| 5 | P4 Ảnh chụp qua gương | Đọc dấu nguồn của ảnh | Máy ảnh, bàn giáo viên, tủ gương |
| 6 | R4 Cửa thoát hiểm một chiều | Chọn đường, tôn trọng cửa một chiều | Sơ đồ, máy quét, biển cửa |
| 7 | X1 Ảnh phòng máy lúc 09:04 | Ghép hành trình với ảnh có giờ | Sơ đồ, máy quét, máy ảnh |

Đáp án xoay vòng, không vụ liền nhau nào trùng người. Mỗi fixture có dấu giờ riêng; vụ sau không sửa dữ kiện vụ trước.

## Khác game lab 13 (theo review PR #104)

- **Không còn máy chấm hộ.** Sổ tay không tự cộng, không hiện ✓/≠. Bảng dựng đường chỉ cộng các đoạn người chơi tự chọn, không tìm đường ngắn nhất.
- **Nộp phải kèm lý do** (loại vật thừa ở từng ảnh, số phút tối thiểu, hoặc bắt buộc/không thể có mặt). Sai tên hay sai lý do đều nhận cùng một câu, không chỉ ra phần nào sai.
- **Không lộ nguồn chưa khám.** Hồ sơ của từng nhân vật chỉ hiện thuộc tính thuộc nguồn đã khám.
- **Câu kiểm khi khám nguồn không nhắc tới hồ sơ đáp án**: ghi lại cả bảng đếm, đọc một đoạn sơ đồ không liên quan, đọc dòng của một hồ sơ khác.
- **Ba vụ mới đã chứng minh một nghiệm**: P4 (đọc nguyên ảnh gương cho 0 nghiệm), R4 (quên cửa một chiều cho 3 nghiệm), X1 (chỉ xét thời gian thì cả 6 đều khả thi).
- Tarot là **bộ phương pháp**: mỗi vụ một lá gợi *cách kiểm*, không nhắc tên ai. Cung chỉ đổi giọng nói; các câu thoại không chứa số, giờ hay tên khu.

## Đồ họa và chuyển động

- Toàn bộ hình vẽ bằng code: phòng 15×10 ô (240×160 px nội bộ), nhân vật 12×16 px có viền, 4 hướng × 3 khung đi bộ, chớp mắt. Không dùng ảnh sinh, nên vị trí đồ vật luôn nhất quán với va chạm và logic.
- Canvas phóng theo bội số nguyên của pixel thiết bị, `image-rendering: pixelated`, `imageSmoothingEnabled = false` sau mỗi lần đổi kích thước. Khi bội số nguyên nhỏ hơn 85% khung (ví dụ 360 px ở 2x) thì giãn CSS, chấp nhận pixel hơi không đều.
- Hiệu ứng: bụi bước chân, lấp lánh khi ghi nguồn, mũi tên mục tiêu nhún nhẹ, hồ sơ thừa nhiễu sọc rồi tan thành lá, các nhân vật khác nhảy nhẹ. Không có nhấp nháy sáng, không rung màn hình, không âm thanh.

## Kiểm tra

```sh
node --test cases.test.cjs engine.test.cjs
```

`cases.test.cjs` (12 test) kiểm tính duy nhất, bẫy gương và cửa một chiều, judge cần lý do, câu kiểm không nhắc đáp án, đáp án xoay vòng. `engine.test.cjs` (9 test) kiểm bản đồ, mọi điểm tương tác tới được kể cả khi NPC đứng chắn, trượt va chạm, gia tốc, sprite và chu kỳ bước.

Đã chơi trọn 7 vụ trong Chromium (pane trình duyệt của app desktop) ở 1024×768, 390×844, 360×780; kiểm bàn phím, chạm-để-đi, popup, focus trap. Chưa thử Safari iOS và Chrome Android thật, chưa đo hiệu năng máy yếu, chưa có người chơi thật.

`window.__lab14` có `hold()`/`step()` chỉ để kiểm thử trong pane bị ẩn (không có animation frame). Không phải API sản phẩm.

## Ranh giới

Nhân vật hư cấu 18+. Không thu tên, ảnh, ngày sinh, chart, analytics, mạng hay lưu trữ. Nguồn client-side nên ai đọc mã cũng thấy đáp án; không dùng cho chơi nhiều người thật. Không thay luật Ma Sói 15–50 người của PR #93; KS-19, KS-26 và các quyết định owner/counsel giữ nguyên.
