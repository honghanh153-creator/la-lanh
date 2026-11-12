# Spec 1b — test nghiệm thu giữ kín, và không chạy mã PR trên Mac (bản đơn giản)

Mức: M. Owner chốt ngày 12.11.2026: **làm bản đơn giản, thử trước rồi tối ưu sau**.

Bản 8 (5 vùng quyền, 3 tài khoản Mac, GitHub App, 31 phép thử) được lưu ở `2026-11-12-spec-1b-ban-8-luu-tru.md`. Bản đó dành cho lúc app có người dùng thật, hoặc khi agent được cấp quyền cao hơn.

## Vì sao chọn bản đơn giản

App chưa có người dùng. `main` và deploy chỉ owner làm. A/B chỉ là thử nghiệm thăm dò 4 tuần. Hai rủi ro thật là:

1. Claude **vô tình** viết test cho dễ đạt, hoặc sửa test khi trượt. Đây là thiên lệch, không phải cố tình phá.
2. Mã của PR chạy trên Mac của owner. Rủi ro này có từ trước, không do thử nghiệm sinh ra.

Bản 8 chặn cả trường hợp agent cố tình vượt cổng, nhưng phải đổi lại khoảng 60 phút cài đặt của owner và nhiều phần phải vận hành. Mức đó chưa tương xứng với giai đoạn hiện tại.

## 1. Test nghiệm thu giữ kín (chỉ đợt B)

| Bước | Ai | Ở đâu |
|---|---|---|
| Viết AC cho việc, owner duyệt AC trong phiên | Claude soạn, owner duyệt | issue |
| Viết test Playwright hộp đen theo AC | **Codex, phiên mới** | **ngoài repo**: `~/.cache/la-lanh-collab/acceptance/<issue>/`. Claude không đọc thư mục này |
| Thử đột biến: cài 2–3 lỗi cố ý vào bản xem thử, test phải bắt được | Codex | nhánh `agent/probe-*`, xoá sau khi thử |
| Làm việc | Claude | PR như bình thường |
| Nghiệm thu: chạy test kín trên **đúng bản xem thử theo SHA** | Codex, phiên mới | ghi SHA, số test đạt/trượt, hash bộ test vào sổ |
| Owner nghiệm thu với 4 câu hỏi | owner | phiên duyệt |

Quy tắc:
- Claude không đọc, không sửa test kín. Nếu test trượt, Claude chỉ thấy **tên AC trượt**, không thấy mã test.
- Hash của bộ test được ghi vào sổ **trước khi Claude bắt đầu làm**. Lúc nghiệm thu, Codex chạy đúng bộ có hash đó.
- Thiếu test, hoặc test trượt, thì việc **không đạt nghiệm thu**.

**Giới hạn đã biết:** đây là **tách vai**, chưa phải chặn bằng quyền. Claude chạy cùng tài khoản máy, nên về kỹ thuật vẫn đọc được thư mục test. Báo cáo kết quả A/B phải ghi rõ giới hạn này. Kiểm mù sau nghiệm thu (phiên Codex mới) là lớp bù.

## 2. Không chạy mã PR trên Mac (thử từ 12.11)

- `collab-check.mjs` có thêm chế độ `LA_LANH_CHECK_SOURCE=ci`. Ở chế độ này, author check **đọc kết quả job `check` của workflow `pr-check` trên đúng head SHA**. Workflow đó chạy đúng `pnpm check`. Trên Mac **không còn** `pnpm install`, `make` hay `pnpm check` của PR.
- Trên Mac vẫn chạy:
  - quét dữ liệu riêng tư theo danh sách cục bộ của owner;
  - preflight (mẫu PR, lint tĩnh);
  - đồng bộ nhánh với integration (`git merge` + `push`).
  Các bước này không chạy mã của PR.
- Quy tắc: chỉ chấp nhận check `completed` + `success` do GitHub Actions tạo, đúng head. Chưa xong thì chờ lượt sau. Mọi kết quả khác là trượt. Trường hợp `cancelled` có ghi chú "chạy lại, không phải lỗi code".
- Biên nhận vẫn giữ dòng `Author check: PASS|FAIL @ <sha>` và marker như cũ, nên scheduler và `mergeGate` không phải đổi.
- **Bật**: `export LA_LANH_CHECK_SOURCE=ci` trong `collab-cron.sh`. **Quay lui**: xoá dòng đó.

Ngoài lề: Mac không còn chạy check 10–60 phút cho mỗi PR, nên đỡ nóng máy.

## 3. Sandbox cho phiên Claude (tuần 1a)

Thử trên 1 phiên, ở thư mục riêng `la-lanh-sbx`. Phép thử:
- `gh`, `pnpm`, `git push` vẫn chạy được;
- Bash đọc `~/Documents/canary-sbx.txt` thì bị chặn;
- Read tool đọc `~/.codex` thì bị chặn.

Đạt thì bật cho mọi phiên Claude.

## 4. Đo trong thời gian thử

- Số PR qua chế độ CI, và số lần biên nhận sai so với kết quả CI. Mục tiêu: 0 lần sai.
- Số lần vòng tự động bị kẹt vì CI chậm hoặc bị huỷ.
- Với đợt B: tỷ lệ đột biến bị bắt, số lần test kín trượt, phút owner.

Sau 1 tuần chạy chế độ CI không có lỗi thì xoá đường chạy local trong mã.

## 5. Dữ liệu cá nhân

- Không có luồng dữ liệu mới.
- Test kín chỉ dùng dữ liệu giả.
- Biên nhận chỉ có link run CI, không có log.
