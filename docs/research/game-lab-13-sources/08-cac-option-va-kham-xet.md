# Ba phương án và thao tác khám xét trên hiện trường

Ngày: 27/10/2026. Minh họa và bản thử thao tác, không tích hợp runtime game.

## Hình gốc

Ba hình được tạo bằng imagegen tích hợp, theo thứ tự hiển thị trong chat:

1. [Trang truyện](08-option-trang-truyen.png). Hình chính với ngăn khám xét bên cạnh.
2. [Tí hon](08-option-ti-hon.png). Góc không gian và khung khám xét nổi.
3. [Hồ sơ](08-option-ho-so.png). Ưu tiên túi đồ và quan sát vật dụng.

Các hình vẫn gần nhau về nhân vật và phong cách vì dùng chung ảnh tham chiếu. Đây chưa phải ba hệ mỹ thuật đã tách biệt hoàn toàn. [Prompt đầy đủ](08-prompts-option-va-chuyen-dong.txt).

## Điều người dùng đã làm rõ

Không tách người và đồ vật ra thành một sân khấu animation độc lập. Hình tổng thể là nơi thao tác chính. Khi bấm một vật, mới xuất hiện hai lựa chọn:

- Nhìn kỹ: phóng gần phần đang nhìn thấy, chưa mở ngăn hoặc nội dung bị che.
- Khám xét: kiểm nơi chứa hoặc các mặt được luật ván cho phép, rồi ghi phạm vi quan sát. Tìm thấy đồ không tự xác nhận chủ đồ gây chuyện.

Bản xem thử trong chat dùng hình tổng thể và 11 điểm chọn: cốc, cặp, máy in, túi quần vai Quân, tarot, điện thoại, tài liệu, sổ, bình nước, bồn rửa, dây đang được cầm. Các nút số là vùng bấm tạm để thử thao tác, không phải dấu xác nhận chứng cứ. Hình chính đã bỏ phần ngăn khám xét có sẵn trong ảnh, để người chơi chủ động mở chi tiết.

Ở khổ hẹp, một số dấu nhỏ được ẩn để tránh chồng vùng bấm. Danh sách chọn đồ vẫn có đủ 11 mục. Nhìn kỹ, khám xét, đóng cửa sổ và quay lại món đang chọn là các thao tác riêng.

## Chuyển động trong bản thử

- Cửa sổ cận cảnh tiến gần và hiện lên sau khi chọn hành động.
- Cặp có hai hình đóng và mở, chuyển nhẹ khi bấm mở ngăn. Chưa đồng bộ trạng thái vật với hình nền tĩnh.
- Tôn trọng cài đặt giảm chuyển động. Không chớp sáng hoặc chạy âm thanh.
- Không cho cốc tự rung hoặc tái diễn việc đổ tại hiện trường hiện tại. Không dùng chuyển động để chỉ người gây chuyện.

[Atlas gốc](08-motion-atlas.png) có hai tư thế Quân và hai trạng thái cặp. Nhân vật chưa được ghép thành chuyển động trên bản đồ. Không coi thử thở/chớp mắt riêng là đã hoàn thành animation hiện trường. Atlas còn cần căn lại từng khớp và giữ nguyên đồ cầm trước khi dùng trong game.

## Giới hạn nội dung khám xét

Khám túi Quân trong bản thử hiện đồ hư cấu do ảnh concept minh họa. Chưa chốt đây là EV của vụ mẫu. Các nơi chưa có ảnh riêng, như đáy cốc, trang sổ bị che, tin nhắn điện thoại hoặc nhật ký máy in, nói rõ là chưa có dữ liệu. Không tự sinh một bí mật để người chơi tìm thấy.

Chữ nhỏ, hóa đơn, mã hoặc các món mới do imagegen vẽ chưa dùng để chấm suy luận. Chuỗi EV01 đến EV04 và GT trong tài liệu 06 không thay đổi. Túi và đồ thuộc vai hư cấu, không xin ảnh túi, điện thoại hoặc đồ riêng của người thật.

## Kiểm tra đã làm

- Kiểm cú pháp JavaScript, ảnh nhúng và kích thước bản xem thử dưới 1 MB.
- Kiểm 33 tổ hợp món và phương án bằng mô hình DOM: chọn, nhìn kỹ, khám xét, đóng, Escape và quay lại. Kiểm mở/đóng cặp và bỏ chọn.
- Chưa xác minh bố cục và hoạt ảnh trong trình duyệt. Mở file cục bộ bị chính sách trình duyệt chặn; không thử vượt chặn. Chưa có kết quả test runtime của game.

## Prompt tiếp cho Claude

Giữ hình tổng thể làm nơi thao tác chính. Dùng bản xem thử trong chat và tài liệu 05, 06, 07, 08 để hoàn thiện đặc tả 11 điểm bấm. Với mỗi điểm, tách Nhìn kỹ và Khám xét, trạng thái đóng/mở, quyền xem, góc cận cảnh cần vẽ, phần chưa biết và phạm vi kết luận. Không làm sân khấu animation nhân vật rời. Không sinh chứng cứ mới hoặc sửa GT. Chưa tích hợp runtime cho tới khi người dùng chọn phương án hình và duyệt tương tác.
