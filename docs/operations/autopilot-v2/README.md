# Autopilot v2: thiết kế vòng auto (owner duyệt 12.11.2026)

Đây là nguồn chuẩn cho vòng auto mới. Nó thay chỉ tiêu "20 PR/ngày" bằng một vòng khép kín có luật, chỉ số dẫn tới hành động, bằng chứng chạy thật và phản biện plan.

## Cách bản này được làm ra

1. `learned-catalog.md` gom 166 mục lá, mỗi mục một mã:
   - yêu cầu của owner (R);
   - lỗ hổng tìm thấy trong code (G);
   - 42 bài AI Native DevCon 2026 (D);
   - 3 video của Lauren Tan (L);
   - nghiên cứu bên ngoài (E);
   - kết quả rà UI (U);
   - phản biện của Codex (C).
2. Có hai thiết kế viết độc lập: `claude-full-design.md` và `codex-indep.md`.
3. Phản biện chéo qua các file `claude-review-of-codex.md`, `codex-x.md`, `claude-rA.md`, `codex-rA.md`, `codex-rB.md`. Kết luận của Codex: **chốt nếu sửa**. Các chỗ cần sửa đã được áp vào bản này.
4. Phần bổ sung: tầng giá trị (`value-layer.md` + `codex-value.md`) và làn tài liệu (`docs-lane.md` + `codex-docs.md`).

Ma trận truy vết từng mã nằm ở mục 9 của `claude-full-design.md`. Một script đã kiểm: cả 166 mục đều được nhắc tới. Phần kiểm nghĩa của từng mục là việc ở P1.

## Kiến trúc (4 tầng)

- **Nền tin cậy**:
  - `policy.json`;
  - manifest có chữ ký của owner, credential nằm ngoài agent;
  - `mergeGate` tự phân loại diff;
  - khoá chạy riêng (idempotency);
  - hàng rào kiến trúc cứng;
  - sandbox.
- **Thấy và kiểm**:
  - skill `verify-la-lanh` + CLI, bản đồ tính năng;
  - UAT độc lập với credential riêng;
  - verifier theo AC;
  - bằng chứng gắn vào PR;
  - bot tái hiện lỗi;
  - eval nội dung, có phần giữ kín;
  - test sạch.
- **Điều khiển**:
  - hợp đồng chỉ số;
  - `decide()` có 10 nhánh và trạng thái đóng băng bền;
  - tầng mục tiêu;
  - `critic()`;
  - vòng ngoài;
  - sổ phát hiện.
- **Học**:
  - lỗi lặp lại thành luật cứng;
  - "nằm mơ" có ngân sách;
  - đăng ký skill kèm eval;
  - gu của owner thành dữ liệu;
  - wiki và ADR;
  - kiểm nghi thức hằng tháng.

## Giai đoạn (sau 2 vòng phản biện thêm)

| GĐ | Nội dung | Nghiệm thu |
|---|---|---|
| P0 | Sửa 2 lỗi P1 của cổng merge, sandbox lần 3, review lại và merge #448–#451, đưa thiết kế vào repo | Các PR đã merge và đang chạy |
| P1 | (a) Broker giữ credential, thu hồi PAT; bằng chứng khoá theo head + base + artifact + policy; manifest; khoá chạy riêng; hợp đồng chỉ số; bảng 4 trạng thái; watchdog ngoài Mac; lệnh dừng xác thực. (b) Verify runtime + bản đồ tính năng; cài lỗi trong sandbox; eval skill của chính vòng; truy vết kiểm nghĩa; chạy lại dữ liệu 14 ngày | Giả làm owner không vượt được quyền; base đổi thì huỷ bằng chứng; bắt 100% lỗi nghiêm trọng đã cài |
| P2 | 360/390, Lighthouse/a11y, hàng rào kiến trúc, UAT độc lập, bot tái hiện, eval nội dung, test sạch; sửa U2/U5/U7/U9 và nút X đè chữ | UAT xanh mỗi đêm; độ phức tạp không tăng |
| P3 | `decide()` + phục hồi + hồ sơ đêm + chạy bóng + `critic()` + review theo tầng | 100% bất biến an toàn khi chạy bóng |
| P4 | Mở đêm theo hồ sơ lòng tin của từng loại thay đổi (có khoảng tin cậy) | Tự hạ quyền khi vượt ngưỡng |
| P5 | Go-live, không chờ tầng mục tiêu: nội dung → runtime → 5 tester; cổng bảo mật và riêng tư | Owner ra lệnh; ≥ 4/5 tester hoàn tất |
| P6 | Tầng mục tiêu; mục tiêu đầu tiên "nội dung hay hơn" | Thắng so cặp mù mà đối trọng vẫn đạt |
| P7 | Học: nằm mơ, eval skill, wiki/ADR, vòng ngoài, bộ chấm theo gu | — |
| P8 | Auto hết: diễn tập quay lui, canary theo power, lệnh phát hành thường trực có chữ ký | — |
| P9 | Lá Dám → café | — |

## Chất lượng khi chạy auto (câu trả lời đã thống nhất với Codex)

- **Không có bảo đảm tuyệt đối.**
- **Bảo đảm được** các bất biến đã khoá bằng code và đã được kiểm, trong phạm vi quyền bị khoá.
- **Chỉ giới hạn được** tỷ lệ lỗi lọt của từng loại thay đổi. Mục tiêu là bắt 100% lỗi nghiêm trọng đã cài trước khi mở quyền.
- **"Hay" không suy ra được từ test xanh**; phải có người đọc đánh giá.
- **Quay lui không xoá được dữ liệu đã lộ.**
- **Phát hành vẫn cần lệnh của owner.**

## Nguyên tắc vận hành mới (thay chỉ tiêu PR)

- Mỗi ngày 3–5 việc. Mỗi việc ghi:
  - US/AC;
  - loại giá trị A–E;
  - dòng `Người dùng thấy gì:`;
  - cách kiểm.
- WIP: 1 việc đang làm + 1 việc đang review.
- Rảnh còn hơn làm việc độn.
- Báo cáo theo giai đoạn và chỉ số, không theo số PR.
