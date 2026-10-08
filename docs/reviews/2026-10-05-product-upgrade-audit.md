# Rà soát nâng cấp sản phẩm Lá Lành — 05/10/2026

## Kết luận ngắn

Lá Lành hiện đã đủ ổn để tiếp tục **QA nội bộ và beta có kiểm soát**: onboarding ngắn, Home giải thích được sản phẩm dùng để làm gì, chart thật chạy, Radar giữ nguyên tắc riêng tư và các luồng chính vượt qua smoke test.

Sản phẩm chưa nên được xem là hoàn thiện về nội dung. Khoảng trống lớn nhất không còn là “thiếu màn hình”, mà là chất lượng diễn giải sau khi người dùng đã mở thêm dữ liệu. Tarot còn lặp ý, Bầu trời hôm nay mới hiển thị dữ liệu chung và lớp viết lại bằng model chưa được kiểm chứng bằng request trả phí thực tế.

## Những gì đang làm tốt

| Khu vực | Đánh giá | Bằng chứng |
|---|---|---|
| Onboarding | Gọn, chỉ hỏi ngày sinh trước, chưa ép đăng nhập | Welcome → ngày sinh → reveal → Home chạy xuyên suốt |
| Home | Promise rõ, note nằm sớm, điều hướng đúng 4 nhu cầu chính | Test Home và review trực tiếp ở viewport mobile |
| Birth chart | Dùng dữ liệu ephemeris thật, có giờ/nơi sinh và danh sách 34 tỉnh thành mới | Native asset guard và smoke flow pass |
| Radar hợp gu | Có nhập kín, hỗ trợ không rõ giờ sinh, không tự tạo hồ sơ hay đưa người kia vào pool | Radar experience audit pass |
| Quyền riêng tư | Có consent theo mục đích, guard chống gửi dữ liệu cá nhân thô sang lớp rewrite | Privacy guard pass |
| Vận hành | Contract, lint, typecheck, unit/integration và QA build đều xanh | `pnpm check` pass toàn bộ |

## Nâng cấp nên làm tiếp theo

### P1 — Làm Tarot thành một bài đọc thống nhất, không phải ba đoạn ghép lại

Content gate hiện còn **36 cảnh báo mức trung bình**, phần lớn là câu và hành động bị lặp giữa các vị trí Tarot. Cần:

- Cho mỗi vị trí một vai trò riêng: chuyện đang diễn ra, điều chưa nhìn thấy, bước có thể thử.
- Viết một đoạn tổng hợp mới từ quan hệ giữa các lá; không lấy nguyên nghĩa lá đầu làm kết luận.
- Bỏ mốc thời gian áp đặt kiểu “24 giờ tới” nếu câu hỏi không có thời hạn.
- Kiểm tra câu lặp giữa tiêu đề, phần giải nghĩa và hành động trước khi phát hành.

### P1 — Biến “Bầu trời hôm nay” từ bảng dữ liệu thành giá trị cá nhân

Hiện tại tên hành tinh/cung đã được Việt hóa và giải thích đây là dữ liệu chung. Bước kế tiếp cần so transit hiện tại với natal chart để trả lời ba câu rõ ràng:

1. Điều gì đang được kích hoạt?
2. Nó có thể xuất hiện trong tình huống đời thường nào?
3. Dữ kiện nào nên quan sát thay vì tin ngay?

Nếu chưa có natal chart đầy đủ, giao diện phải nói rõ đang đọc lớp nào và giá trị bị giới hạn ở đâu.

### P1 — Chạy lớp rewrite bằng model theo chế độ shadow trước khi bật cho người dùng

Luna/GPT chỉ được viết lại từ một brief đã đóng và khử dữ liệu nhận dạng; không được tự tính chart, tự thêm luận điểm hay nhận ngày/giờ/nơi sinh thô. Thứ tự an toàn:

1. Chạy trên corpus tổng hợp, không có dữ liệu người thật.
2. So đầu ra với bản deterministic bằng content gate.
3. Review thủ công các mẫu Tarot, natal và Radar.
4. Chỉ bật theo feature flag khi có budget cap và fallback deterministic.

