# Bản review full luồng và hiệu ứng Tarot

2026-10-09 · web QA cục bộ 5310 / backend 8030 · dữ liệu giả lập do QA nhập qua giao diện. Không triển khai production, không gọi API trả phí, không thay đổi billing/key. Đây là bản chạy của sản phẩm hiện tại, không phải demo chỉ có một màn Tarot.

Mở từ đầu: <http://127.0.0.1:5310/welcome?restart=1>. Vào trang chưa xóa dữ liệu; bấm “Đồng ý & bắt đầu” tạo phiên onboarding mới trên môi trường QA này. Đừng dùng link restart để thay phiên chứa dữ liệu cần giữ.

## Luồng để chủ sản phẩm review

| Nhánh | Cách đi trên giao diện | Kết quả kiểm tra lần này |
|---|---|---|
| Chỉ có ngày sinh | Giới thiệu → Đồng ý & bắt đầu → điền ngày/tháng/năm → bỏ qua giờ/nơi → reveal → Note hôm nay | Chạy được; Vibe ghi rõ chưa đủ lá số; Home có CTA thêm giờ/nơi |
| Có giờ/nơi ngay từ đầu | Ngày sinh → mở phần tùy chọn → chọn giờ/phút → tìm Hà Nội → chọn kết quả → consent riêng → reveal → Home | Chạy được; có Aura, mở tổng quan; Home không mời thêm thông tin đã có |
| Note | Home → Đọc thêm → quay lại | Note và hành động hiển thị, không có màn trống |
| Check-in | Icon mood trên Home → Chill | Popup đóng, icon/nhãn đổi sang Chill |
| Natal | Khám phá → Mở bản đọc Natal đầy đủ | Chạy được với ngày/giờ/nơi; còn vấn đề biên tập, xem bên dưới |
| Đổi hệ đọc | Khám phá → Jyotish | Chart/URL/nội dung đổi; phần tổng hợp Jyotish chưa đạt độ dễ hiểu |
| Tarot | Home → Rút Tarot → câu hỏi/chủ đề/độ sâu → Xòe → chọn đủ lá | Đã bốc thật cả 1, 3 và 5 lá; mỗi lần mở hiệu ứng rồi report |
| Tarot đọc lại | Result → mở từng lá → reload | Summary nằm trên; chapter mở được; giữ bộ lá, không chạy lại ceremony |
| Tarot bỏ qua | Trải một lá → lá cuối → Xem bài ngay | Report mở ngay; không gửi thêm lượt bốc |
| Tarot chuyện mới | Report → Hỏi một chuyện khác | Về form; chủ đề/câu hỏi trước có thể vẫn được giữ trong SPA, có thể thay trực tiếp |
| Hợp gu | Home → Mình & người ấy → Check kín một người → điền dữ liệu test → Không rõ giờ → chọn Đà Nẵng → xác nhận quyền dùng → Check | Có kết quả, mục lục, giới hạn độ chính xác; bỏ lớp phụ thuộc giờ của người kia |
| Cài đặt | Hợp gu → Mình → chế độ tối → chế độ sáng | Toggle hoạt động; dữ liệu sinh hiện đúng |
| Chia sẻ | Home → Chia sẻ note | Preview định dạng và CTA có mặt; chưa gửi cho ai, chưa kiểm export/publication trong lượt này |
| Sửa giờ/nơi | Mình → Sửa lớp dữ liệu sinh | Trang mở được; còn dùng lời mời mở khóa thay vì trạng thái sửa, chưa kiểm gửi lại trong lượt này |

## Hiệu ứng mới

- Chỉ sau phản hồi cuối thành công có reading. UI không giả vờ đang tính lại hoặc thêm tiến độ engine.
- Các mặt bài quay theo thứ tự, có halo/orbit chuyển động; giữ nguyên tên và thứ tự từ server. Năm lá xếp 3 + 2 trên mobile.
- Thời lượng 2.8 giây, có nút bỏ qua. Giảm chuyển động của hệ thống hoặc pause chung trong onboarding sẽ bỏ qua; có kiểm tra tự động cho thay đổi preference giữa chừng.
- Focus chuyển vào tiêu đề ceremony rồi sang tiêu đề report. Timer/listener được dọn; completion callback chỉ chạy một lần. Lỗi/không có reading không chạy animation.
- Không thêm endpoint, dữ liệu lưu, analytics, âm thanh, rung, dịch vụ ngoài hoặc chi phí generation.

