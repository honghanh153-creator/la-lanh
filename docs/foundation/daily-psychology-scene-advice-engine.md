# Daily Psychology Scene & Advice Engine

Trạng thái: implemented, giọng direct
Phiên bản runtime: `daily-direct-meaning-v6`; selection: `daily-semantic-eligibility-v3`
Ngày rà soát: 2026-10-09 (đã kiểm thử local, chưa deploy beta)

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
- sáu headline mô tả cùng một tình huống, không dùng động từ khuyên;
- tám cảnh minh họa có chủ thể và dấu hiệu quan sát được;
- tám hành động nhỏ hợp với các cảnh trong cùng họ vấn đề;
- `meaning` và `takeaway` nói rõ ý muốn diễn đạt; bài "Đọc thêm" dùng chúng để giải thích đúng tình huống trên Home, không lấy một đoạn natal nói về vấn đề khác;
- `observation_question` hỏi một kết quả cụ thể sau hành động, không dùng câu chung chung về "một khác biệt nhỏ";
- `scene_anchors` và `action_anchors` giúp gate bắt việc đổi sang vấn đề khác;
- source IDs để audit phương pháp, không hiển thị như factual claim.

V6 có 15 họ vấn đề: mười họ cũ và năm họ mới — kiểm tra thời gian trước khi nhận việc, trả lời quá nhanh, sửa lời đã gửi, hỏi góp ý cụ thể, nói rõ điều cần giúp. Biến thể hành động cho lens quan hệ hỏi cả nhu cầu/thời gian của người kia; không chỉ thêm tiền tố vào câu auto.

## 4. Selection và chống lặp

```text
chart factors + context opt-in + local date
  → eligible issue family
  → one authored situation with compatible headline / scene / advice variants
  → server-owned meaning brief
  → evidence / anti-influence / editorial / meaning / privacy gates
```

- Cùng chart, context và ngày địa phương luôn replay cùng output.
- Chọn ý nghĩa trước: vai trò hero/primary, hành tinh + domain + sign, cặp hành tinh đã có rule, góc/độ mạnh/pha và nhà có dữ kiện chính xác. Chỉ dùng nhà/angle khi precision exact; lens người dùng chọn có ưu tiên so với bối cảnh từ nhà.
- Các rule đủ điều kiện được xếp hạng; ngày chỉ xoay giữa những rule đồng hạng và biến thể trong cùng ý nghĩa. Hash chart, ID người dùng, thứ tự factor và cách format orb không chọn tính cách.
- Mỗi họ có 6 × 8 × 8 = 384 bộ `hook + scene + advice`. Test giữ 365 ngày khác nhau cho date-only, ambiguous, full chart và các lens được kiểm tra. Đây không phải 384 phát hiện khác nhau hoặc cam kết không lặp vô hạn; chu kỳ biến thể trong họ hữu hạn.
- Cặp Moon/Mars applying và separating có thể dùng ví dụ “định trả lời” và “sửa lời đã gửi” với hành động khác nhau. Pha là góc biên tập cho ví dụ, không chứng minh có tin nhắn/va chạm thật.
- Không đủ rule thì dùng ví dụ trung tính, không đoán hoàn cảnh. Date-only có giới hạn chỉ đọc tổng quát từ Sun. Hai chart có cùng dữ kiện được biết có thể nhận cùng ý nghĩa/câu chữ; không ép khác bằng chi tiết cá nhân bịa ra.
- Không lưu lịch sử note để chống lặp.

Cohort local 20 chart tổng hợp cùng mùa Sun: 14 card, 12 ý nghĩa, 9 họ hành vi; còn các nhóm trùng cần mở rộng rule có căn cứ. Đây không phải tỷ lệ trùng của toàn bộ người dùng. Xem `docs/reviews/2026-10-09-daily-semantic-personalization-content-receipt.md` cho mẫu và counterfactual tests.

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

### Cấu trúc hiển thị v7 (11.10.2026, Issue #5 / B1a)

Audit 11.10.2026 cho thấy đoạn chính ghép bốn câu từ bốn bảng, không có chủ ngữ, lặp ý cảnh/hành động và nhét giới hạn vào giữa bài. Từ `daily-direct-meaning-v7` và `daily-semantic-eligibility-v4`:

- `thesis` gồm đúng hai câu có chủ ngữ: câu xu hướng riêng của bạn (`placement`/`pair` meaning, đều bắt đầu bằng "Bạn …") rồi `issue.takeaway` (cũng có chủ ngữ). `issue.meaning` chỉ còn trong `core_meaning` của brief, không hiển thị.
- Giới hạn không nằm trong đoạn chính. Cảnh minh họa được đánh dấu bằng tiêu đề "Ngoài đời có thể trông như…" và `scene_status`. Date-only được ghi rõ ở claim "(chỉ từ ngày sinh)". Trang chỉ còn một hộp Lưu ý; framework disclosure nằm trong phần "Vì sao hôm nay?" đóng sẵn.
- Ngữ cảnh mở câu cảnh ("Trong công việc hoặc chuyện học, khi …"), không còn câu cụt "Ví dụ …". Ghi chú đã lưu ở v6 vẫn được nhận diện cho giọng Cà khịa (`LEGACY_ARENA_LEADS`, khớp `issue.meaning`).
- Note Detail luôn có "Thử một việc nhỏ": có thử nghiệm giữ được khi exact, chỉ hiện câu hành động khi date-only hoặc giờ không chính xác. "Vì sao hôm nay?" chỉ là một nhãn; link ở Home mở thẳng panel.
- Brief cho Luna không còn câu giới hạn trong `reader_takeaway`; trạng thái minh họa vẫn đi qua `scene_status` và gate rewrite.


Daily transit, nếu có, giữ tên hành tinh/góc/orb/pha từ claim canonical và giải thích ngắn ý nghĩa của pha. Không ghép nó thành một câu dự báo chuyện đời thường. Evidence gate v2 chuẩn hóa dấu tiếng Việt khi đối chiếu pha nhưng vẫn từ chối pha không có trong chart.

Renderer version chứa fingerprint của catalog Daily. Cache key thay đổi khi biên tập lại nội dung, kể cả câu hỏi sau thử nghiệm, mà không thay plan/chart hoặc lịch sử đã đóng băng.

Home truyền góc đang chọn vào đường dẫn "Đọc thêm" và preview chia sẻ. Chỉ chấp nhận năm context đã biết; giá trị lạ trở về `auto`, không chuyển tiếp dữ liệu tùy ý trong URL. Context có query key riêng và không lấy note auto làm fallback khi context đó chưa tải được. Nút giữ thử nghiệm gửi đúng lens và revision đang thấy. Lưu và tạo share artifact cũng dùng revision hiện trên màn hình thay vì dựa vào request khác vừa chạy.

Daily compiler hash toàn bộ blueprint và chuyển brief qua `DailySafePayload`/`PrivacyMinimiser`. Prompt `surface-rewrite-v3` dùng hai mẫu direct để dạy cách viết, không ép lặp nguyên câu cho tình huống khác. Brief mang cả xu hướng, nhu cầu cạnh tranh, cảnh quan sát được, hành động và giới hạn. Luna chỉ viết lại ý nghĩa đã chọn; không tự đổi vấn đề, suy ra lịch sử cá nhân hoặc cố tạo độc nhất. Compiler từ chối baseline chưa qua gate và house/angle evidence không đủ precision. Đợt này kiểm thử compiler bằng fixture, không gọi Luna trả phí.

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
