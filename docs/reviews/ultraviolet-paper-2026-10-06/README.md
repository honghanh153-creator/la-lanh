# QA — Ultraviolet Paper, 06/10/2026

## Kết quả và giới hạn

Đã triển khai hệ giao diện được chọn vào bản web mobile-first và giữ luồng backend hiện có. **Chưa deploy, chưa đánh dấu native hoặc toàn bộ sản phẩm production-ready.** CMS không nằm trong phạm vi thay UI khách hàng. Các thay đổi backend/content đang có trước phiên này được giữ nguyên.

Reference: [ảnh người dùng](../../design-directions/ultraviolet-paper-2026-10-06/reference.png). [Danh sách toàn bộ route / trạng thái](../../design-directions/ultraviolet-paper-2026-10-06/README.md). [Gallery ảnh chạy thật](gallery.html).

Preview đang chạy: `http://127.0.0.1:5207/welcome`. QA API port 8027, web port 5207, local SQLite tách biệt production. Dùng hồ sơ giả định 15/03/1990, 07:30, Hà Nội; người thứ hai giả định 20/06/1992, không rõ giờ. Không đưa dữ liệu thật của khách vào test.

## Gate tài liệu / nghiệp vụ

- Đối chiếu router thật, PRD nền và US-01/02/03/06/07; không dùng danh sách ý tưởng làm bằng chứng một tính năng đã hoàn thành.
- Giữ guest-first, ngày sinh → reveal → Home; giờ/nơi và consent sâu vẫn là tự chọn.
- Không mở lại Lá Chứng, vòng ghép người lạ, chat hoặc matching pool.
- Profile có đường vào Đã lưu sau khi bottom nav rút về bốn mục.
- Cập nhật README story map để direction cũ không ghi đè quyết định mới.

## Gate security / privacy

- Không thêm trường dữ liệu cá nhân, analytics, provider AI hoặc lời gọi ra ngoài để chạy bản đọc.
- Không đổi authorization, CSRF, mã hóa, retention, quyền token/link hay rút consent.
- Consent dữ liệu sinh/consent Radar không được tích sẵn hoặc ẩn để làm form ngắn hơn.
- Giờ không đầy đủ không được tự biến thành `HH:00`; hai select giữ đúng hợp đồng `HH:mm`, midnight hợp lệ. Radar không submit exact mode nếu chỉ chọn một trường; unknown gửi `null`.
- SVG chia sẻ dùng whitelist projection và escape XML. Test đảm bảo private field không đi vào SVG.
- Không tạo public link production hoặc gửi báo cáo cho người thật trong QA này.
- Đây là review delta UI, **không phải** audit pháp lý hay penetration test toàn hệ thống.

## Gate trải nghiệm và hình ảnh

| Luồng / màn | Kiểm tra thực tế |
|---|---|
| Welcome → Birth → Reveal → Home | Đã nhập ngày giả định, tới Note có dữ liệu API thật của QA |
| Giờ → Nơi → consent → Aura → Home | Đã chọn 07/30 bằng select, tìm Hà Nội, consent riêng, chọn Dùng Aura; Home/Profile nhận lớp mới |
| Mood | Sheet mở, chọn Chill và đóng; state mới xuất hiện trên trigger |
| Note chi tiết / Đã lưu | Mở bản đọc, lưu, danh sách nhận đúng revision; không chỉ screenshot static |
| Tarot 5 lá | Tạo phiên, chọn đủ năm, tới bài đọc |
| Tarot 3 lá | Tạo phiên khác, chọn đủ ba, tới bài đọc; ảnh drawing/result lưu lại |
| Radar | Giới thiệu → form → không rõ giờ → nơi sinh → consent → báo cáo; mở lại từ lịch sử |
| Natal / Moon | Overview nhận dữ liệu, mở Moon và phần dài; kỹ thuật/disclaimer còn riêng |
| Western → Jyotish | Switch tính chart khác; Moon và House thay đổi, có Nakshatra; vào settings thấy ayanamsa |
| Cách tính | Nhóm hệ nhà/ayanamsa hiển thị và selected rõ; không thay semantics query |
| Sky | API trả vị trí, tên Việt và timestamp; có ghi nhận lỗi copy ở backlog dưới |
| Profile sáng/tối | Toggle hoạt động cả hai chiều, giữ màu đọc; test preference đã lưu |
| Card | Đổi square/story; preview không chồng chữ; UI xác nhận “Card PNG đã được tải về.” |
| Demo/privacy/account/retired | Đã mở và lưu ảnh; account vẫn là placeholder, không giả định có auth |
| Public Radar / recipient / public share | Nhận shell/tokens chung và tests component; **chưa chạy lại toàn bộ luồng hai thiết bị/token hợp lệ** |
| Legacy history/results/withdraw | Nhận tokens chung; chưa tái tạo từng kết quả legacy để visual QA |

