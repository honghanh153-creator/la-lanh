# Onboarding motion v2 — 07/10/2026

Thay cho bản motion ngắn trước đó, sau phản hồi “lên xuống có 1 lần rồi thôi”. Áp dụng cho Welcome → Birth → Reveal, không đổi palette, typography, dữ liệu hoặc nội dung đọc.

## Contract hiện hành / AC

- Hành tinh dùng raster moon hiện có, lượn qua bốn vị trí với độ nghiêng -4° → 5° và scale 1 → 1.06, chu kỳ 6.8 giây, **lặp liên tục**. Bước nhập liệu dùng chu kỳ chậm hơn 8.4 giây.
- Hai sao nhỏ có quỹ đạo 11 và 17 giây, chạy ngược chiều và lệch pha; sao thương hiệu xoay theo nhịp riêng. Không nhấp nháy độ sáng, không âm thanh, không particle engine hay thêm dependency. Quỹ đạo nằm trong vùng trang trí, không che chữ hoặc field.
- Một nút Pause/Play 44×44px ở header dừng/bật toàn bộ vòng lặp trang trí. Có accessible name tiếng Việt, thao tác được bằng bàn phím, không đòi giữ focus để duy trì pause. Khi pause, tiến độ/card entrance được đặt thẳng vào trạng thái cuối; không giữ card nửa mở.
- Lựa chọn pause nằm trong React context tại AppShell, giữ qua điều hướng SPA và các trạng thái loading/error của ba bước. Không lưu cookie/localStorage/sessionStorage, không gửi lên server; reload toàn trang bắt đầu lại. Frame đứng riêng vẫn có state nội bộ dùng được.
- Chữ, form, button đứng yên; bỏ animation fly-in của heading/lead. Progress 33/67/100% vẫn là tiến độ **bước**, không phải tiến độ tính chart. Reveal card mở một lần trong 650ms, không làm mờ cả card.
- Không thêm thời gian chờ, timer điều hướng hoặc request. Pause motion không pause request thật. Chỉ business pending hiện hành được khóa CTA.
- `prefers-reduced-motion: reduce` tắt animation/transition với `!important`, giữ nguyên thông tin và thao tác. Nút motion ẩn trong chế độ này vì không có motion trang trí để điều khiển.

## Bằng chứng và kiểm thử

[Clip browser khoảng 10.7 giây](welcome-motion.gif), [Welcome](01-welcome.png), [Welcome paused](01-welcome-paused.png), [Birth](02-birth.png), [Reveal](03-reveal.png). Clip preview phát một lần; app thực tế lặp liên tục và có nút tạm dừng. Loại bỏ 5 frame đầu lúc browser đang áp dụng viewport override; không ghép hoặc dựng chuyển động giả.

- Browser đọc được `animation-iteration-count: infinite` cho hành tinh và hai quỹ đạo. Hai lần đo cách nhau 11.057 giây có transform hành tinh khác nhau, còn rect heading giữ nguyên chính xác. Pause cho cả ba lớp trả về `animation-play-state: paused`; hai lần đọc transform sau pause bằng nhau.
- **Guest E2E mới** trên QA tách riêng `localhost:5208`: Welcome → đồng ý → Birth → ngày sinh giả lập → Reveal → Home. Pause ở Welcome vẫn giữ ở Birth; nhập liệu trong lúc pause bình thường; Enter trên nút Play bật lại; submit/reveal/completion không bị animation trì hoãn. Home trả về Note thật từ engine, không mock API hoặc chart.
- QA dùng database ephemeral riêng và hostname `localhost`, không dùng chung cookie host `127.0.0.1` hoặc xóa database phiên 5207. Cả generation và generation worker trả phí tắt. Chỉ dùng ngày sinh giả lập để kiểm thử; không nhập giờ/nơi hoặc dữ liệu người thật. Instance tạm dừng sau QA, không phải URL giao sản phẩm.
- Cả ba frame có width = scrollWidth = 320 khi kiểm tra màn hẹp; Birth 390 cũng không tràn ngang. Nút motion đo được 44×44px ở Reveal 320. Form có transform/animation `none`; Reveal card về transform `none` sau entrance; CTA enabled. Không có JS error trong flow QA kiểm tra.
- Lint/typecheck/build, runtime mock/privacy/mobile-config guards pass; **46 files / 174 frontend tests** pass. Hai test bổ sung kiểm tra pause/resume không khóa field/CTA và pause giữ qua cả ba route với AppShell thật. CSS regression bảo vệ reduce-motion và pause selectors. JSDOM chỉ stub `scrollTo`, không mock motion context.

## Doc / security / privacy gate

Đối chiếu US-01/02 và [contract optional birth](../../../plans/2026-10-07-optional-birth-details-planet-surface.md): không thêm bước, không login wall, không giả loading. Không thêm dữ liệu cá nhân, quyền truy cập, API, network flow, SDK hoặc provider; không đổi auth/session/CSRF/retention/share/deletion. UI preference chỉ là boolean trong bộ nhớ trang. Không gọi API trả phí, không deploy hoặc push Git trong lượt này.

Nguồn chính thức đã kiểm tra: [W3C Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) — chuyển động không thiết yếu tự chạy quá 5 giây cần cơ chế dừng; [W3C Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) — ưu tiên giảm chuyển động. Không tuyên bố chứng nhận WCAG toàn app.

## Giới hạn / chưa hoàn tất

- Browser hiện có `prefers-reduced-motion: false`; chưa đổi OS để kiểm tra chế độ reduce trực tiếp. Guard CSS/unit đã được kiểm tra, không coi là bằng chứng native accessibility.
- Chưa test trên máy iOS/Android thật, chưa đo FPS/pin trên thiết bị yếu, chưa deploy production. Cảnh báo bundle JS >500KB có sẵn vẫn còn.
- Backend không đổi trong lượt này; không rerun full backend suite. Guest E2E kiểm tra nhánh ngày sinh bắt buộc; nhánh bổ sung giờ/nơi có frontend regression tests, không được gọi là một lượt manual E2E mới của mọi biến thể.
- Mở trực tiếp `/reveal` ở phiên 5207 lúc đầu không có profile đọc được và hiện trạng thái “Chưa tìm thấy tín hiệu”; không ghi đè phiên đó để lấy screenshot. Preview giao lại là `/welcome?restart=1`, chỉ xem trang không tự reset dữ liệu. E2E xác minh bằng phiên QA riêng nêu trên.

**Result: passed cho motion v2, pause/resume và nhánh guest E2E đã kiểm tra; không phải chứng nhận phát hành toàn sản phẩm.**
