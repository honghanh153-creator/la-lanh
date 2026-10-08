# Rà toàn bộ frame — Ultraviolet Paper

Hoàn tất vòng sửa và chụp lại ngày 07/10/2026. Đây là **bản local để review**, chưa deploy hoặc push. Thư mục dùng ngày bắt đầu 06/10 để giữ cùng một bộ bằng chứng.

Nguồn chọn: `../../design-directions/ultraviolet-paper-2026-10-06/reference.png` (853 × 1844). Chuẩn hóa về 390 × 844 CSS px, mật độ khoảng 2.187. Ảnh runtime chụp bằng browser ở 390 × 844, density 1; bốn kiểm tra nhỏ ở 320 × 740. Không vẽ lại mock thay cho screenshot.

Mở [gallery.html](gallery.html) để xem các frame thực tế; [comparison.png](comparison.png) đặt nguồn và Home mới cạnh nhau. Nội dung ngày 07/10 dài hơn câu mẫu ngày 06/10: card được tăng chiều cao, không cắt câu, vì vậy Tarot/Radar cần cuộn xuống. Không coi đây là so sánh pixel-perfect với dữ liệu giống hệt nhau. Khối khám phá được đối chiếu riêng trong `comparison-explore.png`.

## Những gì đã sửa

- Home: giữ một Note tím; date + mood; moon là lối đổi góc; Đọc thêm / thumbs / share nằm trong card. Bỏ hàng đổi góc, nút giữ thử nghiệm và hàng Natal/Sky dư thừa khỏi Home. Thử nghiệm vẫn còn ở Note chi tiết, Natal/Sky vẫn vào từ Khám phá.
- Chỉnh lại khoảng cách, cỡ chữ, icon nav, kích thước minh họa, grain giấy tím và motif quỹ đạo theo nguồn. Một font, không ảnh cosmos phủ toàn trang.
- Radar: hero tím và ảnh đôi; bỏ progress trên trang giới thiệu. Các form vẫn có tiến độ và consent. Sửa disclosure chỉ báo, lịch sử, copy link, giải thích cho người nhận và Tarot bridge bị nhạt hoặc dính nền tối cũ.
- Tarot: minh họa fan đồng bộ; selected 1/3/5 rõ; xòe bài và từng lá đọc dùng texture tím, icon thư viện thay glyph. Không thay thuật toán/chọn bài.
- Sửa nhãn mẫu dính dòng, CTA quyền riêng tư đi nhầm onboarding, orb Aura đè tiêu đề, focus tự động tạo viền trang trí, danh mục nơi sinh chia cột/cắt helper và nhãn nav xuống dòng ở 320px.

## Danh sách màn và phạm vi quan sát

| Nhóm | Route/frame | Đã xem |
|---|---|---|
| Điểm vào | `/`, `/welcome`, alias `/consent` | Welcome; `/` nối phiên theo router hiện có |
| Ngày sinh | `/birth`, `/reveal` | Form trống, reveal, breakpoint 320px |
| Lớp cá nhân | `/birth-time` | Prompt, biết giờ, gần đúng, chưa biết, danh mục 34 nơi, review với consent chưa tích |
| Mở Aura | `/aura-cutover`, alias `/reveal/aura` | Trạng thái lớp đã tính; giữ các lựa chọn hiện có |
| Home | `/home` | Sáng/tối, card dài, phần khám phá, mood sheet, context sheet, 320px |
| Note | `/note/today` | Bản đọc thật; thử nghiệm/bằng chứng/disclaimer vẫn riêng |
| Bản đồ | `/insights`, alias `/natal` | Tóm tắt, các lớp, đường tới Sky và cách tính |
| Đọc sâu | `/insights/:claimId` | Moon Western, Moon Jyotish, synthesis; các claim khác dùng cùng template, không giả định đã đọc hết nội dung |
| Cách tính | `/insights/settings` | Cài đặt hệ nhà; không đổi chart lưu để chụp ảnh |
| Bầu trời | `/insights/current-sky` | Grid hành tinh và timestamp |
| Tarot | `/tarot`, `/tarot/:sessionId` | Form, 3/5 lá, draw, kết quả, phần đọc dài; hai lượt bốc thật dùng câu hỏi QA về chia việc nhóm |
| Hợp gu | `/radar`, alias `/vong-la` | Landing, CTA check riêng, breakpoint 320px |
| Check kín | `/radar/start` | Form, trường, consent; report QA có người kia không rõ giờ sinh |
| Lời mời | `/radar/invite`, alias `/vong-la/setup` | Form, tạo và copy link QA localhost, lịch sử, trạng thái chờ |
| Người nhận | `/radar/i/:token`, `/radar/continue` | Link QA còn hiệu lực và link sai; màn consent riêng, không tích thay người nhận |
| Receipt | `/radar/receipt` | Không có receipt trên thiết bị; nhánh kết quả người nhận trên thiết bị thứ hai chưa chạy |
| Báo cáo | `/radar/result/:requestId` | Signature, ba chỉ báo, mục lục, chương và cuối trang |
| Thẻ | `/card`, `/birth-card` | Preview, tỷ lệ, các nút xuất/chia sẻ; không gửi ra ngoài |
| Link share | `/share/:token` | Link không còn hoạt động; valid-token/share native chưa chạy trong vòng này |
| Thư viện | `/saved` | Note đã lưu và lối mở revision |
| Mình | `/profile` | Profile, data/settings, bật tối rồi trả sáng |
| Tài khoản | `/existing-user` | Màn thông báo guest; đăng nhập thật vẫn chưa được triển khai |
| Tính năng dừng | `/la-chung/*`, `/la-chung/i/:token` | Thông báo dừng, không khôi phục tính năng |
| Quyền cũ | `/la-chung/history`, `/la-chung/manage-response` | Empty history và form rút quyền; không xóa dữ liệu |
| Kết quả cũ | `/la-chung/result/:requestId` | Chưa có dữ liệu lịch sử hợp lệ trong QA để rà bản có dữ liệu |
| Quyền riêng tư | `/privacy` | Tài liệu và các đường dẫn giữ nguyên |
| Lỗi route | Error boundary | Trang không tồn tại và lối quay về |
| CMS | `/studio` | Ngoài redesign khách hàng; không thay workspace/credential/quyền review |

