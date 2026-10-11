# Vitality layer — Lá, nghi thức và thẻ chia sẻ (11/10/2026)

> **Cập nhật cuối ngày 11/10/2026.** Sau review thiết kế (`docs/reviews/design-review-2026-10-11/`) và phản hồi của chủ sản phẩm ("càng làm càng xấu", "trẻ con"), lớp này được **thu gọn về Ultraviolet Paper gốc**. Đã gỡ: bong bóng lời Lá trên Home/Tarot/Reveal, lớp foil óng ánh và tia sáng, chip trăng riêng, giao diện Roast (Roast giờ **chỉ đổi câu chữ**), bộ chọn vibe/nhân vật ở Welcome, mascot và nền loang trong thẻ danh tính, màu riêng từng bộ Tarot (mọi lá dùng nền tím, chỉ khác màu biểu tượng), đĩa cầu vồng/sao dày/nhãn xoay trong thẻ chia sẻ. Giữ: màn chờ có Lá (đã sửa nét), lá Tarot thật, Mình gọn với bộ ba Mặt Trời/Mặt Trăng/Cung Mọc, "Giọng của Lá" trong Mình, ngày · pha trăng trên một dòng, recap Chủ nhật chỉ khi có note đã lưu, gợi ý nền tối dạng một dòng. Hai nhân vật Mầm Aura và Cửa sổ trời **chưa đưa vào luồng chính**; chỉ xem ở `/companion-lab`. Các mục bên dưới mô tả lần thử đầu và chỉ còn giá trị lịch sử nếu mâu thuẫn với đoạn này.

Nguồn: review UI/UX ngày 11/10/2026 cho nhóm Gen Z 18–25 (playbook `docs/foundation/la-lanh-product-plan-v2.md`). Chủ sản phẩm yêu cầu làm cả P0, P1, P2 để mang bản thật đi thử nghiệm với người dùng. Lớp này **chồng lên** Ultraviolet Paper; không thay bảng màu gốc, font Be Vietnam Pro, thứ tự nội dung đã chốt hay quy tắc tiếng Việt thẳng, đời thường.

## Mục tiêu

Sôi động và vui hơn nhưng vẫn huyền bí; có một "trợ lý huyền ảo" hiện diện, đặt phép màu vào đúng các khoảnh khắc đỉnh (lá đầu tiên, mở note, rút bài, chia sẻ), và bớt cảm giác "tài liệu".

## Lá — nhân vật đồng hành

| Quy tắc | Chi tiết |
|---|---|
| Hình | Linh hồn chiếc lá tím, gân lime, mắt kem, một tia sáng nhỏ. SVG gốc trong `apps/web/src/shared/ui/la/LaSpirit.tsx`, không dùng ảnh bên ngoài |
| Trạng thái | `idle`, `think` (đang chờ), `happy` (phản ứng/ăn mừng), `whisper` (mở nghi thức) |
| Lời | Chỉ ở lời dẫn: chào theo giờ, câu chờ, phản ứng mood, mời bật nền tối. **Không** đổi ý nghĩa bài đọc, không tiên đoán, không nói thay người khác. Giọng: tiếng Việt thẳng, đời thường, ấm. Giọng "affectionate-sharp" A/B/C vẫn chưa được chọn và không dùng ở đây |
| Trợ năng | Lá luôn `aria-hidden`; mọi câu Lá nói là chữ thật bên cạnh (`LaSays`), trạng thái chờ là `role="status"` |
| Chuyển động | Tắt khi `prefers-reduced-motion`, khi bấm nút tạm dừng ở Home, hoặc khi tạm dừng chuyển động toàn app (`data-motion="paused"` trên `.app-shell`) |

## Bầu trời thật

Pha trăng được tính trên máy từ ngày hiện tại (`moonPhase.ts`, chu kỳ giao hội 29,53 ngày, mốc trăng mới 06/01/2000). Chỉ dùng làm bối cảnh ("Trăng mới"), không bao giờ là lý do của một bài đọc. Nếu note có `sections.transit`, Home hiện link "Vì sao hôm nay?" tới phần căn cứ.

## Thay đổi theo màn

