# Time selector, diễn giải dễ hình dung và vân tím — 07/10/2026

Phạm vi: local web tại `http://127.0.0.1:5207`. Không deploy, push hoặc gọi API trả phí. Receipt này thay thông số vật liệu 0.09 trong lượt trước, không xóa bằng chứng lịch sử.

## Hành vi và contract

`BirthTimeInput` là component chung cho giờ sinh tùy chọn ở `/birth`, bổ sung/chỉnh sửa qua `/birth-time`, và người kia ở `/radar/start`. Giờ/phút dùng native select, không buộc gõ dấu `:`. Empty hoặc thiếu phút không biến thành 00. `00:00` hợp lệ. Nhóm nút native có tên nhóm và `aria-pressed`, focus bàn phím và chiều cao 44px tại viewport 320.

- Onboarding và bổ sung thông thường: Biết giờ / Nhớ khoảng / Chưa biết; khoảng giờ dùng chung một danh sách.
- Radar nhập người kia: Biết giờ / Không rõ giờ. API hiện chỉ hỗ trợ exact/unknown, **không thêm nút approximate giả**. Unknown xóa giờ draft và không dùng Moon/Rising/House của người kia.
- Hoàn thiện chart chủ thể để tiếp tục Radar: chỉ exact vì contract của nhánh này cần chart đủ giờ/nơi; không thay điều kiện backend bằng lựa chọn UI.
- Đổi thông tin tùy chọn ở onboarding vẫn hủy consent bổ sung; không gửi dữ liệu trước kiểm tra trường và consent riêng. Không đổi schema/API, độ chính xác tính toán hoặc quyền dữ liệu.

## Nội dung

Nguồn đoạn bị phản ánh là `full_frame()` nhánh natal aspect trong `knowledge.py`, không phải một prompt Luna mới. Sáu góc Mars–Moon đã được viết thành tình huống riêng, cả hai thứ tự hành tinh cho cùng nội dung. Ví dụ square đã hiện thật trên `/note/today`:

> Khi ai đó làm bạn khó chịu, bạn có thể muốn nói thẳng ngay. Nhưng bạn cũng lo cuộc nói chuyện sẽ căng hơn, nên lại giữ trong lòng. Điều khó ở đây là nói rõ điều mình không đồng ý mà hai người vẫn nghe được nhau.

Các cặp khác dùng hành vi rõ hơn cho 14 body keys + cầu nối theo góc, không còn nối những cụm “được hành động thẳng”, “giành phần ưu tiên” và không khẳng định orb gần bảo đảm hành vi rõ ngoài đời. Orb/độ/góc vẫn giữ trong facts, ranking và evidence. Không thêm dữ kiện nhà/transit khi chart thiếu dữ liệu.

Renderer tăng từ `deterministic-vi-v8` lên `v9`. Content review chặn cụm đã loại; cơ chế sửa bản deterministic hiện hành của cùng chủ thể/cùng plan tự kích hoạt revision mới khi gặp cụm cũ. Browser reload đã xác nhận đúng bản mới. Saved/shared historical snapshots không bị viết đè. Regression test kiểm tra bản cũ còn nguyên trong bộ nhớ repository.

Đây **không phải** chứng nhận toàn bộ content đã dễ hiểu: các cặp generic còn dùng cầu nối dùng chung; sign/Jyotish/Tarot không được viết lại hết trong lượt này. Hook/scene tâm lý và thesis chart có thể còn lệch trọng tâm, cần audit sự nhất quán chung ở lượt content tiếp theo. Ma trận natal-scene mới nằm trong bundled knowledge; editor hiện tại của CMS chưa cho sửa riêng cả sáu đoạn Mars–Moon. Không đánh đồng CMS đang có với một editor đầy đủ cho ma trận này.

## Visual QA

