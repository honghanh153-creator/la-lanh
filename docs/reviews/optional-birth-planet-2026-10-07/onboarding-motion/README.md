# Onboarding motion — 07/10/2026

> Receipt lịch sử. Hành vi hiện hành đã thay bằng [motion v2 lặp liên tục + Pause/Play](../onboarding-motion-v2/README.md) sau phản hồi chuyển động quá đơn điệu. Các giới hạn và timing dưới đây chỉ mô tả bản cũ.

User request: thêm một vài animation vui mắt ở 1/3 → 3/3, giữ UI tối giản hiện hành. Local web 5207; không deploy/public/push, không phát sinh API trả phí.

## Quyết định và AC

- Bước 1: moon trôi lên 7px, nghiêng 3°, 2 chu kỳ × 2.2 giây rồi dừng; dấu sao thương hiệu xoay nhẹ 2 × 0.9 giây.
- Bước 2: moon nhỏ lướt vào, hơi vượt vị trí rồi ổn định trong 1.4 giây. Form ngày/giờ/nơi đứng yên, không dùng animation để chờ nhập hay ép người dùng dừng.
- Bước 3: card tổng quan mở lên 10px, nghiêng tối đa 1°, scale 0.985 → 1 trong 650ms sau khi dữ liệu render. Không giảm opacity toàn card để giữ tương phản chữ. Không thêm confetti/particle/âm thanh hay chữ mới.
- Tiến độ 1/3 → 2/3 → 3/3 tương ứng 33% → 67% → 100%; transform scaleX 480ms, bắt đầu từ mốc trước đó. Đây là tiến độ **các bước**, không giả phần trăm engine đang tính. Không dựng loading tối thiểu, timer điều hướng hay thêm request.
- Nút luôn sẵn sàng ngay khi logic nghiệp vụ cho phép. Chỉ real request pending hiện hành mới khóa nút. Animation không điều khiển consent, tính chart, lưu dữ liệu hoặc điều hướng.
- Tôn trọng `prefers-reduced-motion`: animation/transition none với priority cao hơn selector onboarding. Bản tĩnh giữ đúng progress và toàn bộ nội dung; motion chỉ là trang trí `aria-hidden`, không thêm thông tin screen reader phải nghe.

## Bằng chứng

[Preview chuyển động thật](welcome-motion.gif), [Welcome](01-welcome.png), [Birth](02-birth.png), [Reveal](03-reveal.png). GIF được ghép từ chuỗi browser screenshots, timing xấp xỉ; không thay cho kiểm tra trong app.

Browser actual 390: moon transform thay đổi qua các frame và trở về `none` sau hai chu kỳ; native CSS đọc đúng tên/duration/iteration. Bước 2 field animation `none`, nút submit enabled, width = scrollWidth = 390. Bước 3 progress đạt matrix scaleX 1, card có animation 650ms, CTA enabled, không lỗi JS trong actions kiểm tra. Không bấm consent mới, không thay ngày/giờ/nơi sinh để lấy screenshot; Reveal dùng profile QA hiện hành. Flow chuyển trang/save/retry/no-fake-delay được phủ frontend tests; không gọi đây là một lần guest E2E mới hoàn toàn.

Lint/typecheck/build, 46 files / 172 frontend tests và mock/privacy/mobile-config guards pass. Test mới kiểm tra cả ba bước giữ CTA/content ngay lập tức, real loading state và CSS reduce-motion priority. Browser đang `prefers-reduced-motion: false`: chưa đổi thiết lập OS để test trực tiếp reduce; không tuyên bố đã test native iOS/Android hoặc production. Backend không đổi trong lượt này; không rerun full backend suite. Cảnh báo JS bundle >500KB có sẵn vẫn còn.

## Doc / security / privacy

Đã đối chiếu US-01/02 và contract optional birth details: không thêm slide, không login, không kéo dài reveal giả. Motion dùng ảnh moon/logo hiện có, không dependency, SDK, provider, quyền truy cập hay trường dữ liệu mới. Session/CSRF/consent/search/retention/share/deletion giữ nguyên; không reset DB QA. Không gửi PII ra bên thứ ba.

Nguồn chính thức: [W3C 2.3.3 Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html), [W3C 2.2.2 Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html). Decorative movement tự kết thúc dưới 5 giây; loading indicator hiện có chỉ dùng cho request thật. Đây không phải chứng nhận WCAG toàn app.

**Final result: passed cho motion và không-blocking-flow scope đã có bằng chứng.** Native/production, kiểm thử reduced motion qua OS và một guest E2E mới hoàn toàn chưa được chứng nhận lại.
