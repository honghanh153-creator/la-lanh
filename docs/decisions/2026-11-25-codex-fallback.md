# Codex sửa thay Claude khi Claude gần hết hạn mức tuần (#894)

Ngày: 25.11.2026. Người viết: Claude. Người review: Codex (vòng tự động), phản biện thứ hai theo §4.4 của `docs/operations/collab-auto-loop-plan.md`. Mức: L (vòng tự động ghi code và push thay một agent; chạy code của nhánh trên máy owner).

## Bối cảnh

Owner 22.11: "chuyển qua codex khi claude gần hết. giữ 5% claude để duy trì nếu cần" và "tôi cần có phản biện nên ko muốn codex làm 1 mình". Owner 23.11 cho phép sửa R1 theo hướng này (L82). Từ 95% giới hạn tuần Claude, lượt "Claude sửa" phải có người làm, nếu không cả hàng việc đứng.

Rủi ro chính: lượt sửa chạy test của nhánh trên máy owner. Code trong nhánh là dữ liệu chưa tin (một PR có thể thêm test đọc file riêng, gọi mạng, sửa hook Git), và Codex có thể đổi chính luật cho phép việc của mình merge.

## Lựa chọn đã cân nhắc

1. **Giữ mọi PR chờ Claude** cho tới tuần sau.
   - Ưu: không chạy code nào của nhánh, không cần hộp cát.
   - Nhược: hàng việc đứng tới 3–4 ngày mỗi tuần; trái lời owner "chuyển qua codex".
2. **Codex sửa, test chạy thẳng trên máy** như phiên Claude.
   - Ưu: đơn giản, giống author check.
   - Nhược: test của nhánh đọc được thư mục nhà, token trong env, mạng; một PR độc hại lấy được dữ liệu riêng mà không ai đọc diff trước (Codex review r1 và auto-7, P1).
3. **Codex sửa trong hộp cát, test của nhánh trong hộp cát macOS, file cổng và việc của owner bị giữ trước khi tốn lượt, phản biện thứ hai trước merge.**
   - Ưu: dùng công cụ có sẵn trên máy (không cài thêm, không tốn phí, R13); cùng cơ chế Seatbelt mà Codex CLI dùng cho chế độ `workspace-write` trên macOS.
   - Nhược: `sandbox-exec` được Apple ghi là đã cũ (deprecated) dù vẫn chạy; test web/API không chạy trong hộp cát mà để author check làm sau, nên một bản sửa app hỏng tốn thêm một vòng.
4. **Test trong container** (Docker hoặc máy ảo).
   - Ưu: cách ly mạnh hơn, chạy cả test web/API.
   - Nhược: phải cài và chạy dịch vụ mới trên máy owner (cần owner duyệt, R2 loại 1), tốn RAM khi đang có 2 việc nặng (R10). Để sau, nếu cách 3 không đủ.

## Quyết định

Chọn cách 3:

- Codex chạy `codex exec -s workspace-write`, tắt mạng, `--ephemeral`, trong clone riêng `~/.cache/la-lanh-collab/fallback`.
- Test của nhánh chỉ là `node --test <file test>` (lệnh khác bị từ chối), chạy qua `collab-test-guard.mjs` của integration, `env -i`, trong `sandbox-exec`:
  - không mạng ngoài socket cục bộ;
  - chỉ ghi được trong clone và một thư mục tạm, `.git` của clone chỉ đọc;
  - không đọc được nội dung file trong `/Users`, `/Volumes`, thư mục tạm chung, `/opt`, `/usr/local`, trừ clone, thư mục tạm của lượt và thư mục Node (Codex auto-7 trên #894, P1 privacy). Tên và kích thước file vẫn đọc được để Node tìm đường dẫn.
- PR mang việc của owner (`owner-release-check`) hoặc đụng file cổng của vòng (luật, `.claude/`, `.github/`, lockfile, script và test của vòng, prompt và schema Codex review) được gắn `cho-claude` **trước** khi giữ lượt Codex, và hàng việc đi tiếp sang PR sau (Codex auto-7, P1). Xung đột merge nằm ở file cổng cũng bị giữ như vậy.
- Trước push: quét dữ liệu riêng tư, ghi dấu Codex đã sửa trên máy. Sau push: Author check, Codex review read-only, phản biện thứ hai (Antigravity, Claude hoặc Gemini) đúng head.

## Hệ quả

- Lượt sửa không tốn lượt Claude; mỗi lượt tốn một lượt Codex trong trần ngày (R8) và trần riêng của chế độ này.
- PR đụng vòng tự động chờ Claude cho tới khi hết chế độ này.
- Test của nhánh cần đọc file ngoài clone (ví dụ `node_modules` dùng chung) sẽ hỏng trong hộp cát; khi đó lượt sửa bị từ chối, không push.

## Rủi ro và đường hỏng

- Hộp cát hỏng hoặc bị bỏ trên bản macOS mới: `sandbox-exec` không chạy thì test không chạy và lượt sửa bị từ chối (không có đường chạy không hộp cát). Có test chạy thật trên macOS: đọc trong clone được, đọc file ngoài clone bị `EPERM`.
- Quy tắc Seatbelt: luật khớp sau cùng thắng, nên lệnh cho phép clone đứng sau lệnh chặn thư mục nhà (có test thứ tự).
- Lùi bản: tắt chế độ bằng file chế độ (`collab-usage.mjs`), nhãn `cho-claude` tự gỡ ở tick sau.

## Nguồn đã đọc

- `man sandbox-exec` trên máy owner (macOS 26): cách chạy với profile, ghi chú DEPRECATED.
- Codex CLI, chế độ sandbox trên macOS dùng Seatbelt: https://github.com/openai/codex (thư mục `docs/`, mục sandbox).
- Review Codex trên #894: r1 (23.11), auto-3, auto-7 (25.11).
