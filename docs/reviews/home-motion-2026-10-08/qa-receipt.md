# Home motion — QA 2026-10-08

## Phạm vi

Home local tại `http://127.0.0.1:5207/home`. Giữ Ultraviolet Paper và toàn bộ nội dung/luồng đang có. Không deploy, đổi backend, bật generation, gọi API trả phí hoặc thêm thư viện.

## Thay đổi

- Hành tinh của Note chuyển động theo vòng nhỏ 10 giây; bộ bài nghiêng nhẹ 8 giây; cặp hành tinh dùng chu kỳ 13 giây lệch pha; sao trên advice sáng nhẹ 5.5 giây. Các vòng lặp tiếp tục, không chỉ chạy một lần.
- Note fade vào 360ms, không dời vị trí chữ. Nút chọn góc vẫn đứng yên; chỉ ảnh bên trong chuyển động.
- Nút 44×44 cạnh hồ sơ dừng/bật bốn vòng lặp. Không lưu trạng thái ra storage. Reduced Motion tắt hiệu ứng và ẩn nút.

## Kiểm chứng

- Production build + TypeScript và ESLint: pass.
- Web tests: 191/191, 47 file. Có kiểm thử pause/resume không thay note, không refetch, không khóa hành động; kiểm thử CSS Reduced Motion.
- Runtime mock, privacy và mobile release guards: pass. Đổi fixture kiểm thử query sai thành khóa không nhạy cảm; không nới guard hoặc thay logic lọc query.
- Browser bản build: bốn animation có `infinite`; transform hành tinh thay đổi giữa hai lần đọc DOM, vị trí headline không đổi `(44, 229.1953125)`; không tràn ngang ở viewport hiện tại 458px.
- Pause: cả bốn computed `animation-play-state` = `paused`; hai mẫu transform cách nhau qua thao tác mở/đóng chọn góc giống nhau. Resume trả về chạy. Sheet chọn góc vẫn mở/đóng được khi dừng.
- Bắt được lỗi specificity khiến hai hình khám phá chưa dừng; đã sửa và kiểm tra lại trên browser, không chỉ bằng unit test.
- Ảnh chụp: [Home](./home.png). Đây là ảnh tĩnh, xem chuyển động trực tiếp ở URL local.

## Ba quality gates

- Doc: bổ sung AC chuyển động vào US-03. Không đổi thứ tự Home hoặc contract nội dung.
- Security: không thêm endpoint, quyền, session, HTML động, dependency hay dữ liệu từ nguồn ngoài. Chỉ CSS transform/opacity và state React.
- Privacy: không thu dữ liệu, không analytics, không đọc/ghi storage hoặc gửi trạng thái chuyển động. Chi phí API phát sinh: 0.

## Chưa kiểm chứng / rủi ro còn lại

- Browser hiện tại có Reduced Motion = false; nhánh Reduce được kiểm tra bằng cascade/CSS unit test, chưa bật OS Reduce Motion để quan sát trực tiếp.
- Chưa test thiết bị iOS/Android thật hoặc đo pin/FPS. Bundle JS vẫn có cảnh báo có sẵn >500kB; thay đổi này không xử lý code splitting.
- Không tuyên bố đã QA lại toàn bộ backend, nội dung hay tất cả tính năng live. Production chưa cập nhật trong yêu cầu này.

## Nguồn chính thức đã rà

- [WCAG 2.2 — Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html): chuyển động tự chạy lâu hơn 5 giây có cơ chế dừng.
- [MDN — prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion): ưu tiên người dùng yêu cầu giảm chuyển động.
