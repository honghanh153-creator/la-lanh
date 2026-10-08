# QA — giờ/nơi sinh tùy chọn và bề mặt hành tinh

Ngày: 07/10/2026. Phạm vi: local web mobile-first, không deploy, push, native build hay gọi API rewrite trả phí.

**Cập nhật mới nhất:** [time selector / content / terrain receipt](time-content-terrain/README.md). Texture hiện tại là 0.50 luminosity, không còn 0.09. Component giờ được dùng chung; đoạn natal aspect đã có bản sửa xác minh trên browser. Các thông số và test counts phía dưới là lịch sử của các lượt trước.

## Bản sửa màu sau feedback — trạng thái hiện tại

Phần soft-light trong receipt phía dưới là lịch sử, **đã được thay thế**. Người dùng thấy màu sai; so vùng nền tương ứng, reference median `#4c2e8e`, bản soft-light median `#311288`. Fix: base `#4c2e8e`, texture riêng opacity 0.09 với `mix-blend-mode: luminosity`. Median recapture `#482e8a`, gần reference, không còn kéo cả card sang xanh. [Comparison mới](comparison-color-corrected.png) đã mở để so nguồn 390×844 và runtime cùng kích thước; copy/ngày khác, không giả định pixel-identical.

- Color P2 fixed, có recapture Home/Tarot/Radar. Terrain/image quality giữ rất nhẹ; minh họa không đổi. Font/type, spacing/layout và copy không sửa trong lượt color fix; card dài do copy thật vẫn là P3 density đã ghi nhận, không cắt chữ.
- Contrast conservative bound: giả sử lớp texture 9% trắng hoàn toàn, body kem ≥7.50:1/lime ≥6.97:1. Không dùng raw asset dưới chữ, không claim WCAG toàn app. DOM xác nhận base, opacity, luminosity và width=scrollWidth=390.
- Lint/typecheck/build/runtime guards pass; **44 files / 166 tests** pass. New test replay reset mocks riêng, giữ ordinary Radar continuation và không tạo guest khi chỉ mở Welcome.
- `/welcome?restart=1` là đường review từ đầu; chỉ khi bấm Đồng ý mới reset local theo flow cũ và bỏ pending Radar. Không xóa server profile, không mở thêm quyền, không tự gửi consent hay thêm PII field. Không có JS error trong actions vừa chạy.
- Đã giữ tab Welcome cho user tự đi flow; [welcome-restart.png](welcome-restart.png). Chưa tự bấm consent/tạo lại profile; browser E2E date-only mới hoàn toàn vẫn cần chạy riêng. Automated validation/retry/route tests vẫn pass.
- Sources rechecked: [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Luật 91/2025/QH15](https://chinhphu.vn/?classid=1&docid=214590&orggroupid=1&pageid=27160); doc US-01/optional flow và security/privacy delta được rà. Không kết luận tuân thủ toàn hệ thống. Các release/native/deletion/token limits phía dưới còn nguyên.

**Current result: passed cho color/replay-entry scope đã kiểm chứng; không phải release certification toàn hệ thống.**

## Contract và nguồn chuẩn

- [Plan + fields/AC/edge cases](../../plans/2026-10-07-optional-birth-details-planet-surface.md), US-01/02/06 được cập nhật cross-reference.
- Nguồn UI vẫn là `../../design-directions/ultraviolet-paper-2026-10-06/reference.png`. Người dùng yêu cầu thêm độ sâu tím như bề mặt hành tinh thật subtle, không đổi concept nền kem/tím/lime.
- So sánh nguồn 853×1844 chuẩn hóa 390×844 với runtime 390×844 trong [comparison.png](comparison.png), cả hai đã được mở để kiểm tra. Trái là nguồn, phải là bản chạy. Ngày và nội dung khác nhau; card runtime cao hơn vì copy thật dài hơn, không phải cùng-state pixel diff.

## Đã sửa và xác minh

| Hạng mục | Bằng chứng |
|---|---|
| Optional ngay dưới ngày sinh, mặc định đóng; không thêm bước bắt buộc | `birth-collapsed.png`, `birth-expanded-unknown.png`; BirthDatePage test |
| Giờ/phút bằng select, không suy ra phút; 00:00 hợp lệ | BirthDatePage và optionalBirthInput tests |
| Khoảng giờ/chưa biết giữ độ chính xác; text nơi sinh phải chọn kết quả hoặc xóa | validation/helper tests; form browser |
| Consent riêng không tích sẵn; đổi giờ/nơi phải đồng ý lại; skip xóa draft | `birth-full-consent.png`, `birth-320-skipped.png`; regression tests |
| Supplement được tính trước Note, xóa cache RAM; retry không duplicate DOB/supplement | test thứ tự save/read và hai failure stages |
| Thông tin đủ không hỏi lại trong Radar | Browser nhập synthetic 01/01/1990, 07:30, Hà Nội → `/radar/continue`, không submit consent Radar; regression test |
| Reveal có Aura/nguồn dữ liệu đúng và lối đọc tổng quan | `reveal-full.png`; click mở `/natal` thật |
| Không upsell thêm giờ khi đầy đủ; chỉ thiếu nơi thì CTA đúng nơi | `natal-full-no-add-cta.png`, Home full state; 6 birthReadiness tests và Insights test |
| Responsive/đọc được sáng tối | `birth-320-expanded.png`, `birth-320-skipped.png`, `birth-dark-expanded.png`, `home-dark.png` |
| Texture dùng lại trên các focus card | `home-light-final.png`, `tarot-light.png`, `radar-light.png` |

Browser đo document width = scrollWidth ở 390 và 320 trong các capture đã kiểm tra. Không thấy page-level overflow, label/consent/CTA không chồng nhau. Expanded form dài hơn viewport và cần scroll theo lựa chọn của user; không ép tất cả form vào một màn.

## Chất liệu và tương phản

Asset runtime: `apps/web/public/assets/ultraviolet/violet-planet-v2.webp`, 640×800; ImageGen tạo vân khoáng/relief nhẹ và ánh sáng một phía. CSS trộn `soft-light` với `#4b278f`; thêm rim/contact shadow nhẹ. Không parallax, animation hay thêm wallpaper sao. Các chữ vẫn là DOM thật.

**Không dùng texture thô dưới chữ.** Ảnh thô chỉ đạt kem 3.21:1/lime 2.98:1 ở pixel sáng nhất. Tính sRGB sau soft-light trên màu tím đạt tối thiểu kem 8.39:1/lime 7.79:1. DOM xác nhận blend mode có hiệu lực. Đây là kiểm tra lớp nền/chữ chính, không chứng nhận WCAG toàn hệ thống. Cần giữ kiểm tra này khi đổi màu nền hoặc bỏ blend.

Texture rất nhẹ ở kích thước điện thoại; ưu tiên đọc nội dung thay vì thể hiện hố hành tinh rõ. Moon/orbit minh họa giữ vị trí cũ. Đã mở comparison, form 320 và dark capture để rà visual.

## Gates

- `pnpm web:lint`, `pnpm web:typecheck`, `pnpm web:test`: pass, **44 files / 165 tests**.
- `pnpm verify:runtime`: mock/privacy/mobile config guards pass.
- `pnpm web:build`: pass. Existing >500KB JS chunk warning vẫn còn; không phải regression phát sinh từ texture này.
- Console: không có JS error trong browser actions đã chạy.
- Doc: đọc AGENTS, US-01/02/06 và chart synthesis release runbook; docs trên được cập nhật, không thay AC consent bằng consent cơ bản.
- Security: dùng owner session/CSRF/API hiện hành; không thêm credential, role, public access hoặc endpoint. Không thay quyền Radar.
- Privacy: draft trong RAM; không giờ/nơi sinh trong URL, browser persistent storage, analytics/public share hoặc gửi ImageGen/provider. Search nơi sinh đi qua POST backend hiện hành trước khi lưu; không GPS hay địa chỉ nhà. Checkbox xác nhận mục đích bổ sung rõ ràng, không tick sẵn.
- Nguồn đối chiếu: [Luật 91/2025/QH15](https://chinhphu.vn/?classid=1&docid=214590&orggroupid=1&pageid=27160), [WCAG 2.2](https://www.w3.org/TR/WCAG22/). Không đưa ra kết luận pháp lý toàn sản phẩm.

## Giới hạn và việc chưa xác minh

- Phiên browser QA còn pending Radar từ kiểm thử trước: welcome/date-only trả về `/birth-time` theo flow Radar đang dở là hành vi chủ ý. Date-only không có pending Radar được phủ automated routing/save tests, chưa chạy lại một browser E2E hoàn toàn mới trong đợt này.
- Xóa supplement: thêm invalidate overview trong code, nhưng chưa rerun thủ công toàn flow xóa/rút quyền; không đánh dấu AC này hoàn tất.
- GET supplement không trả giờ thô. Flow sửa hiện tại xác nhận lại dữ liệu, không bổ sung response PII chỉ để prefill. Nhãn khoảng giờ “Đêm · sau 22h” từ flow hiện hành còn chưa mô tả đầy đủ đầu ngày; cần đối chiếu engine window riêng, không âm thầm đổi thuật toán.
- Chưa test mọi deep-link/result/share/token state với texture mới; shared CSS áp dụng, không đồng nghĩa các flow đã được chứng nhận lại.
- Không sửa engine/backend trong lượt này, không chạy toàn backend suite; dirty backend/content/infra work có trước được bảo toàn.
- Không xác minh native iOS/Android, production, screenshot xuất share, account auth hoặc trải nghiệm nội dung của người dùng thật. Copy thật dài còn khiến lựa chọn Tarot/Radar xuống dưới fold; không cắt nội dung để làm giả fidelity.

**Kết quả: passed cho phạm vi visual và optional-onboarding đã có bằng chứng; partial cho release/end-to-end tổng thể theo giới hạn trên.**

Preview: [Home + form tùy chọn](preview.png). Local: [Home](http://127.0.0.1:5207/home), [Birth](http://127.0.0.1:5207/birth). Không dùng link local để mời người ngoài thử.
