# Chuẩn nội dung tiếng Việt dễ hiểu của Lá Lành

## Mục tiêu

Người chưa biết chiêm tinh hoặc Tarot phải hiểu được bài đọc ngay lần đầu. Nội dung chính phải tự
chạy tốt từ knowledge bundle trong sản phẩm; Content Studio chỉ là công cụ biên tập tùy chọn, không
phải điều kiện để engine tạo ra nội dung có chất lượng.

## Giọng direct đã chốt ngày 2026-10-07

Viết như nói với một người bạn: có chủ thể, nói rõ việc gì đang diễn ra, không bắt người đọc giải mã ẩn dụ. Không cố chèn slang hoặc câu đùa. Ví dụ chuẩn:

> Bạn gật đầu, nhưng vẫn chưa hiểu hết.
>
> Khi cả nhóm chốt rất nhanh, bạn có thể đồng ý theo dù vẫn còn một chỗ muốn hỏi lại.
>
> Hỏi ngay chỗ đó: Mình chưa rõ phần này, giải thích thêm được không?

Loại các câu như "Ý kiến đông người dễ nghe giống ý kiến đúng" và "Sự tự tin của người nói có thể đang được nghe như bằng chứng". Ý muốn diễn đạt phải được viết rõ trong meaning brief của backend, không chỉ đưa câu khó hiểu cho Luna sửa từ.

Daily Home không ghép quan sát và reflection độc lập. Mọi headline, scene và advice của một issue phải nói cùng một tình huống. Advice phải làm được tại thời điểm của scene, không yêu cầu quay lại trước một việc đã xảy ra.

## Thứ tự bắt buộc của một bài đọc

1. **Trả lời thẳng:** nói điều đáng chú ý nhất bằng một câu ngắn.
2. **Giải thích:** nêu lá bài hoặc dữ kiện chart đóng góp điều gì cho kết luận đó.
3. **Đưa ra đời thường:** mô tả một tình huống có người, việc hoặc hành động quan sát được.
4. **Đề nghị một việc:** dùng động từ rõ, có đối tượng và có thể thử trong thời gian ngắn.
5. **Disclaimer riêng:** đặt ngoài nội dung chính, có kiểu hiển thị khác; không chen giữa phần giải
   nghĩa.

Riêng Home Daily Note rút gọn còn hai lớp: “Cảnh dễ gặp hôm nay” và “Hôm nay thử thế này”.
Scene không được chứa lời khuyên. Evidence, lý do chiêm tinh và disclaimer sâu chỉ xuất hiện khi người
dùng chủ động mở Note Detail.

Full body của lớp fallback một lớp ưu tiên 45–80 từ. Bản đọc Aura nhiều yếu tố có thể dài hơn,
nhưng không kéo dài câu chỉ để tạo cảm giác “đọc sâu”.

## Tiêu chuẩn câu chữ

- Ưu tiên từ quen thuộc, câu chủ động và một ý chính trong mỗi câu.
- Nói rõ ai làm gì. Không dùng “một bên”, “phần kia” hoặc “cơ chế này” khi chưa có chủ thể rõ.
- Mỗi tình huống phải có dấu hiệu quan sát được, ví dụ: tin nhắn đến chậm, lịch đổi, người kia trả lời
  ngắn, hoặc bạn nhận thêm một đầu việc.
- Mỗi gợi ý phải có động từ và việc cụ thể, ví dụ: hỏi lại, viết ra, chọn, đặt lịch, bỏ bớt hoặc kiểm
  tra.
- Không dùng “hãy”, “thử”, “nên”, “đừng” trong scene. Các từ này chỉ được xuất hiện trong advice.
- “Mở lòng”, “được trân trọng” và “ranh giới” được dùng khi câu nói rõ người, việc và hoàn cảnh.
- “Mood” chỉ được dùng trong microcopy vui; không dùng để giải thích kết luận.

## Cụm từ không dùng trong nội dung chính

- pattern, vận hành, giữ nhịp, vùng mờ, cơ chế này;
- kéo ánh nhìn, mở một góc, câu hỏi đang chạm vào;
- đặt lại sức chứa, chuyển năng lượng, một bước có giới hạn;
- nhịp gây nhiễu, nhịp có ích, mang dấu tay, còn một dấu phẩy;
- tín hiệu vũ trụ, vũ trụ thì thầm, mọi thứ xảy ra đều có lý do.

Danh sách máy đọc nằm trong `ContentReviewAgent`. Nếu một cụm mới bị người dùng hiểu sai, phải sửa
output gốc, thêm regression test và cân nhắc đưa cụm đó vào gate; không chỉ sửa một màn hình.

## Content-review agent

Agent là gate xác định, chạy offline và không nhận dữ liệu cá nhân. Trước khi release, agent kiểm tra:

- nguồn và evidence của nội dung;
- cụm từ cấm, disclaimer lẫn vào nội dung và câu quá dài;
- câu lặp, tham chiếu mơ hồ và cách diễn đạt dịch máy;
- tình huống có quan sát được hay không;
- gợi ý có làm được hay không;
- output của 10 synthetic personas có bị trùng lõi hay không.

Web search chỉ dùng trong lúc biên tập để kiểm tra cách nói và được ghi lại thành chuẩn có phiên bản.
Runtime không gửi ngày sinh, câu hỏi, mood, Tarot session hoặc nội dung riêng tư lên công cụ tìm kiếm.

## Vai trò tùy chọn của Content Studio

Studio giúp chủ sản phẩm xem, sửa, preview, publish và rollback content matrix. Khi Studio tắt, lỗi
hoặc chưa được cấu hình, engine vẫn dùng bundled catalog đã qua cùng content-review gate. Studio không
được phép thay đổi chart facts, evidence hoặc bỏ qua gate.

## Cơ sở biên tập

- Microsoft Learn, *Nội dung giao diện người dùng*: dùng từ quen thuộc, động từ hành động cụ thể,
  câu ngắn hoàn chỉnh và thể chủ động:
  https://learn.microsoft.com/vi-vn/power-platform/well-architected/experience-optimization/user-interface-content
- Digital.gov, *Plain Language*: đặt nhu cầu của người đọc trước và giúp họ tìm, hiểu, dùng thông tin:
  https://digital.gov/guides/plain-language/writing
- Australian Government Style Manual, *Quick guide to plain language*: viết rõ, trực tiếp và phù hợp
  với người đọc:
  https://www.stylemanual.gov.au/style-manual-resources/quick-guides/quick-guide-plain-language
