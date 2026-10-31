# Checklist quyết định: Claude tự quyết hay hỏi owner

Owner yêu cầu ngày 31.10.2026. Áp dụng cho Claude và Codex trong vòng tự động (`collab-auto-loop-plan.md`).
Mục tiêu: owner chỉ được hỏi những việc thật sự cần owner. Mọi việc khác agent tự quyết, làm, rồi báo lại.

## 1. Năm câu hỏi trước mỗi quyết định

Trả lời lần lượt. Gặp **"có"** ở câu nào thì dừng ở câu đó và làm theo cột "Kết quả".

| # | Câu hỏi | Kết quả nếu "có" |
|---|---|---|
| Q1 | Việc này **có nằm trong danh sách cấm** ở mục 2 không? | Không làm. Hỏi owner, kèm đề xuất. |
| Q2 | Có **câu chữ mới mà người dùng nhìn thấy** không (copy, nhãn, thông báo, bản đọc)? | Làm bản nháp + PR gắn `needs-owner`. Owner duyệt copy rồi mới merge. |
| Q3 | Có **thu thập, lưu, chia sẻ hay suy ra thêm dữ liệu cá nhân** không, hoặc đổi mục đích/thời hạn lưu? | Hỏi owner, kèm phân tích privacy (AGENTS.md mục 3). |
| Q4 | Có **đổi hướng sản phẩm** không (tính năng mới, bỏ tính năng, đổi thứ tự ưu tiên owner đã chốt)? | Hỏi owner, kèm 2 lựa chọn và khuyến nghị. |
| Q5 | Có **tốn tiền, không hoàn tác được, hoặc ảnh hưởng người dùng thật ngay** không? | Hỏi owner. |
| — | Cả năm câu đều "không" | **Tự quyết, làm, báo lại** trong tóm tắt cuối lượt. |

## 2. Danh sách cấm (luôn cần lệnh riêng của owner)

- Merge vào `main`, release, deploy, SSH hay chạm server/database thật.
- Bật provider, đổi IAM, secret, budget, gọi API trả phí ngoài review Codex trong vòng tự động.
- Đọc dữ liệu thật của người dùng trên production, kể cả của owner (owner có thể tự xem rồi gửi đúng trường cần).
- Cài PostgreSQL hoặc chạy probe #106 (owner loại trừ riêng ngày 29.10).
- Đăng dữ liệu cá nhân, ngày/giờ/nơi sinh thật, ảnh chụp tài khoản lên repo public.
- Viết `Duyệt`, `Giữ`, `Bỏ #N` thay owner trên issue plan.

## 3. Việc Claude tự quyết (ví dụ đã chốt)

| Loại việc | Tiêu chí đã thỏa | Ví dụ |
|---|---|---|
| Sửa lỗi kỹ thuật không đổi câu chữ | Q1–Q5 đều "không"; có test đỏ→xanh | #144 Jyotish 503, #142 kiểm tra "máy bận" |
| Thay đổi quy trình trong vòng tự động | Miễn phí, hoàn tác được; vẫn qua Codex review | Ops đi trước (#135), tick tự check (#137) |
| Sửa fix-forward P2 | Đã có verdict; không đổi copy | #140 |
| Hướng kỹ thuật khi dữ liệu thiếu | Không đổi dữ liệu thu thập | E1 #143: giờ khoảng vẫn đọc hành tinh, bỏ nhà/cung mọc |
| Việc local, miễn phí, riêng tư | Không chạm production | Cài job launchd, dọn lượt autopilot treo |

## 4. Input cần có trước khi quyết

| Input | Lấy ở đâu |
|---|---|
| Yêu cầu gốc và AC | PRD/SRS/US, issue task |
| Quyết định owner đã chốt | `collab-auto-loop-plan.md` §2, hub #2, memory của Claude |
| Bằng chứng | Repro (dữ liệu tổng hợp), test đỏ trên code cũ, log |
| Ảnh hưởng | Copy? Dữ liệu? Chi phí? Hoàn tác được không? |
| Cổng tự động | `pnpm check` (gồm `fallback_approval`, content audits), Codex review |

## 5. Khi phải hỏi owner

- Một câu hỏi, có **lựa chọn đánh số + khuyến nghị**, nói rõ hậu quả mỗi lựa chọn.
- Không hỏi lại điều owner đã chốt; không hỏi việc thuộc mục 3.
- Trong lúc chờ owner, làm tiếp việc khác (§3.2 cách làm hằng ngày); không ngồi chờ.
- Việc chờ owner được gắn `needs-owner` và hiện ở bảng trạng thái trên issue plan.

## 6. Ghi lại

Mỗi quyết định owner mới: ghi ngay vào `collab-auto-loop-plan.md` §2 hoặc hub #2 để mọi session đều đọc được. Quyết định Claude tự đưa ra: ghi trong PR/issue liên quan, nêu câu hỏi nào trong mục 1 đã được trả lời "không".