Chưa thực hiện paid probe trong đợt rà soát này, vì tài khoản hiện chưa có credit và mọi phát sinh chi phí cần xác nhận tại thời điểm chạy.

### P2 — Tách bundle web

Production bundle JavaScript hiện khoảng **730 kB** (gzip khoảng **206 kB**) và Vite cảnh báo chunk lớn hơn 500 kB. Nên lazy-load Tarot, Radar, Studio và các trang insight; giữ onboarding và Home trong entry chunk nhẹ.

### P2 — QA app thật trên thiết bị

Mobile release guard đã pass, nhưng cần thêm một vòng kiểm tra trên iOS/Android thật hoặc simulator: time picker, safe area, bàn phím, deep link, chia sẻ ảnh và xóa dữ liệu. Web vẫn là bản QA/reference; app mới là sản phẩm chính.

### P2 — Đo trải nghiệm thay vì chỉ đo lỗi kỹ thuật

Thêm event không chứa nội dung nhạy cảm cho các điểm:

- hoàn thành onboarding;
- mở full chart;
- đọc hết note/Tarot/Radar;
- bấm “hữu ích/không hữu ích”;
- quay lại ngày hôm sau.

Không ghi câu hỏi Tarot, tên người được Radar hoặc dữ liệu sinh vào analytics.

## Thay đổi đã thực hiện trong đợt rà soát

- Sửa ngôn ngữ natal để bỏ các cụm chuyên môn mơ hồ như “góc rộng”, “hai phần gọi nhau”, “nén một nhu cầu”.
- Ngăn tiêu đề natal bị lặp nguyên văn ở câu đầu nội dung.
- Dịch tên hành tinh, cung và trạng thái nghịch hành trên trang Bầu trời hôm nay; thêm giải thích giới hạn của dữ liệu chung.
- Mở rộng content release gate từ Daily + Natal thành Daily + Natal + Tarot cho 10 persona tổng hợp.
- Thêm phát hiện câu lặp giữa các phần của một bài đọc.
- Sửa typing cho các script kiểm tra rewrite worker và paid probe.

## Bằng chứng kiểm thử

- Content matrix: 630 biến thể daily, 23 concept quan hệ, 8 chủ đề Radar.
- Tarot knowledge: 78 lá × 6 bối cảnh, kèm sample trải ba lá.
- Rewrite corpus: 670 case tổng hợp trên 13 surface.
- Web: 39 file test, 138 test pass.
- API: 494 test pass.
- Ruff, mypy, TypeScript và ESLint: pass.
- QA smoke: schema, API proxy, SPA deep-link và guest → birth → daily note pass.

## An ninh và quyền riêng tư

- OpenAI nêu dữ liệu API không được dùng để huấn luyện mặc định, nhưng abuse-monitoring log có thể được giữ tới 30 ngày; vì vậy Lá Lành vẫn phải gửi brief đã tối thiểu hóa dữ liệu và đặt `store: false`, không dựa vào lời hứa “không train” để gửi dữ liệu sinh thô. Nguồn: [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint).
- App cần tiếp tục bám ba nhóm kiểm soát của OWASP MASVS: lưu trữ an toàn, kết nối mạng an toàn và tối thiểu hóa/minh bạch dữ liệu. Nguồn: [OWASP MASVS](https://mas.owasp.org/MASVS/).
- Việt Nam đã có Luật Bảo vệ dữ liệu cá nhân năm 2025; trước beta rộng cần legal review chính thức cho consent, thời hạn lưu, quyền xóa và xử lý dữ liệu của người thứ hai trong Radar. Nguồn tra cứu: [Thư viện số Quốc hội](https://thuvienso.quochoi.vn/handle/11742/103334).

## Quyết định phát hành

- **Có thể:** QA nội bộ, beta nhỏ bằng deterministic content hiện tại.
- **Chưa nên:** quảng bá lớp AI rewrite hoặc coi Tarot là hoàn thiện.
- **Không được:** gửi dữ liệu sinh, câu hỏi riêng tư hoặc danh tính người thứ hai sang model/analytics khi chưa có consent phù hợp và cơ chế tối thiểu hóa dữ liệu.