| Màn | Thay đổi |
|---|---|
| Chờ phiên (mọi route riêng tư) | Lá + câu chờ + khung xương nhấp nháy thay cho chữ trơn; hiện sau 220 ms để tránh nháy. Logic kiểm tra phiên giữ nguyên |
| Chờ khác | Home, Note chi tiết, bản đọc, Đã lưu, Aura, lá đầu tiên dùng `LaLoading` |
| Lá đầu tiên `/reveal` | Lá ăn mừng, biểu tượng cung lớn phát sáng theo màu nguyên tố |
| Home | Lá chào theo giờ, chip pha trăng; lần mở đầu tiên trong ngày note "lật mở" kèm tia sáng; lớp foil óng ánh chạy chậm trên card tím; mood hiện đúng emoji đã chọn và Lá phản ứng; sau 21h gợi ý nền tối (một lần mỗi đêm); Chủ nhật có thẻ "nhìn lại tuần" từ note đã lưu |
| Mình | Mở đầu bằng bộ sưu tập danh tính: cung Mặt Trời, nguyên tố, Vibe/Aura, bộ ba Mặt Trời / Mặt Trăng / Cung Mọc. Mặt Trăng và Cung Mọc chỉ hiện khi có giờ sinh **chính xác**, nếu không là "Lá ẩn" dẫn tới thêm giờ/nơi sinh. Nút "Tạo thẻ khoe vibe" và "Note đã lưu". Cài đặt và dữ liệu gom trong "Cài đặt & dữ liệu", vẫn chỉ một chạm |
| Tarot | Hình lá bài SVG gốc cho đủ 78 lá, xòe hình vòng cung, chạm để lật, lá thật trong nghi thức mở và trang kết quả; sửa tên trợ năng cho nút chủ đề/số lá. Chi tiết trong review receipt |
| Thẻ chia sẻ | Một câu hook đậm, biểu tượng lớn, màu nguyên tố, foil; không kèm ngày/giờ/nơi sinh. Chi tiết trong review receipt |
| Vi tương tác | 👍 bật tia sáng, nút co nhẹ khi bấm, rung 12 ms trên thiết bị hỗ trợ (bỏ qua khi giảm chuyển động) |
| Nội dung | Câu "Góc đọc là muốn…" trong `daily_personalization.py` đổi thành "Bạn dễ muốn…" cho tự nhiên; ý nghĩa giữ nguyên |
| Đăng nhập | Quay lại `/reveal` sau đăng nhập; thông báo huỷ Google không còn nói "hồ sơ khách" khi đã có tài khoản; "Mình" không còn nháy "Đăng nhập để giữ hồ sơ" khi đang kiểm tra |

## Không làm

- Không mở lại Vòng Lá, ghép người lạ hay recap pool (US-18 vẫn DEFERRED). Thẻ Chủ nhật chỉ đọc note do chính người dùng lưu.
- Không streak gây tội lỗi, không đếm ngày bỏ lỡ.
- Không thêm thư viện, font hay ảnh từ bên ngoài. Không thêm plugin native (iOS/Android đang tạm dừng).

## Dữ liệu trên máy (privacy inventory)

| Khoá `localStorage` | Giá trị | Mục đích | Xoá |
|---|---|---|---|
| `la-lanh-daily-ritual-v1` | Ngày của note (`YYYY-MM-DD`) | Chỉ chạy nghi thức mở một lần mỗi ngày | Trong `clearPersonalDataOnDevice` |
| `la-lanh-night-nudge-dismissed-v1` | Ngày (`YYYY-MM-DD`) | Không lặp lại gợi ý nền tối trong đêm | Trong `clearPersonalDataOnDevice` |

Không lưu mood, nội dung note, cung hay danh tính. Pha trăng tính tại chỗ, không gọi dịch vụ ngoài. Không có dữ liệu mới gửi lên server. Không cần cập nhật App Privacy / Data Safety vì không có trường dữ liệu mới được thu thập hay truyền đi.

## Vibe của app: Direct và Roast (quyết định của chủ sản phẩm, 11/10/2026)

Người dùng chọn vibe ngay ở Welcome (trước hai CTA) và đổi lại trong Mình → "Vibe & bạn đồng hành". Lựa chọn chỉ lưu trên máy (`la-lanh-vibe-v1`), áp dụng bằng `data-vibe` trên `<html>`.

| | Direct (mặc định) | Roast |
|---|---|---|
| Giọng | Tiếng Việt thẳng, đời thường, ấm | Cà khịa thân thiện: chọc tình huống, không chọc con người; luôn kèm một việc làm được |
| Giao diện | Ultraviolet Paper như cũ | Bubble Lá kiểu sticker lime viền mực, nút có bóng lệch, viền nóng coral quanh card tím, Lá nhướng mày + ngọn lửa |
| Lời của Lá | Chào, chờ, phản ứng mood | Bản roast tương ứng (`laVoice.ts`) |
| Welcome | "Hiểu mình hơn. Bớt đoán mò." | "Bớt overthinking. Để Lá soi giùm." |
| Note hằng ngày, Tarot | Nội dung hiện tại | Lớp giọng roast phía server: cùng ý nghĩa, cùng việc nên làm, cùng thứ tự lá; câu hỏi Tarot nhạy cảm (sức khoẻ, an toàn, khủng hoảng…) tự về Direct |
| Chia sẻ | Bản Direct | Vẫn Direct theo kế hoạch U6 (không tự mang giọng sang người nhận) |

Chưa áp dụng Roast cho Natal/insight, Radar và nội dung pháp lý/quyền riêng tư: các phần này giữ Direct.