Kiểm tra 390 × 844; thêm 320 × 740 cho Home/Radar form/Tarot/Profile: `documentElement.scrollWidth === innerWidth` ở các màn này. Fan Tarot và danh sách chủ đề có scroll ngang **bên trong** control, không tràn toàn trang. Không có console error ở phiên QA quan sát.

Cặp màu đã tính theo luminance tương đối:

| Chữ / nền | Contrast |
|---|---:|
| Kem `fff9e9` / tím `47258c` | 10.45:1 |
| Helper `625c73` / nền `f7f4eb` | 5.79:1 |
| CTA `321960` / lime `dfff4f` | 12.85:1 |
| Accent `54249b` / nền `f7f4eb` | 9.08:1 |
| Helper dark `c7bed4` / `191426` | 10.04:1 |

Đối chiếu ngưỡng 4.5:1 cho chữ thường từ [W3C WCAG 2.2 Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum). Không suy diễn kết quả token thành chứng nhận WCAG cho mọi pixel/trạng thái.

## Lỗi được sửa trong vòng QA này

1. CSS global được import sau concept mới khiến màu cũ ghi đè ở share card → đưa stylesheet mới về cuối main.tsx.
2. Preview share dùng position absolute khiến title/body chồng nhau → layout flow; SVG tải về cũng chuyển palette, không cắt sau ba dòng.
3. Nhãn form/Radar progress và giới hạn unknown-time nhạt trên nền sáng/tím → màu riêng đủ tương phản.
4. Note body bị clamp giữa câu → bỏ clamp, card tăng chiều cao theo nội dung.
5. Native input time khó thao tác qua preview → dùng hai select có label; thêm regression partial/midnight.
6. Tùy chọn giọng đọc chiếm gần một màn form → disclosure, giữ default và đầy đủ lựa chọn.
7. “Đã lưu” không còn entry sau đổi nav → thêm row trong Mình.
8. Domain kỹ thuật `core/emotions/mind` lặp với tiêu đề bản đọc → bỏ nhãn dư thừa ở overview.

## Kiểm tra tự động

`pnpm web:lint`, `pnpm web:typecheck`, `pnpm web:test`, `pnpm web:build`, `git diff --check` đều chạy thành công. Suite cuối: 41 files / 145 tests. Có regression cho theme, Home links, time picker, partial exact Radar, SVG palette/long title/XML/privacy.

Build còn warning JS chunk ~731KB (~207KB gzip), không phải lỗi build. Ba minh họa runtime dùng WebP tổng 64,688B; PNG nguồn không nằm trong public build.

## Còn lại trước release rộng

- Chạy lại nhánh mời/nhận/share/thu hồi trên hai thiết bị và native OS share sheet. Sự kiện download của browser automation không trả path, nhưng UI xác nhận PNG đã tải; chưa kiểm tra file raster đã tải trong iOS/Android.
- `/existing-user` chưa phải đăng nhập thật; không được tuyên bố US-19 hoàn thiện vì thay UI.
- Copy backend của Sky nói “12:00 UTC” trong khi observed_at QA trả thời điểm hiện tại. Đây là mâu thuẫn nội dung có trước, chưa sửa backend trong visual pass.
- Một số hook Natal/Jyotish và kết quả Tarot còn dài/thiên về thuật ngữ. Cần vòng content gate riêng; thay palette không phải bằng chứng chất lượng nội dung đã đạt.
- Birth-card download và renderer báo cáo Radar hiện có chưa được đồng bộ/review từng ảnh xuất; preview khách hàng đã nhận theme chung.
- Tách bundle/lazy route và dọn CSS legacy theo từng component là follow-up kỹ thuật; không xóa hàng loạt CSS có thể phá feature ngoài scope.

Final visual result: **passed cho các màn/luồng đã nêu đã kiểm tra; partial cho nhánh token/legacy/native và chất lượng copy toàn hệ thống.**