## Bằng chứng

- Frontend **220 tests / 49 files passed**; 11 test mới so với 209 test trước, gồm count/order/timing, skip, cleanup, pause, reduced motion, restored report, intermediate pick, failed pick và missing reading.
- Lint, typecheck + production build passed. Bundle JS khoảng 757 kB còn cảnh báo kích thước; chưa coi native performance là đã kiểm.
- Runtime mock guard, privacy guard, mobile config guard, 4 mobile guard tests, OpenAPI và generated TypeScript contract passed.
- Backend `tests/tarot` passed. Không sửa thuật toán/knowledge/provider trong lượt animation này.
- Browser thật 390 × 844: hai nhánh onboarding, note, mood, natal, hệ đọc, Tarot 1/3/5, Radar unknown-time, dark/light. Scene năm lá có scrollWidth = viewport = 390; không tràn ngang. Console error log không có entry ở điểm kiểm cuối.
- [Ceremony 3 lá](security-content-2026-10-09/tarot-reveal-magic-mobile.png), [ceremony 5 lá](security-content-2026-10-09/tarot-reveal-five-mobile.png), [trang đầu review](security-content-2026-10-09/full-flow-review-welcome.png). Ảnh chụp lúc chuyển động bắt đầu, không phải toàn bộ video.

## Những phần không được gọi là hoàn tất

1. **Nội dung Natal**: headline “Điểm khó không phải chọn một bên…” không nhất quán với body nói dễ kết hợp hai việc. Không phải lỗi điều hướng, nhưng chưa đạt gate biên tập. Cần sửa ý nghĩa headline theo loại aspect, không chữa bằng animation.
2. **Jyotish synthesis**: vẫn ghi drishti/opposition và “chưa được duyệt”. Cần nội dung đã kiểm cho hệ này; không biến thành kết luận tự tin chỉ để che khoảng trống.
3. **Sửa precision**: `/birth-time` chưa phân biệt rõ người đã mở đủ chart với người mới thêm. Chưa xác nhận toàn bộ submit lại/withdrawal bằng browser lần này.
4. Không gọi paid Luna, không dùng người thật, không thử native iOS/Android, không kiểm tất cả OS/browser. Reduced-motion có regression tests, chưa có manual OS setting proof.
5. Không kiểm luồng mời hai trình duyệt, xuất/chia sẻ/xóa dữ liệu bằng UI lần này. Không mở lại Vòng Lá/chat đang ngoài phạm vi sản phẩm đã chốt.
6. Scan an ninh toàn hệ thống, remaining triage, formal ship review và xác minh live provider/DB controls vẫn chưa nghiệm thu: [receipt an ninh/content trước](2026-10-09-security-content-work-handoff.md). Không gọi bản này “đã sửa hết lỗi an ninh”.

## Nguồn và ba gate

Docs: [plan/AC](../plans/2026-10-09-tarot-reveal-full-flow-review.md) khớp runtime và test. Motion tham chiếu [W3C Animation from Interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions) và [C39](https://www.w3.org/WAI/WCAG22/Techniques/css/C39.html), kiểm 2026-10-09; không tuyên bố chứng nhận WCAG toàn app.

Security: phiên/card ownership vẫn do API cũ quyết định; animation chỉ nhận kết quả đã có, React render text không dùng HTML injection, không gọi lại start/select. Privacy: không thêm field, log, URL, SDK hay lưu trữ; không truyền question/chart cho bên thứ ba trong QA. Cấu hình generation tắt. Thay đổi trình bày này không thay consent/retention hay thay thế kiểm tra pháp lý và kiểm toán triển khai.
