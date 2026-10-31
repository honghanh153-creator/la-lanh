## Task

Related: #ISSUE_NUMBER
Agent thực hiện:
Agent review:

## Mục tiêu và thay đổi

## Ảnh hưởng tới task khác

File đang thay đổi / contract / migration / các bên cần sync:

## Cổng (docs/operations/product-development-process.md §3–4)

Mức: S | M | L. Ghi bằng chứng cho từng cổng bắt buộc theo mức; cổng không áp dụng ghi "không áp dụng" kèm lý do.

- G1 Tài liệu / US-AC:
- G2 UI/UX:
- G3 Câu chữ (owner duyệt nếu có câu mới):
- G4 BE + kiến trúc:
- G5 FE:
- G6 QC (test đỏ→xanh, author check):
- G7 Bảo mật:
- G8 Data privacy:
- G9 Release: không áp dụng cho PR vào integration
- G10 Chi phí / license:

## Kiểm thử

Lệnh đã chạy, kết quả và AC chưa hoàn tất:

## Security, data privacy và chi phí

## Bàn giao

Commit, quyết định, phần còn thiếu, bước tiếp theo:

## Review

Reviewer đăng comment `Review verdict: APPROVE | REQUEST_CHANGES @ <SHA>`.
Người làm chỉ merge khi SHA đó trùng head (`gh pr merge --merge --match-head-commit`).

PR task vào `collab/integration`. PR tổng vào `main` chỉ sau release review.
Không merge vào main, không deploy. Không dán secret hoặc dữ liệu người dùng.
