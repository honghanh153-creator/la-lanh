# Lá Lành — phương pháp xây knowledge corpus diễn giải Western

Trạng thái: implemented foundation v4  
Ngày rà soát: 2026-09-23  
Methodology version: `western-synthesis-method-2026-09-v1`  
Runtime knowledge version: `western-interpretation-matrix-v4`

## 1. Ranh giới nguồn

“Top 5” dưới đây là năm đầu sách phù hợp nhất với bài toán của Lá Lành, không phải bảng xếp hạng tuyệt đối của toàn ngành. Bản cập nhật này dùng mô tả chính thức của tác giả/nhà xuất bản, mục lục công khai và khái niệm cấp phương pháp để thiết kế taxonomy. Lá Lành không tải, chép, nhúng, fine-tune hoặc tái tạo nguyên văn nội dung sách.

Copy tiếng Việt trong runtime do sản phẩm tự biên tập, được version, test và review độc lập. Muốn dùng trích đoạn hay nội dung chi tiết từ bất kỳ sách nào phải có quyền sử dụng riêng.

## 2. Năm sách nền cho engine hiện tại

| Sách | Phần phương pháp được dùng | Dịch thành cấu trúc engine | Không được suy diễn |
|---|---|---|---|
| Steven Forrest — *The Inner Sky* | Cách đọc hướng lựa chọn và quyền tự quyết; planet–sign–house là một tổ hợp sống | `InterpretiveLens.GROWTH`, câu hỏi mở, micro-action có thể đảo ngược | Không biến “tiềm năng” thành định mệnh hoặc lời thúc ép |
| Stephen Arroyo — *Chart Interpretation Handbook* | Tổng hợp planet, sign, house, aspect; dùng element như nhịp năng lượng thay vì đọc từng keyword rời | `PLANET_PERSPECTIVES`, `ELEMENTS`, synthesis theo nhu cầu–cách vận hành–bối cảnh | Không gắn một element với phẩm chất tốt/xấu cố định |
| Howard Sasportas — *The Twelve Houses* | Nhà là lĩnh vực trải nghiệm và nơi pattern biểu hiện; angular/succedent/cadent có chức năng khác nhau | `HOUSES`, `HOUSE_MODES`, manifestation theo vùng đời sống | Không đồng nhất nhà với cung; không đọc nhà khi giờ sinh chưa đủ chính xác |
| Sue Tompkins — *Aspects in Astrology* | Aspect là quan hệ động giữa hai chức năng; cần xét loại góc, orb, applying/separating và toàn cấu hình | `ASPECTS`, aspect child refs, orb bands, natal phase nuance | Không gọi trine là “tốt”, square là “xấu”, hoặc bỏ qua hai hành tinh con |
| Robert Hand — *Planets in Transit* | Transit là quá trình kích hoạt theo thời gian, cần đặt trên nền natal và theo dõi mức độ/phase | 70% natal + 30% transit, một contact nổi bật, `approaching/exact/separating` | Không dự báo sự kiện chắc chắn hoặc dùng một ngày để chỉ thị quyết định lớn |

Nguồn công khai:

