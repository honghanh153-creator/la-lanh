# Daily Psychology Scene & Advice Engine

Trạng thái: implemented, giọng direct
Phiên bản runtime: `daily-direct-meaning-v4`
Ngày rà soát: 2026-10-07

## 1. Mục tiêu sản phẩm

Daily Note có hai việc khác nhau và không được trộn:

1. **Cảnh dễ gặp hôm nay** — sự việc, dấu hiệu hoặc hành động có thể quan sát. Phần này không khuyên, không chẩn đoán và không nói sự việc chắc chắn sẽ xảy ra.
2. **Hôm nay thử thế này** — một hành động nhỏ, đảo ngược được và có cách biết mình đã thử xong.

Chiêm tinh xếp hạng góc đọc và bối cảnh. Ma trận tâm lý giúp chuyển góc đó thành tiếng Việt đời thường. Tâm lý học không được dùng như bằng chứng rằng một vị trí chiêm tinh gây ra hành vi.

## 2. Mười nguồn biên tập

Đây là mười nguồn neo được chọn vì độ phủ cho hành vi hằng ngày; “top 10” không phải bảng xếp hạng học thuật tuyệt đối.

| Nguồn | Dimension dùng trong engine | Không được suy ra |
|---|---|---|
| Daniel Kahneman — *Thinking, Fast and Slow* | phản ứng nhanh, dữ kiện và suy đoán | mức thông minh hoặc lỗi nhận thức cố định |
| Robert Cialdini — *Influence* | ảnh hưởng xã hội và shortcut khi lựa chọn | kỹ thuật thao túng người khác |
| Carol Dweck — *Mindset* | phản ứng với thử thách và một lần vấp | chia người dùng thành hai kiểu người |
| Mihaly Csikszentmihalyi — *Flow* | độ khó, tập trung và phản hồi | công thức bảo đảm năng suất/hạnh phúc |
| Daniel Goleman — *Emotional Intelligence* | nhận biết cảm xúc và khoảng dừng | điểm số hoặc chẩn đoán năng lực cảm xúc |
| Kristin Neff — *Self-Compassion* | giọng tự trách và cách đối xử với mình | thay thế chăm sóc sức khỏe tâm thần |
| Russ Harris — *The Happiness Trap* | tách suy nghĩ khỏi dữ kiện phải làm theo | điều trị ACT trong ứng dụng |
| Marshall Rosenberg — *Nonviolent Communication* | quan sát, cảm xúc, nhu cầu, đề nghị | đoán nhu cầu hoặc ý định người khác |
| Carol Tavris & Elliot Aronson — *Mistakes Were Made (But Not by Me)* | tự biện hộ và chi phí chìm | kết luận ai đang tự lừa dối |
| Lee Ross & Richard Nisbett — *The Person and the Situation* | ảnh hưởng của hoàn cảnh | nhãn tính cách từ một tình huống |

Runtime chỉ lưu metadata, nguyên tắc biên tập và copy tiếng Việt do Lá Lành tự viết. Không lưu đoạn trích hoặc bản số hóa của sách.

## 3. Ma trận

Mỗi `DailyIssuePattern` có:

- `arenas`: quan hệ, giao tiếp, công việc/học tập, năng lượng hoặc chăm mình;
- bốn headline mô tả cùng một tình huống, không dùng động từ khuyên;
- ba cách viết cùng cảnh có chủ thể và dấu hiệu quan sát được;
- bốn hành động hợp với mọi cách viết của cảnh đó;
- `meaning` và `takeaway` nói rõ ý muốn diễn đạt; bài "Đọc thêm" dùng chúng để giải thích đúng tình huống trên Home, không lấy một đoạn natal nói về vấn đề khác;
- `observation_question` hỏi một kết quả cụ thể sau hành động, không dùng câu chung chung về "một khác biệt nhỏ";
- `scene_anchors` và `action_anchors` giúp gate bắt việc đổi sang vấn đề khác;
- source IDs để audit phương pháp, không hiển thị như factual claim.

