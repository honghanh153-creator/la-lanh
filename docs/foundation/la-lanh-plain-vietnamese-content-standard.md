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

## Giọng Roast đã chốt ngày 2026-10-11

Chủ sản phẩm duyệt một giọng tùy chọn thứ hai: **Roast** — cà khịa thân thiện, chọc đúng chỗ nhưng
vẫn có lối ra. Direct vẫn là mặc định; thiếu lựa chọn thì luôn dùng direct. Quyết định này thay cho
ghi chú "chưa chọn giọng A/B/C" trong plan U6, chỉ cho riêng giọng này.

Quy tắc:

- Chọc vào **hành vi đang được mô tả** trong bài, không bao giờ chọc vào danh tính, ngoại hình, giới,
  gia đình, hoàn cảnh tiền bạc, trí thông minh hoặc sức khỏe tinh thần của người đọc.
- Không chửi thề, miệt thị, nội dung tình dục, định mệnh, dự đoán chắc chắn về sự việc, hoặc nói thay
  suy nghĩ riêng của người khác.
- Cùng nghĩa với direct: cùng issue/scene, cùng lá bài, thứ tự và vị trí, cùng hành động cụ thể. Chỉ
  được thêm một câu mở hoặc khung vui trước/sau; evidence, disclaimer và provenance giữ nguyên.
- Mỗi câu chọc phải đi cùng một việc làm được (micro action hoặc small action của bài).
- Gen Z nhẹ, đọc được với người 18–25: "thám tử tin nhắn", "đọc lần thứ năm rồi đó nha", "thôi nào",
  "não đang mở 12 tab". Hạn chế tiếng Anh; "plot twist", "rep" chỉ dùng lẻ tẻ.
- Tự giảm độ chọc: ví dụ thuộc góc cơ thể/nghỉ ngơi (Daily) hoặc ngữ cảnh năng lượng/chăm mình (Tarot)
  chỉ dùng câu trêu nhẹ. Câu hỏi Tarot về sức khỏe, an toàn, khủng hoảng, pháp lý/tiền bạc, tự hại
  hoặc mất mát dùng direct hoàn toàn, và session lưu giọng thực tế đã dùng.

Ví dụ cùng một tình huống:

> Direct: Bạn đọc lại tin nhắn vì chưa hiểu ý.
>
> Roast: Đọc tin nhắn lần thứ năm rồi đó nha, ý vẫn chưa ra. … Đóng hồ sơ thám tử lại nào. Hỏi lại
> phần chưa rõ: Bạn muốn nói gì ở chỗ này?

Cách chạy:

- Daily: lớp đọc `apps/api/app/domains/readings/voice.py` khớp đúng chữ của ma trận direct đã duyệt
  (90 headline, 15 issue, 13 placement meaning). Bản lưu, share và saved snapshot luôn là direct;
  chữ không khớp (bản AI viết lại, natal, legacy) giữ nguyên direct.
- Tarot: `TarotVoice.ROAST` render cục bộ từ `apps/api/app/domains/tarot/voice.py`. Bài Roast không
  được gửi đi viết lại bằng AI, nên không có thêm nội dung nào ra provider.
- Gate: `ContentReviewAgent`, Tarot quality gate, `pnpm tarot:audit` (mọi voice) và
  `pnpm content:review` (thêm một lượt Roast) đều phải qua; test giữ danh sách từ cấm.
- Trên app, giọng này tên là **"Cà khịa"** trong Mình → "Giọng của Lá"; giao diện giống hệt Direct,
  chỉ câu chữ đổi.
- **Duyệt câu chữ:** chủ sản phẩm đã duyệt bộ câu Roast hiện tại (Daily, Tarot, lời của Lá) ngày
  2026-10-11 để đưa cho người dùng thật. Câu mới hoặc sửa nghĩa phải duyệt lại.

## Lời của Lá

Lá là linh vật mầm cây trên app. Lá chào, chờ và phản hồi. Lá không đổi nghĩa bài đọc, không đoán
tương lai, không nói mình biết hết về người đọc và không nói thay người khác.

- **Nguồn:** content matrix `apps/api/app/domains/readings/companion.py`. Web đọc câu tĩnh qua
  file sinh `apps/web/src/shared/ui/la/laCatalog.generated.ts`. Sửa câu xong thì chạy
  `pnpm content:companion`; test sẽ báo nếu hai bên lệch nhau.
- **Câu cạnh note hôm nay:** mỗi vấn đề Daily có một câu Thẳng (tối đa 14 chữ) và một câu Cà khịa
  (tối đa 16 chữ), kèm một dòng ý nghĩa. Câu nhắc người đọc thử việc nhỏ trong thẻ, không lặp lại
  tiêu đề hay hành động.
- **Cà khịa:** tối đa một câu chọc vào hành vi trong bài đọc, không chọc vào con người, luôn có lối ra.
- **Luna:** chỉ nhận dòng ý nghĩa, không nhận câu viết sẵn. Gate dùng chung luật với câu viết sẵn.
  Người đọc chọn Cà khịa luôn thấy bản viết sẵn của cả thẻ, không bao giờ thấy nửa thẻ Luna, nửa thẻ
  Cà khịa.
- **Chờ duyệt (2026-10-13):** 15 cặp câu theo vấn đề và cặp câu dự phòng là câu mới. Ba câu Cà khịa
  cũ được sửa vì chạm chuẩn này: lời chào buổi trưa ("xem số phận"), lời chào buổi chiều ("Lá biết
  hết á") và một câu chờ ("Vũ trụ đang gõ"). Chủ sản phẩm cần duyệt trước khi đưa cho người dùng thật.

Nhãn persona trên app và thẻ chia sẻ giữ dạng **"Vibe · X"** (quyết định 2026-10-11; không đổi thành
"Chất X").

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
