# Home audit — 2026-10-06

## Kết luận

Home cũ có hai vấn đề cùng lúc: câu mở đầu không trả lời được người dùng nên làm gì, còn note lấy một câu trừu tượng từ content matrix rồi đặt ở cấp chữ quá lớn. Bản mới chuyển trọng tâm về một hành trình dễ quét: đọc note hôm nay, giữ một việc nhỏ nếu hữu ích, rồi chọn đúng nhu cầu tiếp theo.

## 1. Mở đầu

- Trước: `Hiểu mình. Hiểu chuyện đang xảy ra. Hiểu một người.` là tuyên ngôn thương hiệu nhưng không tạo nhiệm vụ rõ ràng, ngày nào cũng lặp lại.
- Sau: `Hôm nay có gì đáng để ý?` và một câu hướng dẫn ngắn nói rõ thứ tự sử dụng.
- Trạng thái: đạt. Một tiêu đề chính, một câu dẫn, không còn ba mệnh đề cạnh tranh nhau.

## 2. Note hôm nay

- Trước: câu `Một việc chưa hoàn hảo có thể nằm yên lâu hơn một việc còn thiếu.` vừa trừu tượng vừa dùng so sánh khó hình dung.
- Sau: `Bạn có thể sửa mãi một việc đã đủ dùng.`; phần tình huống và việc có thể thử được đặt chung trên một tờ note.
- Trạng thái: đạt. Nội dung có chủ thể, động từ và tình huống đời thường; CTA nói rõ nó sẽ lưu việc gì để thử.

## 3. Các lối đi tiếp

- Trước: các tính năng bị tách thành nhiều khu vực nhỏ, nhãn thiên về khái niệm nên khó quét.
- Sau: bốn ô 2×2 gồm `Bản đồ của mình`, `Bầu trời hôm nay`, `Người ấy`, `Rút Tarot`, mỗi ô có một câu giải thích lợi ích.
- Trạng thái: đạt ở mobile 390 px. Thứ tự ưu tiên và vùng bấm đã rõ hơn.

## 4. Content gate

- Prompt viết lại yêu cầu tiếng Việt phổ thông, hiểu ngay lần đầu; giọng một người bạn trẻ thông minh, ấm, trực tiếp, hơi nghịch nhưng không cố dùng meme hoặc tiếng lóng.
- Cấm ẩn dụ văn vẻ, nghịch lý giả sâu, jargon tâm lý và câu không có chủ thể/hành động/tình huống quan sát được.
- Daily Home có rule riêng: tiêu đề dưới 14 từ và chứa ví dụ xấu/tốt để neo phong cách.
- Content audit giờ quét cả ngân hàng headline, scene, observation và advice của daily psychology.

## 5. Accessibility và giới hạn kiểm tra

- Đã kiểm tra cấu trúc heading, nhãn vùng note, nhãn phần lời gợi ý và mô tả liên kết bằng accessibility tree.
- Đã kiểm tra viewport mobile 390×844 và full-page capture.
- Chưa thay thế kiểm tra thủ công bằng VoiceOver/TalkBack trên thiết bị thật; đây vẫn là bước cần làm trước public beta rộng.

## Bằng chứng

- `01-home-before.png`: bản trước khi sửa.
- `02-home-after.png`: cấu trúc mới lần đầu.
- `03-home-final.png`: bản cuối sau khi sửa content version và tự thay nội dung bị cấm.