- [Steven Forrest — The Inner Sky và cách tiếp cận choice-centered](https://www.forrestastrology.com/blogs/astrology/august-2014-newsletter)
- [Stephen Arroyo — Chart Interpretation Handbook](https://books.google.com/books/about/Stephen_Arroyo_s_Chart_Interpretation_Ha.html?id=QgmfDwAAQBAJ)
- [Howard Sasportas — The Twelve Houses](https://books.google.com/books/about/The_Twelve_Houses.html?id=9b5evgAACAAJ)
- [Sue Tompkins — Aspects in Astrology](https://www.innertraditions.com/books/aspects-in-astrology)
- [Robert Hand — Planets in Transit](https://www.arhatmedia.com/blank-3)

## 3. Ma trận kiến thức v4

### 3.1 Lớp bằng chứng

1. `planet`: chức năng/nhu cầu nào đang hoạt động.
2. `sign`: chức năng đó vận hành theo phong cách nào.
3. `element`: cần nhịp gì để tự điều hòa; khi quá tải dễ lệch theo hướng nào.
4. `modality`: cách bắt đầu, duy trì hoặc thích nghi; blind spot của tốc độ đó.
5. `house`: pattern xuất hiện ở vùng đời sống nào.
6. `house_mode`: pattern có xu hướng đưa ra hành động, giữ ổn định hay phân phối/diễn giải.
7. `aspect`: hai chức năng cộng hưởng, thương lượng hay tạo ma sát ra sao.
8. `orb`: mức độ nên đặt pattern ở foreground hay background.
9. `natal aspect phase`: applying/separating chỉ thêm nuance về cách hai chức năng gọi nhau; không phải timing dự báo.
10. `degree`: giữ trong evidence để người dùng kiểm tra; không tự sinh diễn giải tâm lý từ ba dải độ đầu/giữa/cuối.
11. `motion`: direct/retrograde được giữ trong evidence; chưa tự sinh kết luận tâm lý trong prose.
12. `transit`: lớp thời gian kích hoạt natal pattern, luôn đứng sau natal.

### 3.2 Sáu lăng kính đầu ra

| Lens | Câu hỏi engine trả lời | Atom ưu tiên |
|---|---|---|
| `inner_pattern` | Hai nhu cầu bên trong đang phối hợp hoặc kéo nhau thế nào? | planet, sign, aspect, orb |
| `relationships` | Pattern dễ đi vào sự có qua có lại và kỳ vọng chưa nói ra thế nào? | planet relationships, element, house, aspect phase |
| `work` | Pattern ảnh hưởng cách ưu tiên, cộng tác, chịu trách nhiệm và hoàn thành ra sao? | planet work, modality, house mode |
| `regulation` | Khi quá tải, phản xạ bảo vệ nào bật lên và điều gì giúp hạ cường độ? | protection, element overload, retrograde, reversible action |
| `communication` | Điều nói ra, điều giữ lại và cách xử lý thông tin lệch nhau ở đâu? | sign style, protection, applying/separating, motion |
| `growth` | Có thể thử lựa chọn mới nào mà không phủ nhận phần đã quen? | modality blind spot, house mode, growth question |

Nếu user chọn background, background quyết định lens. Nếu không, Daily Note xoay lens theo ngày địa phương. Việc xoay chỉ đổi câu hỏi biên tập; factor refs và chart facts không đổi. Daily Note còn đi qua lịch biên tập ít nhất 365 ngày gồm lens, mode, micro-action và reflection cue để tránh việc hai ngày khác nhau nghe như cùng một note. Lịch này deterministic và stateless: không cần lưu prose hoặc lịch sử riêng tư của user để kiểm tra trùng.

## 4. Chống “nhét cả chart vào một đoạn”

Một note không được kể hết mọi lớp cùng lúc. Engine chọn một thesis và một lens, sau đó chỉ dùng các atom cần để trả lời lens đó. Các lớp còn lại nằm trong chương đọc sâu hoặc ngày khác.

Giới hạn runtime:

- mỗi section tối đa 85 từ tách theo bộ đếm tiếng Việt hiện tại;
- toàn candidate tối đa 240 từ;
- một hero aspect hoặc một cặp factor độc lập;
- một house context nếu hợp lệ;
- một transit đủ salience;
- evidence receipt giữ nguyên factor refs, không dựa vào prose để chứng minh fact.

### 4.1 Grammar chống câu vô nghĩa

- Luôn gọi đúng hai hành tinh/điểm và nói rõ nhu cầu riêng của từng phần trước khi mô tả aspect.
- Không ép hai vế đối lập khi hai vị trí dùng cùng nguyên tố; nhu cầu chung chỉ được nói một lần.
- Orb chỉ điều chỉnh trọng số đọc bằng lời đời thường: rõ, đáng chú ý hoặc nét phụ. Không xuất bản shorthand như “sắc độ nền”.
- Degree, house mode và thuật ngữ kỹ thuật ở evidence khi chúng không làm câu đời thường rõ hơn.
- Editorial gate chặn vế gần trùng trong cùng section, không chỉ chặn hai section giống hệt.
- Matrix regression phải quét đủ 6 aspect × 3 dải orb × các cặp cung cùng nguyên tố trước release.

## 5. Những gì chưa được thêm

- Dignity, sect, rulership/dispositor, profection, progression, solar return và aspect pattern lớn chưa có dữ liệu/contract đủ chặt trong engine hiện tại.
- Không dùng Sabian symbols, critical degrees hoặc decan như chân lý tâm lý.
- Corpus này chỉ dành cho Western tropical. Jyotish tiếp tục fail-closed ở mức structural cho tới khi có corpus, chuyên gia và golden tests riêng.
- Không suy giọng văn người dùng từ chart. Chart quyết định nội dung; user quyết định cách muốn nghe.

## 6. Release và review

Mỗi thay đổi atom phải:

1. tăng `knowledge_version` hoặc `methodology_version`;
2. nêu nguồn phương pháp và ranh giới transform;
3. qua coverage test 12 cung, 12 nhà, body launch, 6 aspect và 6 lens;
4. qua evidence, anti-influence, editorial, privacy gates; riêng editorial phải bắt lặp nội câu và shorthand nội bộ;
5. benchmark near-neighbor chart để phát hiện copy kiểu ai đọc cũng thấy đúng;
6. được chuyên gia chiêm tinh review trước khi gắn nhãn “expert-reviewed”.
