# Quyết định: author check chạy trên GitHub Actions (owner chọn gói A, 31.10.2026)

Mức L theo `docs/operations/product-development-process.md`.

## Bối cảnh

Ngày 31.10, author check (`pnpm check`) chạy lần lượt trên Mac của owner qua launchd. Mỗi PR mất 10–35 phút;
hạ tầng tự dựng (khoá, PATH, `ProcessType`, kiểm tra máy bận, hạn chót) sinh nhiều lỗi (retro K8, K10, K16,
K18, K19). Trong 10 PR merge từ 10:00, 6 là sửa chính vòng tự động.

## Research (1a + 1b)

- GitHub Actions: runner chuẩn miễn phí, không giới hạn phút cho repo public; tối đa 20 job song song (gói Free).
- Merge queue: chỉ cho repo thuộc organization; repo này thuộc tài khoản cá nhân, nên học ý tưởng (cập nhật
  nhánh với base và chạy lại CI trước khi merge).
- Rulesets / required status checks: có cho repo public gói Free.
- GitHub Security Lab "pwn requests": chỉ dùng `pull_request`; không `pull_request_target`; quyền tối thiểu;
  ghim action theo SHA; không chạy code PR với secret.

## Quyết định (gói A, 4 phần)

1. `.github/workflows/pr-check.yml`: PR vào `collab/integration` chạy check song song; phân mức theo file đổi
   (`docs` không chạy suite, `loop` chạy `collab:test`, `full` chạy đúng `pnpm check`). Sau khi workflow chạy
   ổn định, ruleset trên `collab/integration` yêu cầu `pr-check` xanh và nhánh cập nhật; cổng
   `collab-merge.mjs` chấp nhận check `pr-check` thành công trên đúng head thay cho comment "Author check".
2. Tự review trước khi mở PR: Claude chạy Codex trên nhánh, sửa xong mới mở PR.
3. Autopilot chạy ngay khi có PR bị trả về (owner bật "Always allow").
4. WIP: tối đa 1 PR quy trình mở cùng lúc, chỉ khi đang làm kẹt vòng; cải tiến khác gom mỗi tuần.

## Threat model ngắn

| Mối đe doạ | Chặn |
|---|---|
| PR fork chạy code đọc secret hoặc ghi repo | `pull_request` không có secret, token chỉ đọc; `persist-credentials: false` |
| Action bên thứ ba bị chiếm | Ghim theo SHA commit |
| CI xanh giả do bỏ suite | Phân mức chỉ theo đường dẫn; mọi file ngoài `docs`/`*.md`/script vòng → `full` |
| Merge khi head đổi sau check | `--match-head-commit` giữ nguyên; check gắn với head SHA |

## Hoàn tác

Xoá workflow và ruleset; cổng merge quay về comment "Author check" (code cũ vẫn hỗ trợ).
