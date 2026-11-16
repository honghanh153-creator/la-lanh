# Danh sách việc ứng viên cho thử nghiệm cặp A/B (15.11.2026)

Ghi chú: tài liệu chỉ để đọc. Chưa chia A/B; owner bốc thăm. Mọi ví dụ đều là dữ liệu giả.

## Cách chọn

- Đọc từ `origin/collab/integration` @ `cfae0ee`: `docs/plans/2026-11-03-daily-v2-gap-register.md` (#177), `docs/plans/2026-11-02-daily-v2-content-quality-plan.md`, `docs/user-stories/US-03`, `US-20`, `US-21`; các issue #143, #180, #190, #6, #14; các issue fix-forward đang mở; code web và API của từng việc.
- Tiêu chí: việc sản phẩm có thật và chưa làm, cỡ S hoặc M, xong trong 1–2 PR, viết được 3–6 AC.
- Đã loại:
  - quyền riêng tư và dữ liệu cá nhân, câu chữ khủng hoảng, xóa dữ liệu, thanh toán, đăng nhập, Luna, Nơi bình yên, cầu nối Sheet, script vận hành;
  - chia sẻ và thu hồi link, Radar, mood, nhập giờ hoặc nơi sinh.
- Không trùng file với các PR #411, #404, #388, #354. Cũng tránh file của các PR đang mở khác:
  - #428 sửa `readings/service.py`, `renderers.py`, `knowledge.py`, `readingLabels.ts`;
  - #431 sửa `InsightsPage.tsx`, `ReadingDetailPage.tsx`, `InsightQueryStates.tsx`;
  - các PR bundle Daily sửa `copy_registry.json`.
- Đã bỏ vì đã xong hoặc bị chặn:
  - #143 E2, E3, E4 đã xong; E1 nằm trong #388.
  - PL-12 đã xong (`62f0868`).
  - #405 trùng `test_daily_variants.py` với #404.
  - Lô bundle nội dung Daily trùng `copy_registry.json`.
- Mọi câu chữ mới đi theo quy trình duyệt hiện hành (cờ chờ duyệt, Codex duyệt theo lô). Câu quyền riêng tư đang có phải giữ nguyên từng chữ.

## Tổng hợp ứng viên

| # | Tên | Nguồn | Mảng | Cỡ | Số AC | Đổi chữ? | File chính |
|---|---|---|---|---|---|---|---|
| K1 | Màn hỏi Tarot: chữ và gợi ý câu hỏi bằng lời thường | `TarotPage.tsx:54-85, 355, 400, 409, 477`; #6 (bỏ chữ thừa) | UI copy · Tarot | S | 5 | có | `features/tarot/TarotPage.tsx`, `TarotPage.test.tsx` |
| K2 | Bộ chọn góc đọc: bỏ "Context Dial", trình đọc màn hình nghe đủ | `SignalContextPicker.tsx:55, 68`; sổ lỗ hổng :187 (PL-35) | UI copy + trợ năng · Daily | S | 5 | có | `shared/ui/SignalContextPicker.tsx`, test mới `SignalContextPicker.test.tsx` |
| K3 | Note chi tiết: câu thông báo bằng lời thường | `NoteDetailPage.tsx:69, 79, 80, 112` | UI copy · Daily | S | 4 | có | `features/home/NoteDetailPage.tsx`, `NoteDetailPage.test.tsx` |
| K4 | Đã lưu: chữ trạng thái bằng lời thường | `SavedPage.tsx:49, 75, 134` | UI copy · Đã lưu | S | 4 | có | `features/saved/SavedPage.tsx`, `SavedPage.test.tsx` |
| K5 | Home tự sang note ngày mới sau nửa đêm | sổ lỗ hổng :184 (PL-10); `AppProviders.tsx:19-21`; `HomePage.tsx:99-109` | Web UX · Daily | M | 4 | không | `features/home/HomePage.tsx`, `HomePage.test.tsx` |
| K6 | Bầu trời hôm nay: giờ theo giờ Việt Nam, tự làm mới khi qua ngày | `CurrentSkyPage.tsx:46, 55` (giờ đang theo múi giờ của máy) | Web UX · Khám phá | M | 4 | không | `features/insights/CurrentSkyPage.tsx`, `CurrentSkyPage.test.tsx` |
| K7 | Note dự phòng đổi tiêu đề theo ngày | sổ lỗ hổng :175 (PL-6, PL-9); `daily/service.py:180, 247, 472` | Nội dung · Daily | M | 5 | có | `apps/api/app/domains/daily/service.py`, `tests/daily/test_daily_service.py` |
| K8 | Lời chào và câu chờ của Lá: lời thường, đổi theo ngày | sổ lỗ hổng :175 (PL-6 "Câu của Lá lặp"); `companion.py:201, 224` | Nội dung · Lá | M | 5 | có | `readings/companion.py`, `laCatalog.generated.ts`, `shared/ui/la/laVoice.ts`, `tests/readings/test_companion.py`, `la.test.tsx` |
| K9 | Trang Cách tính: giải thích hệ nhà và Ayanamsa bằng lời thường | `CalculationSettingsPage.tsx:28-35`; `insightConfig.ts` | UI copy · Khám phá | S | 4 | có | `features/insights/CalculationSettingsPage.tsx`, `insightConfig.ts` |
| K10 | Thẻ "có bản đọc mới": bỏ câu giải thích cơ chế | `ReadingUpdateGift.tsx:30, 36`; quy tắc owner "không giải thích cơ chế" | UI copy · Daily | S | 4 | có | `shared/ui/ReadingUpdateGift.tsx`, `ReadingUpdateGift.test.tsx` |
| K11 (dự bị) | Engine chọn góc: không tạo vòng lặp khi đẩy sự kiện lên | #397; `sky_selection.py:980-988` | Engine · Daily | S | 3 | không | `daily/sky_selection.py`, `tests/daily/test_sky_selection.py` |
| K12 (dự bị) | Bầu trời hôm nay: chữ trạng thái bằng lời thường | `CurrentSkyPage.tsx:58` ("Phiên đọc đã khép lại", "Trạm Bắt Sóng") | UI copy · Khám phá | S | 3 | có | `CurrentSkyPage.tsx` (trùng file K6) |

## AC nháp

Cách viết: **Cho** (Given) / **Khi** (When) / **Thì** (Then).

### K1 — Màn hỏi Tarot: chữ và gợi ý câu hỏi bằng lời thường
1. Cho màn hỏi Tarot đang mở. Khi người dùng đọc dòng trên tiêu đề. Thì không còn "Trạm bắt sóng bên trong bạn"; thay bằng một câu nói rõ màn này để làm gì.
2. Cho bước chọn lá bị lỗi mạng. Khi lỗi hiện ra. Thì câu báo lỗi nói thẳng là mạng lỗi và lá đã chọn vẫn được giữ, không dùng "hụt một nhịp".
3. Cho bước xòe bài không bắt đầu được. Khi lỗi hiện ra. Thì câu báo lỗi không dùng chữ "xòe" và bảo người dùng làm gì tiếp.
4. Cho 18 câu hỏi gợi ý theo 6 chủ đề. Khi rà toàn bộ. Thì không câu nào dùng "nhịp" hay ẩn dụ, không có hai câu trùng nhau, mỗi câu dưới 20 chữ.
5. Cho các test hiện có của `TarotPage`. Khi chạy `pnpm check`. Thì mọi test đều qua và test kiểm tra câu cũ được đổi sang câu mới.

### K2 — Bộ chọn góc đọc
1. Cho bảng chọn góc đọc đang mở. Khi người dùng nhìn dòng nhỏ trên tiêu đề. Thì không còn chữ tiếng Anh "Context Dial"; dòng này dùng tiếng Việt thường.
2. Cho câu "Lựa chọn này không được lưu thành sở thích." Khi sửa chữ trong bảng. Thì câu này giữ nguyên từng chữ.
3. Cho trình đọc màn hình đang bật. Khi người dùng di tới một lựa chọn. Thì nghe được cả tên lựa chọn và dòng mô tả bên dưới.
4. Cho một lựa chọn đang tải. Khi trình đọc màn hình tới lựa chọn đó. Thì nghe được "đang đổi góc".
5. Cho test mới `SignalContextPicker.test.tsx`. Khi chạy test. Thì test kiểm tra tên truy cập (accessible name) của từng nút và kiểm tra câu quyền riêng tư không đổi.

### K3 — Note chi tiết
1. Cho người dùng vừa lưu note. Khi lưu xong. Thì câu báo là "Đã lưu" hoặc câu tương tự, không còn "nằm yên".
2. Cho người dùng vừa mở bản đọc mới. Khi mở xong. Thì câu báo không nhắc "các lớp trong chart" hay cơ chế bên trong.
3. Cho trang đang tải. Khi màn chờ hiện ra. Thì câu chờ nói rõ đang mở note, dưới 10 chữ.
4. Cho các câu về việc nhỏ và streak. Khi sửa chữ trong trang. Thì ý của các câu này giữ nguyên, test `NoteDetailPage` qua.

### K4 — Đã lưu
1. Cho trang Đã lưu đang tải. Khi màn chờ hiện ra. Thì câu chờ không còn "lật lại những note bạn đã giữ", mà nói thẳng là đang tải.
2. Cho người dùng chưa lưu note nào. Khi mở trang. Thì tiêu đề trống nói rõ là chưa có note đã lưu và chỉ cách lưu.
3. Cho người dùng vừa bấm bỏ lưu. Khi câu báo hiện ra. Thì câu báo vẫn có nút Hoàn tác và vẫn nói rõ 5 giây.
4. Cho câu về việc lưu trên máy (dòng 119-120). Khi sửa chữ. Thì câu này giữ nguyên từng chữ và test kiểm tra điều đó.

### K5 — Home tự sang note ngày mới sau nửa đêm
1. Cho Home đang mở lúc 23:58 giờ Việt Nam với note của ngày D. Khi đồng hồ qua 00:00 giờ Việt Nam. Thì trong vòng 1 phút Home tải note của ngày D+1.
2. Cho app nằm nền qua nửa đêm. Khi người dùng quay lại tab. Thì Home không hiện note ngày D như thể là note hôm nay.
3. Cho máy đặt múi giờ khác Việt Nam (ví dụ UTC). Khi qua 00:00 giờ Việt Nam. Thì Home vẫn đổi đúng theo ngày Việt Nam, không theo ngày của máy.
4. Cho cùng một ngày. Khi người dùng mở lại Home nhiều lần. Thì không có request thừa ngoài nhịp hiện tại và test bằng đồng hồ giả qua.

### K6 — Bầu trời hôm nay: giờ và làm mới
1. Cho máy đặt múi giờ UTC. Khi trang hiện giờ quan sát. Thì giờ hiện theo giờ Việt Nam và có ghi rõ là giờ Việt Nam.
2. Cho trang đang mở lúc 23:58 giờ Việt Nam. Khi qua 00:00. Thì trang lấy lại vị trí mới và giờ quan sát đổi sang ngày mới.
3. Cho trang nằm nền lâu hơn 1 giờ. Khi người dùng quay lại. Thì trang tự lấy lại dữ liệu.
4. Cho cùng dữ liệu. Khi chạy test bằng đồng hồ giả và múi giờ giả. Thì chuỗi giờ hiện ra giống nhau trên mọi máy.

### K7 — Note dự phòng đổi tiêu đề theo ngày
1. Cho một hồ sơ giả chỉ có ngày sinh rơi vào note dự phòng. Khi xem 7 ngày liền. Thì không có hai ngày liền nhau trùng tiêu đề.
2. Cho cùng hồ sơ và cùng ngày. Khi tạo note hai lần. Thì ra đúng một tiêu đề, tức kết quả có tính xác định.
3. Cho mỗi cung có ít nhất 3 cặp tiêu đề và thân bài. Khi chạy lint nội dung hiện có. Thì mọi câu mới đều qua và không có câu đoán sự kiện đời người.
4. Cho note đã lưu hoặc đã chia sẻ. Khi đổi bộ câu. Thì note cũ vẫn giữ đúng chữ cũ.
5. Cho note dùng bản dự phòng. Khi API trả về. Thì `fallback_used` vẫn đúng và không có trường dữ liệu mới.

### K8 — Lời chào và câu chờ của Lá
1. Cho 5 khung giờ trong ngày. Khi rà lời chào ở cả hai giọng. Thì mỗi khung có ít nhất 3 câu, không câu nào có "một nhịp", "dò sóng" hay "ánh sao".
2. Cho cùng khung giờ trong 3 ngày liền. Khi mở Home ở bản note cũ. Thì không có hai ngày liền nhau trùng lời chào.
3. Cho cùng ngày và cùng khung giờ. Khi mở lại nhiều lần. Thì lời chào giữ nguyên.
4. Cho file nguồn `companion.py`. Khi chạy `pnpm content:companion`. Thì `laCatalog.generated.ts` khớp với nguồn và test kiểm tra điều đó.
5. Cho danh sách chữ cấm hiện có. Khi chạy test của Lá. Thì mọi câu mới đều qua. Câu phản ứng theo mood không đổi.

### K9 — Trang Cách tính
1. Cho trang Cách tính kiểu Tây phương. Khi xem các lựa chọn hệ nhà. Thì mỗi lựa chọn có một dòng tiếng Việt nói ngắn nó khác gì; tên gốc (Placidus, Whole Sign) có thể giữ trong ngoặc.
2. Cho lựa chọn mặc định. Khi trang mở. Thì lựa chọn mặc định có nhãn "khuyên dùng" ở cả hai hệ, không chỉ ở Ayanamsa.
3. Cho tiêu đề trang. Khi đọc. Thì không còn chữ "chart"; dùng "lá số".
4. Cho các giá trị gửi lên API. Khi đổi chữ. Thì mọi `value` giữ nguyên và test parse cũ qua.

### K10 — Thẻ "có bản đọc mới"
1. Cho note có bản đọc mới. Khi thẻ hiện ra. Thì câu chữ không nhắc "ma trận kiến thức", "nối hành tinh, nhà và góc" hay cơ chế nào khác.
2. Cho thẻ đó. Khi đọc. Thì người dùng biết hai điều: có bản mới và họ tự chọn đổi hay không.
3. Cho các nút "Để bản mới lại sau" và nút mở bản mới. Khi sửa chữ. Thì hành vi của nút giữ nguyên.
4. Cho thẻ hiện ở Home và ở Note chi tiết. Khi chạy `ReadingUpdateGift.test.tsx`. Thì cả hai chế độ đều qua với câu mới.

### K11 (dự bị) — Engine: không tạo vòng lặp khi đẩy sự kiện lên
1. Cho một yếu tố gộp `sun:trine:moon` chứa con `sun:conjunction:sun` là sự kiện. Khi sự kiện được đẩy lên đầu. Thì cha cũ nằm trong `merged` mà không còn mang con cũ.
2. Cho kết quả sau khi đẩy. Khi duyệt đệ quy `merged`. Thì không có yếu tố nào lặp lại.
3. Cho các lá số giả trong test hiện có. Khi chạy `test_sky_selection.py`. Thì thứ hạng và điểm của các ca cũ không đổi.

### K12 (dự bị) — Bầu trời hôm nay: chữ trạng thái
1. Cho phiên đã hết. Khi trang mở. Thì không còn "Phiên đọc đã khép lại" hay "Trạm Bắt Sóng"; câu nói rõ cần mở lại app.
2. Cho lỗi tải. Khi lỗi hiện ra. Thì câu báo lỗi ngắn và có nút Thử lại.
3. Cho các test hiện có. Khi chạy. Thì test được đổi theo câu mới và qua.

## 5 cặp đề xuất (chưa gán A/B)

| Cặp | Việc 1 | Việc 2 | Mảng | Cỡ | AC | Đổi chữ | File chung |
|---|---|---|---|---|---|---|---|
| C1 | K3 Note chi tiết | K4 Đã lưu | UI copy | S / S | 4 / 4 | có / có | không |
| C2 | K1 Màn hỏi Tarot | K2 Bộ chọn góc đọc | UI copy (+ trợ năng ở K2) | S / S | 5 / 5 | có / có | không |
| C3 | K5 Home qua nửa đêm | K6 Bầu trời hôm nay: giờ và làm mới | Web UX, ngày giờ Việt Nam | M / M | 4 / 4 | không / không | không |
| C4 | K7 Note dự phòng đổi theo ngày | K8 Lời chào của Lá đổi theo ngày | Nội dung, xoay theo ngày | M / M | 5 / 5 | có / có | không |
| C5 | K9 Trang Cách tính | K10 Thẻ có bản đọc mới | UI copy trên màn đọc | S / S | 4 / 4 | có / có | không |

- Giữa các cặp cũng không có file chung, nên chạy song song được.
- Dự bị: K11 dùng khi cần thay một việc engine S không đổi chữ. K12 chỉ dùng nếu bỏ C3, vì trùng file với K6.

## Điểm cần lưu ý khi so sánh

- C2: K2 có thêm phần trợ năng, K1 có thêm 18 câu gợi ý. Độ khó gần nhau, nhưng loại việc lệch nhẹ.
- C3: K5 phải phối hợp với cache note và bản dự phòng offline (`noteCache`), nên có thể khó hơn K6. Nếu muốn cặp cân hơn, có thể giới hạn K5 vào lúc quay lại tab.
- C4:
  - Cần kiểm tra note dự phòng (`SIGN_COPY`) còn hiện ra bao lâu một lần trên app thật. Nếu gần như luôn có `reading_projection`, K7 ít người thấy.
  - K8 có thêm bước sinh lại catalog.
- Câu chữ ở mọi cặp (trừ C3) cần duyệt. Thời gian chờ duyệt cần được tách khỏi số đo thời gian làm của từng nhánh.
- Chưa xem giao diện trên trình duyệt. Mọi số dòng ứng với `cfae0ee` và có thể lệch nếu integration đổi trước khi bắt đầu.

## Báo cáo bàn giao

- **Nguồn đã xem:** sổ lỗ hổng #177, kế hoạch Daily v2, US-03, US-20, US-21, các issue #143, #180, #190, #6, #14, các issue fix-forward đang mở, danh sách file của các PR đang mở, code web và API nêu ở trên.
- **Phát hiện đã sửa:** không có, vì đây là bản rà chỉ để đọc.
- **Rủi ro còn mở:**
  - các file có thể đổi trước khi bắt đầu;
  - cần duyệt câu chữ;
  - cần xác minh mức độ hiển thị của K7.
- **AC và DoD còn thiếu:** toàn bộ AC ở trên đều chưa làm. DoD cho từng việc theo `docs/operations/product-development-process.md`.