V1 có các họ vấn đề: thiếu ngữ cảnh, quá nhiều việc mở, đổi kế hoạch, so sánh, tự động chăm người khác, mệt vì phải chọn, chờ hoàn hảo, áp lực đồng thuận, né va chạm nhỏ và bảo vệ lựa chọn cũ.

## 4. Selection và chống lặp

```text
chart factors + context opt-in + local date
  → eligible issue family
  → one authored situation with compatible headline / scene / advice variants
  → server-owned meaning brief
  → evidence / anti-influence / editorial / meaning / privacy gates
```

- Cùng chart, context và ngày địa phương luôn replay cùng output.
- 10 tình huống × 4 headline × 3 scene × 4 advice có 480 bộ câu trong lens general. Test 365 ngày không trùng bộ ba `hook + scene + advice`. Đây là biến thể câu chữ, không phải 480 insight độc lập. Lens hẹp có ít tình huống hơn và có thể lặp sớm hơn.
- Chart signature xoay các slot trong catalog; nó không tạo câu tâm lý mới và không đọc raw DOB. Không khẳng định mỗi người có vấn đề khác nhau chỉ vì chart khác.
- Khi hai lens chọn cùng tình huống, hành động có thể giống nhau. Không đổi advice chỉ để trông cá nhân hóa.
- Không lưu lịch sử note để chống lặp.

## 5. Content contract

Scene đạt chuẩn khi:

- có người/việc/bối cảnh và một dấu hiệu nhìn thấy được;
- không bắt đầu bằng “hãy”, “thử”, “nên”, “đừng”;
- không dùng `pattern`, `cơ chế`, `năng lượng vũ trụ`, thuật ngữ trị liệu hoặc nhãn bệnh;
- dùng xác suất mềm ở nhãn UI “có thể gặp”, không dự báo chắc chắn.
- Home giữ title 3–11 từ, scene 8–40 từ, action 4–24 từ, tổng tối đa 70 từ. Mỗi câu scene không quá 28 từ.

Advice đạt chuẩn khi:

- dùng một động từ như hỏi, viết, chọn, nói, đặt, kiểm tra, tắt hoặc đợi;
- đủ nhỏ để thử trong ngày và có điểm dừng;
- không chỉ đạo y tế, pháp lý, tài chính, giám sát hoặc thao túng;
- giữ cùng `issue_key` với scene.
- Không yêu cầu người dùng làm việc "trước khi đồng ý" nếu cảnh đã mô tả họ gật đầu rồi. Hành động phải làm được ở thời điểm trong cảnh.

## Meaning brief và Luna

`SemanticBlueprint.daily_meaning` chứa `core_meaning`, `reader_takeaway`, `scene_status=illustrative`, `scene_anchors`, `action_anchors` và câu hỏi biên tập `observation_question`. Trường câu hỏi cho phép vắng mặt để đọc bản cũ. Cảnh là minh họa, không phải sự kiện app quan sát được về người dùng. Brief không nhận hoàn cảnh riêng, chat hay thông tin sinh mới.

Ví dụ áp lực nhóm: câu hỏi "Bạn đã hiểu chỗ mình vừa hỏi lại chưa?" được dùng thống nhất khi hiển thị thử nghiệm, khi người dùng giữ thử nghiệm và khi tải lại. Backend lấy từ revision đã chấp nhận; client không được gửi lại lời khuyên hoặc câu hỏi tùy ý.

Daily transit, nếu có, giữ tên hành tinh/góc/orb/pha từ claim canonical và giải thích ngắn ý nghĩa của pha. Không ghép nó thành một câu dự báo chuyện đời thường. Evidence gate v2 chuẩn hóa dấu tiếng Việt khi đối chiếu pha nhưng vẫn từ chối pha không có trong chart.

Renderer version chứa fingerprint của catalog Daily. Cache key thay đổi khi biên tập lại nội dung, kể cả câu hỏi sau thử nghiệm, mà không thay plan/chart hoặc lịch sử đã đóng băng.