- [Source bên trái / runtime bên phải, component cùng 06:15 và focus phút](time-component-comparison.png). Nguồn được scale về cùng chiều rộng UI; labels uppercase, segment active, native select và ring focus được giữ. Chênh lệch type/spacing nhỏ theo form density là P3, không che lỗi layout.
- [Home nguồn / runtime tại 390×844](home-reference-comparison.png). Dùng copy/date thật khác reference; không thay bằng text giả để ép card ngắn. Card thực dài hơn và lối Tarot/Radar xuống dưới fold là follow-up density, không tuyên bố pixel-identical.
- [Note thật sau sửa](note-390.png), [onboarding exact](birth-exact-390.png), [approximate](birth-approx-390.png), [unknown 320](birth-unknown-320.png), [exact 320](birth-exact-320.png), [supplement Radar owner](supplement-time-390.png), [Radar người kia](radar-exact-390.png).
- Texture 0.50 luminosity thay 0.09 quá nhẹ. Giữ base `#4c2e8e`, vùng sáng trên-trái và địa hình/hố nông nhìn rõ hơn, không tạo CSS gradient/ảnh nền giả. Không thêm texture vào nền trường nhập liệu.
- Mô hình blend trên toàn bộ 512.000 pixel asset: minimum contrast kem **5.42:1**, lime **5.03:1**. Đây là kiểm tra giới hạn cho asset hiện tại, không phải đo/chứng nhận mọi pixel chữ trên mọi màn hình.
- Browser: chọn 06:15, 00:00, approximate Chiều, unknown, focus bàn phím; chưa gửi dữ liệu sinh của người khác. Onboarding ở 320: width = scrollWidth = 320; nút mode cao 44px. Không thấy lỗi JS trong actions đã kiểm tra.

## Gates / giới hạn

- Frontend: lint/typecheck/build pass; 45 files / 169 tests pass; mock/privacy/mobile-config runtime guards pass. Cảnh báo JS bundle >500KB có sẵn vẫn còn.
- Backend: full pytest pass; Ruff trên reading domain/tests và CMS test đã sửa pass. Review 10 **synthetic** personas, 30 readings: không critical/high, **36 medium follow-ups còn tồn tại**. Không gọi đây là test với 10 người thật.
- Security/privacy: dùng lại session/CSRF/consent hiện hành; không thêm trường thu thập, credential, endpoint public, lưu draft bền vững, GPS hoặc bên nhận dữ liệu mới. API/worker trả phí bị tắt khi chạy QA. DB QA giữ nguyên, không reset dữ liệu để che bản đọc lỗi.
- Native/production, full deletion/withdrawal/share/revoke, mọi deep-link/dark-state và đánh giá đọc hiểu bởi người thật chưa được chứng nhận lại. Nhãn khoảng “Đêm · sau 22h” vẫn có khoảng chưa diễn đạt rõ đầu ngày; không đổi midpoint backend trong lượt component.

## Nguồn rà soát

[W3C nhóm field](https://www.w3.org/WAI/tutorials/forms/grouping/), [W3C radio pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/), [WCAG 2.2](https://www.w3.org/TR/WCAG22/): tham chiếu labels/group/selected state/focus/contrast; component hiện là nhóm nút toggle, không giả ARIA radio mà thiếu arrow-key behavior.

[Microsoft Learn nội dung giao diện](https://learn.microsoft.com/vi-vn/power-platform/well-architected/experience-optimization/user-interface-content): dùng câu trực tiếp và từ thông dụng; không coi nguồn này là bằng chứng diễn giải astrology đúng với một người.

[Luật 91/2025/QH15](https://chinhphu.vn/?classid=1&docid=214590&orggroupid=1&pageid=27160), AGENTS.md, US-01/02/06 và chart synthesis runbook là ranh giới consent/độ chính xác; không kết luận tuân thủ pháp lý toàn hệ thống.

**Final result: passed cho UI component, cập nhật vật liệu và sửa đoạn natal aspect đã có bằng chứng; không phải chứng nhận content/release toàn sản phẩm.**
