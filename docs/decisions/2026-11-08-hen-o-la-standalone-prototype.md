# Hẹn ở Lá: bản thử độc lập, chưa phải tính năng (08/11/2026)

Mức: **L**. Đây là trải nghiệm mới, và quy trình §0 xếp tính năng mới vào L. Khi phân vân, chọn mức cao hơn.

## Quyết định

`prototype/hen-o-la/` là bản thử cảm giác, chạy độc lập trên máy:
- Trang tĩnh, classic script, không build, không dependency.
- Dùng lại sprite và A* của `prototype/game-lab-14/engine.js`.
- Luật nằm ở module thuần UMD (`event.js`, `cafe.js`, `duo.js`, `spectate.js`, `world.js`) để test bằng `node --test`.
- Hình quán dùng chung qua `room.js`.

Bản thử **không** nối vào `apps/web` hay `apps/api`. Không có tài khoản, mạng, lưu trữ, analytics hay bên thứ ba. Mọi người trong đó là nhân vật hư cấu. Note và ảnh kỷ niệm chỉ nằm trong tab.

## Vì sao

Owner cần cảm nhịp của một buổi ghép đôi dạng sự kiện trước khi quyết có làm thật không. Nếu làm thật, sẽ thành mạng xã hội hoặc trò chơi điện tử theo Nghị định 147/2024, có dữ liệu nhạy cảm (quan hệ, cảm tình) theo Nghị định 356/2025, và cần kiểm duyệt lời nói. KS-26 vẫn BLOCK. Bản thử độc lập cho thử ý tưởng mà không đụng tới các rủi ro đó.

## Hệ quả và khoảng trống (ghi theo G1)

- **Chưa có US/AC, PRD hay SRS** cho Hẹn ở Lá. Thiết kế nằm ở:
  - `docs/research/2026-11-07-*`
  - `docs/research/2026-11-08-hen-o-la-*`
  - `prototype/hen-o-la/README.md`, `AGENTS.md`
  
  Phải viết US/AC trước khi đưa vào sản phẩm.
- **Câu chữ là bản nháp** (G3). Đây là ngoại lệ cho bản thử: **owner đã đồng ý trong chat ngày 08/11/2026** ("Đồng ý ngoại lệ").
  - Câu chữ trong `prototype/hen-o-la/` chưa được duyệt để vào sản phẩm. Người dùng thật chưa thấy vì chưa có đường deploy.
  - Owner duyệt câu chữ khi đưa vào app. Câu về quyền riêng tư và an toàn luôn do owner duyệt.
  - Ngoại lệ chỉ áp dụng cho bản thử này, không áp dụng cho câu chữ trong `apps/`.
- **Threat model ngắn** (G7):
  - Không có endpoint, phiên hay lưu trữ.
  - Đầu vào tự do duy nhất là bong bóng (≤ 40 ký tự) và note (≤ 60 ký tự). Cả hai được làm sạch ký tự điều khiển và render bằng `textContent`.
  - Trang có `noindex` và `no-referrer`.
  - Đường hỏng: đóng tab là mất hết, không còn gì để xoá.
- **Data privacy** (G8): không thu, gửi hay lưu dữ liệu cá nhân. Lựa chọn trong buổi (lá, thư, chọn đèn, "đi tiếp cùng nhau") chỉ nằm trong bộ nhớ của tab.
- **Đưa vào sản phẩm** cần một quyết định mới của owner, kèm: US/AC, kiến trúc realtime, kiểm duyệt, kiểm tuổi, đồng ý riêng cho dữ liệu nhạy cảm, data map, và review pháp lý theo tài liệu research.