## Kiểm tra kỹ thuật và ba gate

- Frontend lint, typecheck, build và 42 file / 146 test pass. Regression mới đảm bảo nút quyền riêng tư ở Demo đi đúng trang.
- Không thấy page overflow trong các frame đo 390px; Home/Radar/Tarot/Birth cũng không overflow ở 320px. Fan và chip Tarot được cuộn ngang có chủ đích, không kéo tràn cả trang.
- Console không có lỗi JS trong các thao tác đã chạy. Điều này không thay cho E2E toàn hệ thống.
- Texture mới: chữ kem tối thiểu **6.29:1**, lime **5.84:1**, tính theo pixel sáng nhất của asset. Không dùng chữ lime trên kem. Nút chính/feedback/sheet có vùng chạm tối thiểu 44px; không tuyên bố toàn sản phẩm đạt chứng nhận accessibility.
- Nguồn chuẩn đã kiểm tra: [WCAG 2.2](https://www.w3.org/TR/WCAG22/) và [Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html). Giữ checklist nghiệp vụ/consent trong US-01/02/06/12/13; không mở stranger matching.
- Security/privacy delta: chỉ layout/assets/link điều hướng. Không thêm field, SDK, permission, endpoint, thông tin sinh vào share hay chi phí API. Form review/recipient vẫn có consent chưa tích; không submit quyền thay người thật. Fixture/link chỉ ở localhost, không đăng ra ngoài. Không lưu token QA vào tài liệu này.

## Giới hạn còn lại

Chưa xác nhận native iOS/Android, native share/download, receipt hai thiết bị, valid public share/revoke và dữ liệu Lá Chứng lịch sử. Xuất ảnh Birth/Radar vẫn dùng bộ renderer hiện có, không phải bản export mới đồng bộ hoàn toàn. Một số câu đọc thật còn dài/trừu tượng; vòng này không thay engine/content, không coi UI đẹp là đã vượt gate nội dung. Bundle JS còn cảnh báo >500KB, cần code-splitting ở vòng hiệu năng riêng.

P3: texture/art được tạo lại theo nguồn nên không trùng từng pixel; Home thật dài hơn mẫu vì data khác. Không có P0/P1/P2 thị giác còn mở trong những frame đã sửa và chụp lại. Pass này chỉ là visual/interaction smoke cho phạm vi liệt kê, không phải chứng nhận hoàn tất tất cả US.

## Nguồn asset mới

ImageGen tích hợp, không gọi API trả phí: reference thật được dùng làm hướng phong cách. Bản gốc lưu cùng design direction và bản tối ưu trong `apps/web/public/assets/ultraviolet/`.

- `violet-paper.png` → `violet-paper.webp`: texture giấy tím lì, màu violet giàu sắc độ, sợi giấy rất nhỏ; không chữ, không đồ vật; chữ kem phải rõ.
- `header-orbit.png` → `header-orbit.webp`: nền trong suốt, một cung quỹ đạo tím mảnh và một sao coral bốn cánh; không UI/chữ; đặt sau header, không phủ nội dung.

Moon, Tarot fan và cặp hành tinh dùng lại asset cùng direction. Không dùng CSS art hoặc ảnh mock nguyên màn để thay giao diện thật.