Home truyền góc đang chọn vào đường dẫn "Đọc thêm" và preview chia sẻ. Chỉ chấp nhận năm context đã biết; giá trị lạ trở về `auto`, không chuyển tiếp dữ liệu tùy ý trong URL. Context có query key riêng và không lấy note auto làm fallback khi context đó chưa tải được. Nút giữ thử nghiệm gửi đúng lens và revision đang thấy. Lưu và tạo share artifact cũng dùng revision hiện trên màn hình thay vì dựa vào request khác vừa chạy.

Daily compiler hash toàn bộ blueprint và chuyển brief qua `DailySafePayload`/`PrivacyMinimiser`. Prompt `surface-rewrite-v3` dùng hai mẫu direct để dạy cách viết, không ép lặp nguyên câu cho tình huống khác. Luna chỉ đổi cách diễn đạt của title/scene/action đã chọn.

Gate `daily-home-rewrite-gates/v2` kiểm tra độ dài, câu khó hiểu đã biết, anchor cảnh/hành động, lời khuyên chen vào scene và mâu thuẫn thời điểm. `meaning-gate-vi-v2` gọi cùng gate này trước khi xuất bản fallback, không chỉ sau khi Luna viết. Quy tắc tự động không thay thế việc đọc và hiểu của người thật.

Projection deterministic hiện tại có thể nhận revision mới khi blueprint Daily thay đổi, trong cùng plan và owner scope. Bản share/lưu và revision lịch sử không bị sửa. Generated projection cũ vẫn theo cơ chế available update hiện có; không tự ghi đè nội dung mô hình đã được kích hoạt.

## 6. UI contract

- Home chỉ hiển thị scene và lời nhắc tách khối.
- Home không hiển thị “Vì sao dành cho bạn?” hoặc “Đọc từ ngày sinh/lá số”.
- Evidence chart và framework disclaimer vẫn có ở Note Detail.
- Feedback, mood, share, context switch và CTA giữ lời nhắc vẫn hoạt động như trước.

## 7. Security, privacy và safety

- Engine chạy local trên backend, không gọi mô hình hoặc search lúc runtime.
- Matrix không nhận raw DOB, giờ sinh, nơi sinh, tọa độ, mood hay free text.
- Web research chỉ phục vụ biên tập source metadata; dữ liệu người dùng không đi vào truy vấn.
- Không sinh nội dung chẩn đoán, điều trị, định mệnh hoặc khuyến nghị high-stakes.
- Content Studio (nếu dùng) không được bỏ qua năm gate và không được sửa evidence facts.

## 8. Verification

- đủ 10 source IDs, không có source mồ côi;
- 365 daily cards khác nhau và đều publishable;
- đủ năm context opt-in;
- scene không chứa advice;
- scene/action cùng issue key;
- 10 synthetic personas qua content-review agent;
- Home test xác nhận disclosure đã được chuyển khỏi first scan.

## 9. Reference pages

- Penguin Random House — *Thinking, Fast and Slow*: https://www.penguinrandomhouse.com/books/89308/thinking-fast-and-slow-by-daniel-kahneman/
- Influence at Work — books and principles: https://www.influenceatwork.com/books-and-publications/
- Penguin Random House — *Mindset*: https://www.penguinrandomhouse.com/books/44330/mindset-by-carol-s-dweck-phd/9780345472328/
- Harper Academic — *Flow*: https://www.harperacademic.com/book/9780061339202/flow/
- Penguin Random House — *Emotional Intelligence*: https://www.penguinrandomhouse.com/books/69105/emotional-intelligence-by-daniel-goleman/9780553804911/
- Kristin Neff — books on self-compassion: https://self-compassion.org/books-by-kristin-neff/
- Shambhala — *The Happiness Trap*: https://www.shambhala.com/the-happiness-trap-9781645470403.html
- Center for Nonviolent Communication — *Nonviolent Communication*: https://www.cnvc.org/store/nonviolent-communication-a-language-of-life
- Carol Tavris & Elliot Aronson — *Mistakes Were Made (But Not by Me)*.
- Lee Ross & Richard Nisbett — *The Person and the Situation*.
